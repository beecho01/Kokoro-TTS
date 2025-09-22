"""Config flow for Kokoro TTS with dynamic model/persona discovery."""

from __future__ import annotations
from typing import Any
import voluptuous as vol
import logging
import traceback
from urllib.parse import urlparse
import hashlib
import aiohttp

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_MODEL,
    CONF_PERSONA,
    CONF_LANGUAGE,
    CONF_SEX,
    CONF_SPEED,
    CONF_FORMAT,
    CONF_SAMPLE_RATE,
    DEFAULTS,
    PERSONA_MAPPINGS,
    LANGUAGE_OPTIONS,
    SEX_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)
_FORMAT_OPTIONS = ["wav", "mp3", "opus", "flac", "pcm"]
_SAMPLE_RATE_OPTIONS = ["22050", "24000", "44100"]

def get_persona_display_name(technical_name: str, selected_language: str | None = None, selected_sex: str | None = None) -> str:
    """Convert technical persona name to user-friendly display name."""
    if technical_name in PERSONA_MAPPINGS:
        language, sex, name = PERSONA_MAPPINGS[technical_name]
        
        # If both language and sex are filtered, show just the name
        if (selected_language and selected_language != "All Languages" and 
            selected_sex and selected_sex != "All"):
            return name
        # If only language is filtered, show name (sex)
        elif selected_language and selected_language != "All Languages":
            return f"{name} ({sex})"
        # If only sex is filtered, show name (language) 
        elif selected_sex and selected_sex != "All":
            return f"{name} ({language})"
        # If no filters, show full format
        else:
            return f"{name} ({language}, {sex})"
    return technical_name  # Fallback to technical name if not mapped

def get_technical_persona_name(display_name: str) -> str:
    """Convert display name back to technical persona name.""" 
    # First try exact match with just the name
    for tech_name, (language, sex, name) in PERSONA_MAPPINGS.items():
        if display_name == name:
            return tech_name
    
    # Then try other formats
    for tech_name, (language, sex, name) in PERSONA_MAPPINGS.items():
        possible_displays = [
            f"{name} ({sex})",
            f"{name} ({language})",
            f"{name} ({language}, {sex})"
        ]
        if display_name in possible_displays:
            return tech_name
    return display_name  # Fallback if not found

def filter_personas_by_language_and_sex(personas: list[str], selected_language: str, selected_sex: str) -> list[str]:
    """Filter persona list by selected language and sex."""
    _LOGGER.debug("Filtering %d personas by language='%s', sex='%s'", len(personas), selected_language, selected_sex)
    filtered = []
    for persona in personas:
        if persona in PERSONA_MAPPINGS:
            language, sex, _ = PERSONA_MAPPINGS[persona]
            
            # Check language filter
            language_match = (selected_language == "All Languages" or 
                            not selected_language or 
                            language == selected_language)
            
            # Check sex filter  
            sex_match = (selected_sex == "All" or 
                          not selected_sex or 
                          sex == selected_sex)
            
            if language_match and sex_match:
                filtered.append(persona)
                _LOGGER.debug("Included persona '%s' (%s, %s)", persona, language, sex)
            else:
                _LOGGER.debug("Filtered out persona '%s' (%s, %s) - lang_match=%s, sex_match=%s", 
                             persona, language, sex, language_match, sex_match)
        elif (selected_language == "All Languages" or not selected_language) and \
             (selected_sex == "All" or not selected_sex):
            # Include unmapped personas when both filters are "All"
            filtered.append(persona)
            _LOGGER.debug("Included unmapped persona '%s' (no filters active)", persona)
        else:
            _LOGGER.debug("Filtered out unmapped persona '%s' (filters active)", persona)
    
    _LOGGER.debug("Filtering result: %d personas after filtering", len(filtered))
    return filtered

def get_persona_options_for_language_and_sex(personas: list[str], selected_language: str, selected_sex: str) -> list[str]:
    """Get user-friendly persona options for specific language and sex."""
    _LOGGER.debug("Getting persona options for language='%s', sex='%s'", selected_language, selected_sex)
    filtered_personas = filter_personas_by_language_and_sex(personas, selected_language, selected_sex)
    persona_options = [get_persona_display_name(persona, selected_language, selected_sex) for persona in sorted(filtered_personas)]
    
    _LOGGER.debug("Generated %d persona options: %s", len(persona_options), persona_options)
    
    # If no personas found, show a helpful message
    if not persona_options:
        if selected_language != "All Languages" and selected_sex != "All":
            persona_options = [f"No {selected_sex.lower()} personas available for {selected_language}"]
        elif selected_language != "All Languages":
            persona_options = [f"No personas available for {selected_language}"]
        elif selected_sex != "All":
            persona_options = [f"No {selected_sex.lower()} personas available"]
        _LOGGER.debug("No personas found, using fallback message: %s", persona_options)
    
    return persona_options

# Backward compatibility function
def filter_personas_by_language(personas: list[str], selected_language: str) -> list[str]:
    """Filter persona list by selected language (backward compatibility)."""
    return filter_personas_by_language_and_sex(personas, selected_language, "All")

@config_entries.HANDLERS.register(DOMAIN)
class KokoroConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Kokoro TTS with dynamic discovery."""
    
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        _LOGGER.debug("KokoroConfigFlow.__init__ called")
        super().__init__()
        self._base_info: dict[str, Any] = {}
        self._discovered: dict[str, list[str]] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        _LOGGER.debug("async_get_options_flow called")
        return KokoroOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle base connection step."""
        _LOGGER.debug("async_step_user called with user_input: %s", user_input)
        errors: dict[str, str] = {}

        try:
            if user_input is not None:
                _LOGGER.debug("Processing user input")
                base = (user_input.get(CONF_BASE_URL) or "").strip().rstrip("/")
                _LOGGER.debug("Base URL after processing: %s", base)

                if not base:
                    _LOGGER.debug("Base URL is empty")
                    errors[CONF_BASE_URL] = "base_url_required"
                elif not (base.startswith("http://") or base.startswith("https://")):
                    _LOGGER.debug("Base URL doesn't start with http/https")
                    errors[CONF_BASE_URL] = "invalid_base_url"
                else:
                    try:
                        p = urlparse(base)
                        _LOGGER.debug("Parsed URL: hostname=%s, scheme=%s", p.hostname, p.scheme)
                        if not p.hostname:
                            _LOGGER.debug("No hostname found in URL")
                            errors[CONF_BASE_URL] = "invalid_base_url"
                    except Exception as e:
                        _LOGGER.debug("URL parsing failed: %s", e)
                        errors[CONF_BASE_URL] = "invalid_base_url"

                if not errors:
                    _LOGGER.debug("No validation errors, storing base info")
                    # Store base info and move to details step
                    self._base_info = {
                        CONF_BASE_URL: base,
                        CONF_API_KEY: user_input.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY]),
                    }
                    _LOGGER.debug("Base info stored: %s", self._base_info)
                    _LOGGER.debug("Moving to details step")
                    return await self.async_step_details()
                else:
                    _LOGGER.debug("Validation errors: %s", errors)

            _LOGGER.debug("Showing user form with errors: %s", errors)
            schema = _base_schema(user_input)
            _LOGGER.debug("Schema created: %s", schema)
            return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

        except Exception as e:
            _LOGGER.error("Exception in async_step_user: %s", e)
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            errors["base"] = f"unexpected_error: {str(e)}"
            return self.async_show_form(step_id="user", data_schema=_base_schema(user_input), errors=errors)

    async def async_step_details(self, user_input: dict | None = None) -> FlowResult:
        """Handle model/persona selection with dynamic discovery."""
        _LOGGER.debug("async_step_details called with user_input: %s", user_input)
        
        try:
            base_url = self._base_info[CONF_BASE_URL]
            api_key = self._base_info.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
            _LOGGER.debug("Using base_url: %s, api_key: %s", base_url, "***" if api_key else "(none)")
            
            # Discover models and personas if not cached
            if "models" not in self._discovered:
                _LOGGER.debug("Discovering models and personas")
                models, personas = await _discover_models_and_personas(base_url, api_key)
                self._discovered = {"models": models, "personas": personas}
                _LOGGER.debug("Discovered %d models, %d personas from %s", len(models), len(personas), base_url)
            else:
                models = self._discovered["models"]
                personas = self._discovered["personas"]
                _LOGGER.debug("Using cached discovery: %d models, %d personas", len(models), len(personas))

            if user_input is not None:
                _LOGGER.debug("Processing details user input")
                _LOGGER.debug("Current user_input keys: %s", list(user_input.keys()))
                
                # Check if this is a filter change (language or sex) - not final submission
                # We detect filter changes by checking if ONLY filter fields have changed
                # and no other required fields are being submitted
                has_language_change = CONF_LANGUAGE in user_input
                has_sex_change = CONF_SEX in user_input
                has_persona_selection = (user_input.get(CONF_PERSONA) is not None and 
                                       user_input.get(CONF_PERSONA) != "" and 
                                       str(user_input.get(CONF_PERSONA)).strip() != "")
                has_other_fields = any(key in user_input for key in [CONF_MODEL, CONF_SPEED, CONF_FORMAT, CONF_SAMPLE_RATE])
                
                _LOGGER.debug("Filter analysis: language_change=%s, sex_change=%s, persona_selected=%s, other_fields=%s", 
                             has_language_change, has_sex_change, has_persona_selection, has_other_fields)
                
                # If user changed filters and hasn't made a final persona selection, re-render
                if (has_language_change or has_sex_change) and not has_persona_selection:
                    selected_language = user_input.get(CONF_LANGUAGE, DEFAULTS[CONF_LANGUAGE])
                    selected_sex = user_input.get(CONF_SEX, DEFAULTS[CONF_SEX])
                    current_persona = user_input.get(CONF_PERSONA, DEFAULTS[CONF_PERSONA])
                    
                    _LOGGER.debug("Filter change detected: language='%s', sex='%s', current_persona='%s'", 
                                 selected_language, selected_sex, current_persona)
                    
                    # Get filtered personas for the new filter settings
                    filtered_personas = filter_personas_by_language_and_sex(personas, selected_language, selected_sex)
                    
                    # Check if current persona is still valid for the selected filters
                    # Convert display name to technical name for validation
                    if current_persona:
                        technical_persona = get_technical_persona_name(current_persona)
                        if technical_persona not in filtered_personas:
                            # Reset persona to None if current persona is invalid for new filters
                            user_input[CONF_PERSONA] = None
                            _LOGGER.debug("Reset persona because '%s' not in filtered personas: %s", technical_persona, filtered_personas)
                    elif not current_persona and filtered_personas:
                        # No persona was selected, leave it as None to force user choice
                        user_input[CONF_PERSONA] = None
                    
                    # Re-render form with updated persona options
                    _LOGGER.debug("Re-rendering form with filter changes")
                    schema = _details_schema(models, personas, user_input)
                    return self.async_show_form(
                        step_id="details",
                        data_schema=schema,
                    )
                
                # Convert sample_rate back to int if it was selected as string
                if CONF_SAMPLE_RATE in user_input and isinstance(user_input[CONF_SAMPLE_RATE], str):
                    try:
                        user_input[CONF_SAMPLE_RATE] = int(user_input[CONF_SAMPLE_RATE])
                    except ValueError:
                        pass  # Keep as string if conversion fails
                
                # Validate that a persona was selected
                errors = {}
                selected_persona = user_input.get(CONF_PERSONA)
                if not selected_persona or selected_persona == "Select a persona..." or selected_persona.strip() == "":
                    errors[CONF_PERSONA] = "persona_required"
                    
                if errors:
                    _LOGGER.debug("Voice validation errors: %s", errors)
                    schema = _details_schema(models, personas, user_input)
                    return self.async_show_form(
                        step_id="details",
                        data_schema=schema,
                        errors=errors,
                    )
                
                # Convert persona display name back to technical name
                if CONF_PERSONA in user_input:
                    display_persona = user_input[CONF_PERSONA]
                    technical_persona = get_technical_persona_name(display_persona)
                    user_input[CONF_PERSONA] = technical_persona
                    _LOGGER.debug("Converted persona '%s' to technical name '%s'", display_persona, technical_persona)
                
                # Merge base info with details
                data = {**self._base_info, **user_input}
                _LOGGER.debug("Merged data: %s", data)
                
                # Create entry with unique ID
                unique_id = _calc_unique_id(base_url)
                _LOGGER.debug("Generated unique_id: %s", unique_id)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                
                hostname = urlparse(base_url).hostname or base_url
                title = f"Kokoro TTS ({hostname}, {data.get(CONF_MODEL, DEFAULTS[CONF_MODEL])})"
                _LOGGER.debug("Creating entry with title: %s", title)
                return self.async_create_entry(title=title, data=data)

            _LOGGER.debug("Showing details form")
            schema = _details_schema(models, personas, user_input)
            _LOGGER.debug("Details schema created")
            return self.async_show_form(
                step_id="details",
                data_schema=schema,
            )

        except Exception as e:
            _LOGGER.error("Exception in async_step_details: %s", e)
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            # Fall back to simple single-step flow
            return self.async_abort(reason="unknown_error")

    async def async_step_import(self, user_input: dict) -> FlowResult:
        """Support YAML import."""
        _LOGGER.debug("async_step_import called with user_input: %s", user_input)
        try:
            base = (user_input.get(CONF_BASE_URL) or "").strip().rstrip("/")
            if not base:
                return self.async_abort(reason="base_url_required")
                
            unique_id = _calc_unique_id(base)
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            hostname = urlparse(base).hostname or base
            title = f"Kokoro TTS ({hostname}, {user_input.get(CONF_MODEL, DEFAULTS[CONF_MODEL])})"
            return self.async_create_entry(title=title, data=user_input)
        except Exception as e:
            _LOGGER.error("Exception in async_step_import: %s", e)
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            return self.async_abort(reason="unknown_error")

def _calc_unique_id(base_url: str) -> str:
    """Generate stable unique ID from base URL."""
    try:
        result = hashlib.sha256(base_url.encode("utf-8")).hexdigest()[:12]
        _LOGGER.debug("Generated unique_id for %s: %s", base_url, result)
        return result
    except Exception as e:
        _LOGGER.error("Error generating unique_id: %s", e)
        return "kokoro_default"

async def _discover_models_and_personas(base_url: str, api_key: str) -> tuple[list[str], list[str]]:
    """Discover models and personas from Kokoro API endpoints."""
    _LOGGER.debug("Starting discovery for %s", base_url)
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    models: list[str] = []
    personas: list[str] = []
    
    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Discover models from /v1/models
            try:
                models_url = f"{base_url}/v1/models"
                _LOGGER.debug("Fetching models from: %s", models_url)
                async with session.get(models_url, headers=headers) as resp:
                    _LOGGER.debug("Models response status: %s", resp.status)
                    if resp.status == 200:
                        data = await resp.json()
                        _LOGGER.debug("Models response data: %s", data)
                        if isinstance(data, dict) and isinstance(data.get("data"), list):
                            models = [str(item.get("id")) for item in data["data"] if isinstance(item, dict) and item.get("id")]
                            _LOGGER.debug("Extracted models: %s", models)
            except Exception as e:
                _LOGGER.debug("Failed to discover models from %s/v1/models: %s", base_url, e)
            
            # Discover personas from /v1/audio/voices
            try:
                personas_url = f"{base_url}/v1/audio/voices"
                _LOGGER.debug("Fetching personas from: %s", personas_url)
                async with session.get(personas_url, headers=headers) as resp:
                    _LOGGER.debug("Voices response status: %s", resp.status)
                    if resp.status == 200:
                        data = await resp.json()
                        _LOGGER.debug("Voices response data: %s", data)
                        # Check for different possible response formats
                        if isinstance(data, dict):
                            if isinstance(data.get("voices"), list):
                                personas = [str(voice) for voice in data["voices"] if isinstance(voice, str)]
                                _LOGGER.debug("Extracted personas from 'voices' field: %s", personas)
                            elif isinstance(data.get("personas"), list):
                                personas = [str(persona) for persona in data["personas"] if isinstance(persona, str)]
                                _LOGGER.debug("Extracted personas from 'personas' field: %s", personas)
                        elif isinstance(data, list):
                            # Direct array of voices
                            personas = [str(voice) for voice in data if isinstance(voice, str)]
                            _LOGGER.debug("Extracted personas from direct array: %s", personas)
            except Exception as e:
                _LOGGER.debug("Failed to discover personas from %s/v1/audio/voices: %s", base_url, e)
    except Exception as e:
        _LOGGER.error("Error in discovery session: %s", e)
    
    # If no personas were discovered, use the static mappings as fallback
    if not personas:
        _LOGGER.debug("No personas discovered from API, using static PERSONA_MAPPINGS as fallback")
        from .const import PERSONA_MAPPINGS
        personas = list(PERSONA_MAPPINGS.keys())
        _LOGGER.debug("Using static personas: %d personas from PERSONA_MAPPINGS", len(personas))
    
    # If no models were discovered, provide a default
    if not models:
        _LOGGER.debug("No models discovered from API, using default 'kokoro' model")
        models = ["kokoro"]
    
    _LOGGER.debug("Discovery complete: %d models, %d personas", len(models), len(personas))
    return models, personas


def _base_schema(user_input: dict | None = None) -> vol.Schema:
    """Schema for base connection step."""
    _LOGGER.debug("Creating base schema with user_input: %s", user_input)
    ui = user_input or {}
    try:
        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=ui.get(CONF_BASE_URL, "")): cv.string,
                vol.Optional(CONF_API_KEY, default=ui.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])): cv.string,
            }
        )
        _LOGGER.debug("Base schema created successfully")
        return schema
    except Exception as e:
        _LOGGER.error("Error creating base schema: %s", e)
        raise


def _details_schema(models: list[str], personas: list[str], user_input: dict | None = None) -> vol.Schema:
    """Schema for details step with dynamic selectors."""
    _LOGGER.debug("Creating details schema with %d models, %d personas", len(models), len(personas))
    ui = user_input or {}
    schema = {}
    
    try:
        # Model selector (dropdown if discovered, text input otherwise)
        if models:
            _LOGGER.debug("Using dropdown for models: %s", models)
            schema[vol.Optional(CONF_MODEL, default=ui.get(CONF_MODEL, DEFAULTS[CONF_MODEL]))] = selector.selector({
                "select": {
                    "options": sorted(models),
                    "mode": "dropdown",
                    "custom_value": True,
                }
            })
        else:
            _LOGGER.debug("Using text input for model")
            schema[vol.Optional(CONF_MODEL, default=ui.get(CONF_MODEL, DEFAULTS[CONF_MODEL]))] = cv.string
        
        # Language selector for persona filtering
        selected_language = ui.get(CONF_LANGUAGE, DEFAULTS[CONF_LANGUAGE])
        schema[vol.Optional(CONF_LANGUAGE, default=selected_language)] = selector.selector({
            "select": {
                "options": LANGUAGE_OPTIONS,
                "mode": "dropdown",
            }
        })
        
        # Sex selector for persona filtering
        selected_sex = ui.get(CONF_SEX, DEFAULTS[CONF_SEX])
        schema[vol.Optional(CONF_SEX, default=selected_sex)] = selector.selector({
            "select": {
                "options": SEX_OPTIONS,
                "mode": "dropdown",
            }
        })
        
        # Voice selector (filtered by language and sex if personas discovered)
        if personas:
            _LOGGER.debug("Using dropdown for personas: %d total personas", len(personas))
            
            # Get filtered persona options for the selected language and sex
            persona_options = get_persona_options_for_language_and_sex(personas, selected_language, selected_sex)
            _LOGGER.debug("Filtered persona options for lang='%s', sex='%s': %s", selected_language, selected_sex, persona_options)
            
            # Convert current persona value to display name if it exists
            current_persona = ui.get(CONF_PERSONA, DEFAULTS[CONF_PERSONA])
            if current_persona is None:
                # Use empty string - Home Assistant will use the translation
                current_persona_display = ""
            else:
                current_persona_display = get_persona_display_name(current_persona, selected_language, selected_sex)
            
            _LOGGER.debug("Current persona: '%s' -> display: '%s'", current_persona, current_persona_display)
            
            # If current persona is not in filtered options, add it (unless it's None/empty)
            if current_persona and current_persona_display not in persona_options and current_persona_display:
                persona_options.append(current_persona_display)
                _LOGGER.debug("Added current persona to options: %s", current_persona_display)
            
            schema[vol.Optional(CONF_PERSONA, default=current_persona_display)] = selector.selector({
                "select": {
                    "options": sorted(persona_options) if persona_options else ["No personas available"],
                    "mode": "dropdown",
                    "custom_value": True,
                }
            })
        else:
            _LOGGER.debug("Using text input for persona")
            persona_default = ui.get(CONF_PERSONA, DEFAULTS[CONF_PERSONA])
            if persona_default is None:
                persona_default = ""  # Empty string for Home Assistant to handle
            schema[vol.Optional(CONF_PERSONA, default=persona_default)] = cv.string
        
        # Speed slider
        schema[vol.Optional(CONF_SPEED, default=ui.get(CONF_SPEED, DEFAULTS[CONF_SPEED]))] = selector.selector({
            "number": {
                "min": 0.25,
                "max": 4.0,
                "step": 0.05,
                "mode": "slider",
            }
        })
        
        # Format dropdown
        schema[vol.Optional(CONF_FORMAT, default=ui.get(CONF_FORMAT, DEFAULTS[CONF_FORMAT]))] = selector.selector({
            "select": {
                "options": _FORMAT_OPTIONS,
                "mode": "dropdown",
            }
        })
        
        # Sample rate dropdown (fixed to use strings)
        default_sample_rate = ui.get(CONF_SAMPLE_RATE, DEFAULTS[CONF_SAMPLE_RATE])
        if isinstance(default_sample_rate, int):
            default_sample_rate = str(default_sample_rate)
        
        schema[vol.Optional(CONF_SAMPLE_RATE, default=default_sample_rate)] = selector.selector({
            "select": {
                "options": _SAMPLE_RATE_OPTIONS,  # Now strings
                "mode": "dropdown",
            }
        })
        
        result = vol.Schema(schema)
        _LOGGER.debug("Details schema created successfully")
        return result
    except Exception as e:
        _LOGGER.error("Error creating details schema: %s", e)
        raise


class KokoroOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Kokoro TTS."""
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        _LOGGER.debug("KokoroOptionsFlow.__init__ called")
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Handle options step with dynamic discovery."""
        _LOGGER.debug("KokoroOptionsFlow.async_step_init called with user_input: %s", user_input)
        try:
            if user_input is not None:
                _LOGGER.debug("Options flow: Processing user input with keys: %s", list(user_input.keys()))
                
                # Check if this is a filter change (language or sex) - not final submission
                has_language_change = CONF_LANGUAGE in user_input
                has_sex_change = CONF_SEX in user_input
                has_persona_selection = (user_input.get(CONF_PERSONA) is not None and 
                                       user_input.get(CONF_PERSONA) != "" and 
                                       str(user_input.get(CONF_PERSONA)).strip() != "")
                
                _LOGGER.debug("Options filter analysis: language_change=%s, sex_change=%s, persona_selected=%s", 
                             has_language_change, has_sex_change, has_persona_selection)
                
                # If user changed filters and hasn't made a final persona selection, re-render
                if (has_language_change or has_sex_change) and not has_persona_selection:
                    # Start with current options or fall back to entry data
                    data = {**self._entry.data, **(self._entry.options or {})}
                    base_url = data.get(CONF_BASE_URL)
                    
                    # Try to discover models/personas for options
                    models, personas = [], []
                    if base_url:
                        api_key = self._entry.data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
                        try:
                            models, personas = await _discover_models_and_personas(base_url, api_key)
                        except Exception as e:
                            _LOGGER.debug("Failed to discover models/personas in options flow: %s", e)
                    
                    selected_language = user_input.get(CONF_LANGUAGE, DEFAULTS[CONF_LANGUAGE])
                    selected_sex = user_input.get(CONF_SEX, DEFAULTS[CONF_SEX])
                    current_persona = user_input.get(CONF_PERSONA, DEFAULTS[CONF_PERSONA])
                    
                    _LOGGER.debug("Options filter change: language='%s', sex='%s', current_persona='%s'", 
                                 selected_language, selected_sex, current_persona)
                    
                    # Get filtered personas for the new filter settings
                    filtered_personas = filter_personas_by_language_and_sex(personas, selected_language, selected_sex)
                    
                    # Check if current persona is still valid for the selected filters
                    if current_persona:
                        technical_persona = get_technical_persona_name(current_persona)
                        if technical_persona not in filtered_personas:
                            # Reset persona to None if current persona is invalid for new filters
                            user_input[CONF_PERSONA] = None
                            _LOGGER.debug("Options: Reset persona because '%s' not in filtered personas", technical_persona)
                    elif not current_persona and filtered_personas:
                        # No persona was selected, leave it as None to force user choice
                        user_input[CONF_PERSONA] = None
                    
                    # Re-render form with updated persona options
                    _LOGGER.debug("Options: Filters changed to language=%s, sex=%s, re-rendering form", selected_language, selected_sex)
                    
                    # Don't allow changing base_url in options
                    data.pop(CONF_BASE_URL, None)
                    
                    # Merge with new user input
                    form_data = {**data, **user_input}
                    
                    return self.async_show_form(
                        step_id="init",
                        data_schema=_details_schema(models, personas, form_data),
                    )
                
                # Convert sample_rate back to int if it was selected as string
                if CONF_SAMPLE_RATE in user_input and isinstance(user_input[CONF_SAMPLE_RATE], str):
                    try:
                        user_input[CONF_SAMPLE_RATE] = int(user_input[CONF_SAMPLE_RATE])
                    except ValueError:
                        pass  # Keep as string if conversion fails
                
                # Validate that a persona was selected
                errors = {}
                selected_persona = user_input.get(CONF_PERSONA)
                if not selected_persona or selected_persona == "Select a persona..." or selected_persona.strip() == "":
                    errors[CONF_PERSONA] = "persona_required"
                    
                if errors:
                    _LOGGER.debug("Options: Voice validation errors: %s", errors)
                    # Get current entry data for form re-rendering
                    current_data = {**self._entry.data, **(self._entry.options or {})}
                    current_data.pop(CONF_BASE_URL, None)  # Don't allow changing base_url in options
                    form_data = {**current_data, **user_input}
                    
                    # Try to get models/personas for form re-rendering
                    try:
                        temp_models, temp_personas = await _discover_models_and_personas(
                            self._entry.data[CONF_BASE_URL], 
                            self._entry.data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
                        )
                    except Exception:
                        temp_models, temp_personas = [], []
                    
                    return self.async_show_form(
                        step_id="init",
                        data_schema=_details_schema(temp_models, temp_personas, form_data),
                        errors=errors,
                    )
                
                # Convert persona display name back to technical name
                if CONF_PERSONA in user_input:
                    display_persona = user_input[CONF_PERSONA]
                    technical_persona = get_technical_persona_name(display_persona)
                    user_input[CONF_PERSONA] = technical_persona
                    _LOGGER.debug("Options: Converted persona '%s' to technical name '%s'", display_persona, technical_persona)
                
                return self.async_create_entry(title="", data=user_input)

            # Start with current options or fall back to entry data
            data = {**self._entry.data, **(self._entry.options or {})}
            # Don't allow changing base_url in options
            base_url = data.pop(CONF_BASE_URL, None)
            
            # Convert stored technical persona name to display name for the form
            if CONF_PERSONA in data:
                technical_persona = data[CONF_PERSONA]
                # Get current language and sex for proper display formatting
                current_language = data.get(CONF_LANGUAGE, DEFAULTS[CONF_LANGUAGE])
                current_sex = data.get(CONF_SEX, DEFAULTS[CONF_SEX])
                display_persona = get_persona_display_name(technical_persona, current_language, current_sex)
                data[CONF_PERSONA] = display_persona
                _LOGGER.debug("Options: Converted stored persona '%s' to display name '%s'", technical_persona, display_persona)
            
            # Try to discover models/personas for options
            models, personas = [], []
            if base_url:
                api_key = self._entry.data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
                try:
                    models, personas = await _discover_models_and_personas(base_url, api_key)
                except Exception as e:
                    _LOGGER.debug("Failed to discover models/personas in options flow: %s", e)

            return self.async_show_form(
                step_id="init", 
                data_schema=_details_schema(models, personas, data),
            )
        except Exception as e:
            _LOGGER.error("Exception in KokoroOptionsFlow.async_step_init: %s", e)
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            return self.async_abort(reason="unknown_error")