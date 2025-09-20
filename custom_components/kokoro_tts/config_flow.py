"""Config flow for Kokoro TTS with dynamic model/voice discovery."""

from __future__ import annotations
from typing import Any
import voluptuous as vol
import logging
from urllib.parse import urlparse
import hashlib
import aiohttp

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.config_entries import ConfigFlow
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
_SAMPLE_RATE_OPTIONS = [22050, 24000, 44100]


def _calc_unique_id(base_url: str) -> str:
    """Generate stable unique ID from base URL."""
    return hashlib.sha256(base_url.encode("utf-8")).hexdigest()[:12]


async def _discover_models_and_voices(base_url: str, api_key: str) -> tuple[list[str], list[str]]:
    """Discover models and voices from Kokoro API endpoints."""
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    models: list[str] = []
    voices: list[str] = []
    
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Discover models from /v1/models
        try:
            async with session.get(f"{base_url}/v1/models", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and isinstance(data.get("data"), list):
                        models = [str(item.get("id")) for item in data["data"] if isinstance(item, dict) and item.get("id")]
        except Exception:
            _LOGGER.debug("Failed to discover models from %s/v1/models", base_url)
        
        # Discover voices from /v1/audio/voices
        try:
            async with session.get(f"{base_url}/v1/audio/voices", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and isinstance(data.get("voices"), list):
                        voices = [str(voice) for voice in data["voices"] if isinstance(voice, str)]
        except Exception:
            _LOGGER.debug("Failed to discover voices from %s/v1/audio/voices", base_url)
    
    return models, voices


def _base_schema(user_input: dict | None = None) -> vol.Schema:
    """Schema for base connection step."""
    ui = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_BASE_URL, default=ui.get(CONF_BASE_URL, "")): cv.string,
            vol.Optional(CONF_API_KEY, default=ui.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])): cv.string,
        }
    )


def _details_schema(models: list[str], voices: list[str], user_input: dict | None = None) -> vol.Schema:
    """Schema for details step with dynamic selectors."""
    ui = user_input or {}
    schema = {}
    
    # Model selector (dropdown if discovered, text input otherwise)
    if models:
        schema[vol.Optional(CONF_MODEL, default=ui.get(CONF_MODEL, DEFAULTS[CONF_MODEL]))] = selector.selector({
            "select": {
                "options": sorted(models),
                "mode": "dropdown",
                "custom_value": True,
            }
        })
    else:
        schema[vol.Optional(CONF_MODEL, default=ui.get(CONF_MODEL, DEFAULTS[CONF_MODEL]))] = cv.string
    
    # Voice selector (dropdown if discovered, text input otherwise)
    if voices:
        schema[vol.Optional(CONF_VOICE, default=ui.get(CONF_VOICE, DEFAULTS[CONF_VOICE]))] = selector.selector({
            "select": {
                "options": sorted(voices),
                "mode": "dropdown",
                "custom_value": True,
            }
        })
    else:
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
    
    # Sample rate dropdown
    schema[vol.Optional(CONF_SAMPLE_RATE, default=ui.get(CONF_SAMPLE_RATE, DEFAULTS[CONF_SAMPLE_RATE]))] = selector.selector({
        "select": {
            "options": _SAMPLE_RATE_OPTIONS,
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
    
    return vol.Schema(schema)


class KokoroConfigFlow(ConfigFlow):
    """Handle a config flow for Kokoro TTS with dynamic discovery."""
    
    VERSION = 1
    domain = DOMAIN

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return KokoroOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle base connection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base = (user_input.get(CONF_BASE_URL) or "").strip().rstrip("/")

            if not base:
                errors[CONF_BASE_URL] = "base_url_required"
            elif not (base.startswith("http://") or base.startswith("https://")):
                errors[CONF_BASE_URL] = "invalid_base_url"
            else:
                try:
                    p = urlparse(base)
                    if not p.hostname:
                        errors[CONF_BASE_URL] = "invalid_base_url"
                except Exception:
                    errors[CONF_BASE_URL] = "invalid_base_url"

            if not errors:
                # Store base info and move to details step
                self._base_info = {
                    CONF_BASE_URL: base,
                    CONF_API_KEY: user_input.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY]),
                }
                return await self.async_step_details()

        return self.async_show_form(step_id="user", data_schema=_base_schema(user_input), errors=errors)

    async def async_step_details(self, user_input: dict | None = None) -> FlowResult:
        """Handle model/voice selection with dynamic discovery."""
        base_url = self._base_info[CONF_BASE_URL]
        api_key = self._base_info.get(CONF_API_KEY, DEFAULTS[CONF_API_KEY])
        
        # Discover models and voices if not cached
        if not hasattr(self, "_discovered"):
            models, voices = await _discover_models_and_voices(base_url, api_key)
            self._discovered = {"models": models, "voices": voices}
            _LOGGER.debug("Discovered %d models, %d voices from %s", len(models), len(voices), base_url)
        else:
            models = self._discovered["models"]
            voices = self._discovered["voices"]

        if user_input is not None:
            # Merge base info with details
            data = {**self._base_info, **user_input}
            
            # Create entry with unique ID
            unique_id = _calc_unique_id(base_url)
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            hostname = urlparse(base_url).hostname or base_url
            title = f"Kokoro TTS ({hostname}, {data.get(CONF_MODEL, DEFAULTS[CONF_MODEL])})"
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="details",
            data_schema=_details_schema(models, voices, user_input),
            description_placeholders={
                "models_found": ", ".join(models)[:180] if models else "(none discovered)",
                "voices_found": ", ".join(voices)[:180] if voices else "(none discovered)",
            },
        )

    async def async_step_import(self, user_input: dict) -> FlowResult:
        """Support YAML import."""
        base = (user_input.get(CONF_BASE_URL) or "").strip().rstrip("/")
        if not base:
            return self.async_abort(reason="base_url_required")
            
        unique_id = _calc_unique_id(base)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        
        hostname = urlparse(base).hostname or base
        title = f"Kokoro TTS ({hostname}, {user_input.get(CONF_MODEL, DEFAULTS[CONF_MODEL])})"
        return self.async_create_entry(title=title, data=user_input)


class KokoroOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Kokoro TTS."""
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Handle options step with dynamic discovery."""
        if user_input is not None:
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
            except Exception:
                _LOGGER.debug("Failed to discover models/voices in options flow")

        return self.async_show_form(
            step_id="init", 
            data_schema=_details_schema(models, voices, data),
            description_placeholders={
                "models_found": ", ".join(models)[:180] if models else "(none discovered)",
                "voices_found": ", ".join(voices)[:180] if voices else "(none discovered)",
            },
        )