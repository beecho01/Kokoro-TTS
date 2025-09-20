"""Config flow for Kokoro TTS with dynamic model/voice discovery."""

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
    CONF_VOICE,
    CONF_SPEED,
    CONF_FORMAT,
    CONF_SAMPLE_RATE,
    CONF_PAD_MS,
    DEFAULTS,
)

_LOGGER = logging.getLogger(__name__)
_FORMAT_OPTIONS = ["wav", "mp3", "opus", "flac", "pcm"]
_SAMPLE_RATE_OPTIONS = ["22050", "24000", "44100"]  # Changed to strings

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
        """Handle model/voice selection with dynamic discovery."""
        _LOGGER.debug("async_step_details called with user_input: %s", user_input)
        
        try:
            base_url = self._base_info[CONF_BASE_URL]
            api_key = self._base_info.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
            _LOGGER.debug("Using base_url: %s, api_key: %s", base_url, "***" if api_key else "(none)")
            
            # Discover models and voices if not cached
            if "models" not in self._discovered:
                _LOGGER.debug("Discovering models and voices")
                models, voices = await _discover_models_and_voices(base_url, api_key)
                self._discovered = {"models": models, "voices": voices}
                _LOGGER.debug("Discovered %d models, %d voices from %s", len(models), len(voices), base_url)
            else:
                models = self._discovered["models"]
                voices = self._discovered["voices"]
                _LOGGER.debug("Using cached discovery: %d models, %d voices", len(models), len(voices))

            if user_input is not None:
                _LOGGER.debug("Processing details user input")
                # Convert sample_rate back to int if it was selected as string
                if CONF_SAMPLE_RATE in user_input and isinstance(user_input[CONF_SAMPLE_RATE], str):
                    try:
                        user_input[CONF_SAMPLE_RATE] = int(user_input[CONF_SAMPLE_RATE])
                    except ValueError:
                        pass  # Keep as string if conversion fails
                
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
            schema = _details_schema(models, voices, user_input)
            _LOGGER.debug("Details schema created")
            return self.async_show_form(
                step_id="details",
                data_schema=schema,
                description_placeholders={
                    "models_found": ", ".join(models)[:180] if models else "(none discovered)",
                    "voices_found": ", ".join(voices)[:180] if voices else "(none discovered)",
                },
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

    async def async_get_engine(hass, config, discovery_info=None):
        """
        Called by HA when the platform is set up via YAML (tts:).
        For UI (config entry) setups, HA will forward the entry data here too,
        so we support both paths by reading from `config` dict.
        """
        _LOGGER.debug("async_get_engine called with config: %s", config)
        
        name = config.get(CONF_NAME, DEFAULT_NAME)
        base_url = config[CONF_BASE_URL].rstrip("/")
        api_key = config.get(CONF_API_KEY, "x") or "x"
        model = config.get(CONF_MODEL, DEFAULT_MODEL)
        voice = config.get(CONF_VOICE)
        speed = float(config.get(CONF_SPEED, DEFAULT_SPEED))
        fmt = (config.get(CONF_FORMAT, DEFAULT_FORMAT) or DEFAULT_FORMAT).lower()
        sample_rate = int(config.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE))
        pad_ms = int(config.get(CONF_PAD_MS, DEFAULT_PAD_MS))

        _LOGGER.debug("Creating KokoroProvider with name: %s, base_url: %s", name, base_url)
        
        return KokoroProvider(
            name=name,
            base_url=base_url,
            api_key=api_key,
            model=model,
            voice=voice,
            speed=speed,
            fmt=fmt,
            sample_rate=sample_rate,
            pad_ms=pad_ms,
        )

def _calc_unique_id(base_url: str) -> str:
    """Generate stable unique ID from base URL."""
    try:
        result = hashlib.sha256(base_url.encode("utf-8")).hexdigest()[:12]
        _LOGGER.debug("Generated unique_id for %s: %s", base_url, result)
        return result
    except Exception as e:
        _LOGGER.error("Error generating unique_id: %s", e)
        return "kokoro_default"

async def _discover_models_and_voices(base_url: str, api_key: str) -> tuple[list[str], list[str]]:
    """Discover models and voices from Kokoro API endpoints."""
    _LOGGER.debug("Starting discovery for %s", base_url)
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    models: list[str] = []
    voices: list[str] = []
    
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
            
            # Discover voices from /v1/audio/voices
            try:
                voices_url = f"{base_url}/v1/audio/voices"
                _LOGGER.debug("Fetching voices from: %s", voices_url)
                async with session.get(voices_url, headers=headers) as resp:
                    _LOGGER.debug("Voices response status: %s", resp.status)
                    if resp.status == 200:
                        data = await resp.json()
                        _LOGGER.debug("Voices response data: %s", data)
                        if isinstance(data, dict) and isinstance(data.get("voices"), list):
                            voices = [str(voice) for voice in data["voices"] if isinstance(voice, str)]
                            _LOGGER.debug("Extracted voices: %s", voices)
            except Exception as e:
                _LOGGER.debug("Failed to discover voices from %s/v1/audio/voices: %s", base_url, e)
    except Exception as e:
        _LOGGER.error("Error in discovery session: %s", e)
    
    _LOGGER.debug("Discovery complete: %d models, %d voices", len(models), len(voices))
    return models, voices


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


def _details_schema(models: list[str], voices: list[str], user_input: dict | None = None) -> vol.Schema:
    """Schema for details step with dynamic selectors."""
    _LOGGER.debug("Creating details schema with %d models, %d voices", len(models), len(voices))
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
        
        # Voice selector (dropdown if discovered, text input otherwise)
        if voices:
            _LOGGER.debug("Using dropdown for voices: %s", voices[:5])  # Log first 5 to avoid spam
            schema[vol.Optional(CONF_VOICE, default=ui.get(CONF_VOICE, DEFAULTS[CONF_VOICE]))] = selector.selector({
                "select": {
                    "options": sorted(voices),
                    "mode": "dropdown",
                    "custom_value": True,
                }
            })
        else:
            _LOGGER.debug("Using text input for voice")
            schema[vol.Optional(CONF_VOICE, default=ui.get(CONF_VOICE, DEFAULTS[CONF_VOICE]))] = cv.string
        
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
        
        # Padding slider
        schema[vol.Optional(CONF_PAD_MS, default=ui.get(CONF_PAD_MS, DEFAULTS[CONF_PAD_MS]))] = selector.selector({
            "number": {
                "min": 0,
                "max": 2000,
                "step": 50,
                "mode": "slider",
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
                # Convert sample_rate back to int if it was selected as string
                if CONF_SAMPLE_RATE in user_input and isinstance(user_input[CONF_SAMPLE_RATE], str):
                    try:
                        user_input[CONF_SAMPLE_RATE] = int(user_input[CONF_SAMPLE_RATE])
                    except ValueError:
                        pass  # Keep as string if conversion fails
                return self.async_create_entry(title="", data=user_input)

            # Start with current options or fall back to entry data
            data = {**self._entry.data, **(self._entry.options or {})}
            # Don't allow changing base_url in options
            base_url = data.pop(CONF_BASE_URL, None)
            
            # Try to discover models/voices for options
            models, voices = [], []
            if base_url:
                api_key = self._entry.data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
                try:
                    models, voices = await _discover_models_and_voices(base_url, api_key)
                except Exception as e:
                    _LOGGER.debug("Failed to discover models/voices in options flow: %s", e)

            return self.async_show_form(
                step_id="init", 
                data_schema=_details_schema(models, voices, data),
                description_placeholders={
                    "models_found": ", ".join(models)[:180] if models else "(none discovered)",
                    "voices_found": ", ".join(voices)[:180] if voices else "(none discovered)",
                },
            )
        except Exception as e:
            _LOGGER.error("Exception in KokoroOptionsFlow.async_step_init: %s", e)
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            return self.async_abort(reason="unknown_error")