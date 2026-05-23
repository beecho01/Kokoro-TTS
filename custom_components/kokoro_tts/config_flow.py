"""Config flow for Kokoro TTS with dynamic model/persona discovery."""
from __future__ import annotations

from typing import Any
import asyncio
import hashlib
import logging
from urllib.parse import urlparse

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_FORMAT,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_PERSONA,
    CONF_SAMPLE_RATE,
    CONF_SEX,
    CONF_SPEED,
    DEFAULTS,
    DOMAIN,
    LANGUAGE_OPTIONS,
    PERSONA_MAPPINGS,
    SEX_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

_FORMAT_OPTIONS = ["mp3", "wav", "opus", "flac", "pcm"]
_SAMPLE_RATE_OPTIONS = ["22050", "24000", "44100"]


# ---------------------------------------------------------------------------
# Persona helpers
# ---------------------------------------------------------------------------

def get_persona_display_name(
    technical_name: str,
    selected_language: str | None = None,
    selected_sex: str | None = None,
) -> str:
    """Convert technical persona name to user-friendly display name."""
    if technical_name not in PERSONA_MAPPINGS:
        return technical_name

    language, sex, name = PERSONA_MAPPINGS[technical_name]

    if (
        selected_language
        and selected_language != "All Languages"
        and selected_sex
        and selected_sex != "All"
    ):
        return name
    if selected_language and selected_language != "All Languages":
        return f"{name} ({sex})"
    if selected_sex and selected_sex != "All":
        return f"{name} ({language})"
    return f"{name} ({language}, {sex})"


def get_technical_persona_name(display_name: str) -> str:
    """Convert display name back to technical persona name."""
    # Exact name match first (most common when both filters active)
    for tech_name, (_, _, name) in PERSONA_MAPPINGS.items():
        if display_name == name:
            return tech_name
    # Then try formatted variants
    for tech_name, (language, sex, name) in PERSONA_MAPPINGS.items():
        if display_name in (
            f"{name} ({sex})",
            f"{name} ({language})",
            f"{name} ({language}, {sex})",
        ):
            return tech_name
    return display_name


def filter_personas_by_language_and_sex(
    personas: list[str], selected_language: str, selected_sex: str
) -> list[str]:
    """Filter persona list by selected language and sex."""
    filtered: list[str] = []
    lang_all = selected_language in ("All Languages", "", None)
    sex_all = selected_sex in ("All", "", None)

    for persona in personas:
        if persona in PERSONA_MAPPINGS:
            language, sex, _ = PERSONA_MAPPINGS[persona]
            if (lang_all or language == selected_language) and (
                sex_all or sex == selected_sex
            ):
                filtered.append(persona)
        elif lang_all and sex_all:
            # Include unmapped personas only when no filters active
            filtered.append(persona)
    return filtered


def get_persona_options_for_language_and_sex(
    personas: list[str], selected_language: str, selected_sex: str
) -> list[str]:
    """Get user-friendly persona options for specific language and sex."""
    filtered = filter_personas_by_language_and_sex(personas, selected_language, selected_sex)
    options = sorted(
        get_persona_display_name(p, selected_language, selected_sex) for p in filtered
    )
    if not options:
        if selected_language != "All Languages" and selected_sex != "All":
            options = [f"No {selected_sex.lower()} personas available for {selected_language}"]
        elif selected_language != "All Languages":
            options = [f"No personas available for {selected_language}"]
        elif selected_sex != "All":
            options = [f"No {selected_sex.lower()} personas available"]
    return options


# ---------------------------------------------------------------------------
# API discovery
# ---------------------------------------------------------------------------

async def _discover_models_and_personas(
    base_url: str, api_key: str
) -> tuple[list[str], list[str]]:
    """Discover models and personas from Kokoro API endpoints."""
    headers: dict[str, str] = {}
    if api_key and api_key not in ("x", "not-needed", ""):
        headers["Authorization"] = f"Bearer {api_key}"

    models: list[str] = []
    personas: list[str] = []
    timeout = aiohttp.ClientTimeout(total=8)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Discover models from /v1/models
            try:
                async with session.get(f"{base_url}/v1/models", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, dict) and isinstance(data.get("data"), list):
                            models = [
                                str(item.get("id"))
                                for item in data["data"]
                                if isinstance(item, dict) and item.get("id")
                            ]
            except Exception:
                _LOGGER.debug("Failed to discover models from %s/v1/models", base_url)

            # Discover personas from /v1/audio/voices
            try:
                async with session.get(
                    f"{base_url}/v1/audio/voices", headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, dict):
                            voices = data.get("voices", data.get("personas", []))
                        elif isinstance(data, list):
                            voices = data
                        else:
                            voices = []

                        for voice in voices:
                            if isinstance(voice, str):
                                personas.append(voice)
                            elif isinstance(voice, dict) and voice.get("id"):
                                personas.append(str(voice["id"]))
            except Exception:
                _LOGGER.debug("Failed to discover personas from %s/v1/audio/voices", base_url)
    except Exception:
        _LOGGER.debug("Error in discovery session for %s", base_url)

    # Fallback to static mappings if API discovery failed
    if not personas:
        personas = list(PERSONA_MAPPINGS.keys())
    if not models:
        models = ["kokoro"]

    return models, personas


async def _test_connection(base_url: str, api_key: str) -> dict[str, str]:
    """Test connection to the Kokoro FastAPI server.

    Returns a dict of errors (empty dict = success).
    """
    headers: dict[str, str] = {}
    if api_key and api_key not in ("x", "not-needed", ""):
        headers["Authorization"] = f"Bearer {api_key}"

    timeout = aiohttp.ClientTimeout(total=10, connect=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(f"{base_url}/v1/models", headers=headers) as resp:
                    if resp.status == 401:
                        return {CONF_API_KEY: "auth_failed"}
                    if resp.status == 404:
                        return {CONF_BASE_URL: "server_not_found"}
                    if resp.status >= 500:
                        return {CONF_BASE_URL: "server_error"}
                    # 200 or other - server is reachable
            except aiohttp.ClientSSLError:
                return {CONF_BASE_URL: "ssl_error"}
            except aiohttp.ClientConnectorError:
                return {CONF_BASE_URL: "cannot_connect"}
            except asyncio.TimeoutError:
                return {CONF_BASE_URL: "timeout"}
    except Exception:
        return {CONF_BASE_URL: "cannot_connect"}
    return {}


# ---------------------------------------------------------------------------
# Unique ID
# ---------------------------------------------------------------------------

def _calc_unique_id(base_url: str) -> str:
    """Generate stable unique ID from base URL."""
    return hashlib.sha256(base_url.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------

def _base_schema(user_input: dict | None = None) -> vol.Schema:
    """Schema for base connection step."""
    ui = user_input or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_BASE_URL, default=ui.get(CONF_BASE_URL, "")
            ): str,
            vol.Optional(
                CONF_API_KEY, default=ui.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
            ): str,
        }
    )


def _details_schema(
    models: list[str],
    personas: list[str],
    user_input: dict | None = None,
) -> vol.Schema:
    """Schema for details step with dynamic selectors."""
    ui = user_input or {}
    schema: dict[vol.Optional | vol.Required, Any] = {}

    # Model selector
    if models:
        schema[
            vol.Optional(CONF_MODEL, default=ui.get(CONF_MODEL, DEFAULTS[CONF_MODEL]))
        ] = selector.selector(
            {
                "select": {
                    "options": sorted(models),
                    "mode": "dropdown",
                    "custom_value": True,
                }
            }
        )
    else:
        schema[
            vol.Optional(CONF_MODEL, default=ui.get(CONF_MODEL, DEFAULTS[CONF_MODEL]))
        ] = str

    # Language filter
    selected_language = ui.get(CONF_LANGUAGE, DEFAULTS[CONF_LANGUAGE])
    schema[vol.Optional(CONF_LANGUAGE, default=selected_language)] = selector.selector(
        {"select": {"options": LANGUAGE_OPTIONS, "mode": "dropdown"}}
    )

    # Sex filter
    selected_sex = ui.get(CONF_SEX, DEFAULTS[CONF_SEX])
    schema[vol.Optional(CONF_SEX, default=selected_sex)] = selector.selector(
        {"select": {"options": SEX_OPTIONS, "mode": "dropdown"}}
    )

    # Persona selector (filtered)
    if personas:
        persona_options = get_persona_options_for_language_and_sex(
            personas, selected_language, selected_sex
        )
        current_persona = ui.get(CONF_PERSONA, DEFAULTS[CONF_PERSONA])
        if current_persona is None:
            current_persona_display = ""
        else:
            current_persona_display = get_persona_display_name(
                current_persona, selected_language, selected_sex
            )
        # Ensure current persona is in the list
        if current_persona and current_persona_display and current_persona_display not in persona_options:
            persona_options.append(current_persona_display)

        schema[vol.Optional(CONF_PERSONA, default=current_persona_display)] = selector.selector(
            {
                "select": {
                    "options": sorted(persona_options) if persona_options else ["No personas available"],
                    "mode": "dropdown",
                    "custom_value": True,
                }
            }
        )
    else:
        persona_default = ui.get(CONF_PERSONA, DEFAULTS[CONF_PERSONA]) or ""
        schema[vol.Optional(CONF_PERSONA, default=persona_default)] = str

    # Speed slider
    schema[
        vol.Optional(CONF_SPEED, default=ui.get(CONF_SPEED, DEFAULTS[CONF_SPEED]))
    ] = selector.selector({"number": {"min": 0.25, "max": 4.0, "step": 0.05, "mode": "slider"}})

    # Format dropdown
    schema[
        vol.Optional(CONF_FORMAT, default=ui.get(CONF_FORMAT, DEFAULTS[CONF_FORMAT]))
    ] = selector.selector({"select": {"options": _FORMAT_OPTIONS, "mode": "dropdown"}})

    # Sample rate dropdown
    default_sr = ui.get(CONF_SAMPLE_RATE, DEFAULTS[CONF_SAMPLE_RATE])
    if isinstance(default_sr, int):
        default_sr = str(default_sr)
    schema[vol.Optional(CONF_SAMPLE_RATE, default=default_sr)] = selector.selector(
        {"select": {"options": _SAMPLE_RATE_OPTIONS, "mode": "dropdown"}}
    )

    return vol.Schema(schema)


# ---------------------------------------------------------------------------
# Config Flow
# ---------------------------------------------------------------------------

class KokoroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kokoro TTS with dynamic discovery."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._base_info: dict[str, Any] = {}
        self._discovered: dict[str, list[str]] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return KokoroOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None):
        """Handle base connection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base = (user_input.get(CONF_BASE_URL) or "").strip().rstrip("/")

            # Validate URL
            if not base:
                errors[CONF_BASE_URL] = "base_url_required"
            elif not base.startswith(("http://", "https://")):
                errors[CONF_BASE_URL] = "invalid_base_url"
            else:
                try:
                    p = urlparse(base)
                    if not p.hostname:
                        errors[CONF_BASE_URL] = "invalid_base_url"
                except Exception:
                    errors[CONF_BASE_URL] = "invalid_base_url"

            if not errors:
                # Test connection to the server
                api_key = user_input.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
                conn_errors = await _test_connection(base, api_key)
                if conn_errors:
                    errors.update(conn_errors)
                else:
                    self._base_info = {
                        CONF_BASE_URL: base,
                        CONF_API_KEY: api_key,
                    }
                    return await self.async_step_details()

        return self.async_show_form(
            step_id="user", data_schema=_base_schema(user_input), errors=errors
        )

    async def async_step_details(self, user_input: dict | None = None):
        """Handle model/persona selection with dynamic discovery."""
        base_url = self._base_info[CONF_BASE_URL]
        api_key = self._base_info.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])

        # Discover models and personas if not cached
        if "models" not in self._discovered:
            models, personas = await _discover_models_and_personas(base_url, api_key)
            self._discovered = {"models": models, "personas": personas}
        else:
            models = self._discovered["models"]
            personas = self._discovered["personas"]

        if user_input is not None:
            # Check if this is a filter change (language or sex changed, no persona selected)
            has_persona = bool(
                user_input.get(CONF_PERSONA)
                and str(user_input.get(CONF_PERSONA)).strip()
            )

            if not has_persona:
                # Re-render with updated filters
                schema = _details_schema(models, personas, user_input)
                return self.async_show_form(step_id="details", data_schema=schema)

            # Convert sample_rate to int
            if CONF_SAMPLE_RATE in user_input and isinstance(user_input[CONF_SAMPLE_RATE], str):
                try:
                    user_input[CONF_SAMPLE_RATE] = int(user_input[CONF_SAMPLE_RATE])
                except ValueError:
                    pass

            # Validate persona selection
            selected_persona = user_input.get(CONF_PERSONA)
            if not selected_persona or not str(selected_persona).strip():
                return self.async_show_form(
                    step_id="details",
                    data_schema=_details_schema(models, personas, user_input),
                    errors={CONF_PERSONA: "persona_required"},
                )

            # Convert persona display name back to technical name
            user_input[CONF_PERSONA] = get_technical_persona_name(user_input[CONF_PERSONA])

            # Merge base info with details
            data = {**self._base_info, **user_input}

            # Create entry with unique ID
            unique_id = _calc_unique_id(base_url)
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            hostname = urlparse(base_url).hostname or base_url
            title = f"Kokoro TTS ({hostname})"
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="details", data_schema=_details_schema(models, personas, user_input)
        )

    async def async_step_reauth(self, entry_data: dict):
        """Handle re-authentication."""
        self._base_info = {
            CONF_BASE_URL: entry_data[CONF_BASE_URL],
            CONF_API_KEY: entry_data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY]),
        }
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict | None = None
    ):
        """Handle re-auth confirmation."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
            base_url = self._base_info[CONF_BASE_URL]
            conn_errors = await _test_connection(base_url, api_key)
            if conn_errors:
                errors.update(conn_errors)
            else:
                # Update the existing entry
                entry_id = self.context.get("entry_id")
                if entry_id:
                    entry = self.hass.config_entries.async_get_entry(entry_id)
                    if entry:
                        self.hass.config_entries.async_update_entry(
                            entry,
                            data={**entry.data, CONF_API_KEY: api_key},
                        )
                        return self.async_abort(reason="reauth_successful")
                return self.async_abort(reason="reauth_failed")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_API_KEY, default=self._base_info.get(CONF_API_KEY, "")): str,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, user_input: dict):
        """Support YAML import."""
        base = (user_input.get(CONF_BASE_URL) or "").strip().rstrip("/")
        if not base:
            return self.async_abort(reason="base_url_required")

        unique_id = _calc_unique_id(base)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        hostname = urlparse(base).hostname or base
        title = f"Kokoro TTS ({hostname})"
        return self.async_create_entry(title=title, data=user_input)


# ---------------------------------------------------------------------------
# Options Flow
# ---------------------------------------------------------------------------

class KokoroOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Kokoro TTS."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Handle options step with dynamic discovery."""
        if user_input is not None:
            # Check if this is a filter change (no persona selected)
            has_persona = bool(
                user_input.get(CONF_PERSONA)
                and str(user_input.get(CONF_PERSONA)).strip()
            )

            if not has_persona:
                # Re-render with updated filters
                data = {**self._entry.data, **(self._entry.options or {})}
                data.pop(CONF_BASE_URL, None)
                form_data = {**data, **user_input}

                base_url = self._entry.data[CONF_BASE_URL]
                api_key = self._entry.data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
                models, personas = [], []
                try:
                    models, personas = await _discover_models_and_personas(base_url, api_key)
                except Exception:
                    pass

                return self.async_show_form(
                    step_id="init",
                    data_schema=_details_schema(models, personas, form_data),
                )

            # Convert sample_rate to int
            if CONF_SAMPLE_RATE in user_input and isinstance(user_input[CONF_SAMPLE_RATE], str):
                try:
                    user_input[CONF_SAMPLE_RATE] = int(user_input[CONF_SAMPLE_RATE])
                except ValueError:
                    pass

            # Validate persona
            selected_persona = user_input.get(CONF_PERSONA)
            if not selected_persona or not str(selected_persona).strip():
                data = {**self._entry.data, **(self._entry.options or {})}
                data.pop(CONF_BASE_URL, None)
                form_data = {**data, **user_input}

                base_url = self._entry.data[CONF_BASE_URL]
                api_key = self._entry.data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
                try:
                    models, personas = await _discover_models_and_personas(base_url, api_key)
                except Exception:
                    models, personas = [], []

                return self.async_show_form(
                    step_id="init",
                    data_schema=_details_schema(models, personas, form_data),
                    errors={CONF_PERSONA: "persona_required"},
                )

            # Convert persona display name back to technical name
            user_input[CONF_PERSONA] = get_technical_persona_name(user_input[CONF_PERSONA])

            return self.async_create_entry(title="", data=user_input)

        # Initial form display
        data = {**self._entry.data, **(self._entry.options or {})}
        base_url = data.pop(CONF_BASE_URL, None)

        # Convert stored technical persona name to display name
        if CONF_PERSONA in data:
            current_language = data.get(CONF_LANGUAGE, DEFAULTS[CONF_LANGUAGE])
            current_sex = data.get(CONF_SEX, DEFAULTS[CONF_SEX])
            data[CONF_PERSONA] = get_persona_display_name(
                data[CONF_PERSONA], current_language, current_sex
            )

        # Discover models/personas
        models, personas = [], []
        if base_url:
            api_key = self._entry.data.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
            try:
                models, personas = await _discover_models_and_personas(base_url, api_key)
            except Exception:
                pass

        return self.async_show_form(
            step_id="init", data_schema=_details_schema(models, personas, data)
        )
