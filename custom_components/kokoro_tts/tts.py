"""Kokoro TTS entity for Home Assistant."""
from __future__ import annotations

from typing import Any

import aiohttp
import base64
import logging

from homeassistant.components.tts.entity import TextToSpeechEntity, TtsAudioType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_FORMAT,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_PERSONA,
    CONF_SAMPLE_RATE,
    CONF_SPEED,
    DEFAULT_API_KEY,
    DEFAULT_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SPEED,
    DEFAULT_VOLUME_MULTIPLIER,
    DOMAIN,
    LANGUAGE_CODE_MAP,
)

_LOGGER = logging.getLogger(__name__)

# Per-call TTS options exposed to HA services
SUPPORTED_OPTIONS = ["persona", "speed", "format", "sample_rate", "volume_multiplier"]

# Default entity name
DEFAULT_NAME = "kokoro"


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Any
) -> None:
    """Set up TTS platform via config entry."""
    config_data = config_entry.data
    options = config_entry.options or {}

    # Options override data
    merged = {**config_data, **options}

    name = merged.get("name", DEFAULT_NAME)
    base_url = merged[CONF_BASE_URL].rstrip("/")
    api_key = merged.get(CONF_API_KEY, DEFAULT_API_KEY) or DEFAULT_API_KEY
    model = merged.get(CONF_MODEL, DEFAULT_MODEL)
    persona = merged.get(CONF_PERSONA)
    speed = float(merged.get(CONF_SPEED, DEFAULT_SPEED))
    fmt = (merged.get(CONF_FORMAT, DEFAULT_FORMAT) or DEFAULT_FORMAT).lower()
    sample_rate = int(merged.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE))
    language = merged.get(CONF_LANGUAGE)

    entity = KokoroTTSEntity(
        name=name,
        base_url=base_url,
        api_key=api_key,
        model=model,
        persona=persona,
        speed=speed,
        fmt=fmt,
        sample_rate=sample_rate,
        language=language,
    )
    async_add_entities([entity])


class KokoroTTSEntity(TextToSpeechEntity):
    """Kokoro TTS Entity - generates speech via a Kokoro FastAPI server."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        persona: str | None,
        speed: float,
        fmt: str,
        sample_rate: int,
        language: str | None = None,
    ) -> None:
        """Initialize the TTS entity."""
        super().__init__()
        self._attr_name = name
        self._attr_unique_id = f"kokoro_tts_{name}"
        self._base_url = base_url
        self._api_key = api_key
        self._model = model
        self._persona = persona
        self._speed = speed
        self._fmt = fmt
        self._sample_rate = sample_rate
        self._language = language

        # Required TTS entity attributes
        self._attr_default_language = "en"
        self._attr_supported_languages = ["en"]
        self._attr_supported_options = SUPPORTED_OPTIONS

    @staticmethod
    def _handle_http_error(status: int, text: str) -> str:
        """Map HTTP status codes to user-friendly error messages."""
        error_map: dict[int, str] = {
            400: "Bad request - check your text or options",
            401: "Authentication failed - check your API key",
            403: "Access forbidden - insufficient permissions",
            404: "Service not found - check your base URL",
            422: "Invalid request data - check voice/model settings",
            429: "Rate limit exceeded - try again later",
            500: "Server error - Kokoro service issue",
            502: "Bad gateway - service unavailable",
            503: "Service temporarily unavailable",
            504: "Gateway timeout - service too slow",
        }
        return error_map.get(status, f"HTTP {status} error: {text[:200]}")

    def _get_lang_code(self, persona: str | None) -> str | None:
        """Determine the lang_code to send to the API.

        Priority: configured language > first letter of voice name.
        The API uses single-letter codes: a, b, j, z, e, f, h, i, p.
        """
        if self._language and self._language in LANGUAGE_CODE_MAP:
            return LANGUAGE_CODE_MAP[self._language]
        # Fallback: derive from voice name prefix (e.g. "af_heart" -> "a")
        if persona and len(persona) >= 1:
            return persona[0].lower()
        return None

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> TtsAudioType:
        """Get TTS audio from Kokoro API."""
        if not message.strip():
            raise ValueError("Message cannot be empty")

        # Merge entity defaults with per-call options
        opts = options or {}
        persona = opts.get("persona", opts.get("voice", self._persona))
        speed = float(opts.get("speed", self._speed))
        fmt = (opts.get("format", self._fmt) or self._fmt).lower()
        volume_multiplier = float(opts.get("volume_multiplier", DEFAULT_VOLUME_MULTIPLIER))

        # Build API payload
        payload: dict[str, Any] = {
            "model": self._model,
            "input": message,
            "voice": persona or "af_heart",
            "response_format": fmt,
            "download_format": fmt,
            "speed": speed,
            "stream": False,
        }

        # Add lang_code if we can determine one
        lang_code = self._get_lang_code(persona)
        if lang_code:
            payload["lang_code"] = lang_code

        if volume_multiplier != 1.0:
            payload["volume_multiplier"] = volume_multiplier

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key and self._api_key not in ("x", "not-needed", ""):
            headers["Authorization"] = f"Bearer {self._api_key}"

        url = f"{self._base_url}/v1/audio/speech"
        timeout = aiohttp.ClientTimeout(total=60, connect=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.warning(
                        "Kokoro TTS API error %d: %s", response.status, error_text[:200]
                    )
                    error_msg = self._handle_http_error(response.status, error_text)
                    raise RuntimeError(error_msg)

                content_type = response.headers.get("content-type", "").lower()

                if "application/json" in content_type:
                    data = await response.json()
                    if isinstance(data, dict):
                        if "audio" in data:
                            audio_bytes = base64.b64decode(data["audio"])
                        elif "download_url" in data:
                            download_url = data["download_url"]
                            async with session.get(
                                download_url,
                                timeout=aiohttp.ClientTimeout(total=30),
                            ) as dl_resp:
                                if dl_resp.status != 200:
                                    raise RuntimeError(
                                        f"Failed to download audio: HTTP {dl_resp.status}"
                                    )
                                audio_bytes = await dl_resp.read()
                        else:
                            raise RuntimeError(
                                f"JSON response missing audio fields: {list(data.keys())}"
                            )
                    else:
                        raise RuntimeError("Unexpected JSON response type")
                else:
                    # Binary audio response (most common)
                    audio_bytes = await response.read()

                if not audio_bytes:
                    raise RuntimeError("Received empty audio data")

                _LOGGER.debug("TTS audio generated: %d bytes, format: %s", len(audio_bytes), fmt)
                return fmt, audio_bytes
