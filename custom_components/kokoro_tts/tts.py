# custom_components/kokoro_tts/tts.py
from __future__ import annotations
from typing import Any
import logging
import voluptuous as vol
import aiohttp
import asyncio
import base64
import json

from homeassistant.components.tts import (
    PLATFORM_SCHEMA,
)
from homeassistant.components.tts.entity import TextToSpeechEntity, TtsAudioType
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv

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
    DEFAULT_API_KEY,
    DEFAULT_MODEL,
    DEFAULT_SPEED,
    DEFAULT_FORMAT,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_PAD_MS,
)

# -------- Defaults --------
DEFAULT_NAME = "kokoro"
_LOGGER = logging.getLogger(__name__)

# Options you can override per-call via tts.speak -> data.options
SUPPORTED_OPTIONS = ["voice", "speed", "pad_ms", "format", "sample_rate", "volume_multiplier"]


# -------- YAML schema (optional; UI uses config entries) --------
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_BASE_URL): cv.url,
        vol.Optional(CONF_API_KEY, default="x"): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
        vol.Optional(CONF_VOICE, default=None): vol.Any(None, cv.string),
        vol.Optional(CONF_SPEED, default=DEFAULT_SPEED): vol.All(float, vol.Range(min=0.25, max=4.0)),  # Updated to match API range
        vol.Optional(CONF_FORMAT, default=DEFAULT_FORMAT): vol.In(["wav", "mp3", "opus", "flac", "pcm"]),  # Updated formats
        vol.Optional(CONF_SAMPLE_RATE, default=DEFAULT_SAMPLE_RATE): vol.All(int, vol.In([22050, 24000, 44100])),
        vol.Optional(CONF_PAD_MS, default=DEFAULT_PAD_MS): vol.All(int, vol.Range(min=0, max=2000)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


# -------- Entry points for HA --------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up TTS platform via config entry."""
    try:
        _LOGGER.info("Setting up Kokoro TTS entity from config entry")
        _LOGGER.debug("Config entry data: %s", config_entry.data)
        
        config_data = config_entry.data
        name = config_data.get(CONF_NAME, DEFAULT_NAME)
        base_url = config_data[CONF_BASE_URL].rstrip("/")
        api_key = config_data.get(CONF_API_KEY, "x") or "x"
        model = config_data.get(CONF_MODEL, DEFAULT_MODEL)
        voice = config_data.get(CONF_VOICE)
        speed = float(config_data.get(CONF_SPEED, DEFAULT_SPEED))
        fmt = (config_data.get(CONF_FORMAT, DEFAULT_FORMAT) or DEFAULT_FORMAT).lower()
        sample_rate = int(config_data.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE))
        pad_ms = int(config_data.get(CONF_PAD_MS, DEFAULT_PAD_MS))

        _LOGGER.info("Creating KokoroTTSEntity: name=%s, base_url=%s, model=%s, voice=%s", 
                    name, base_url, model, voice)
        
        entity = KokoroTTSEntity(
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
        
        async_add_entities([entity])
        _LOGGER.info("KokoroTTSEntity added successfully")
        
    except Exception as e:
        _LOGGER.error("Failed to setup Kokoro TTS entity: %s", e, exc_info=True)
        raise

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up TTS platform via YAML configuration."""
    try:
        _LOGGER.info("Setting up Kokoro TTS entity from YAML config")
        _LOGGER.debug("YAML config: %s", config)
        
        name = config.get(CONF_NAME, DEFAULT_NAME)
        base_url = config[CONF_BASE_URL].rstrip("/")
        api_key = config.get(CONF_API_KEY, "x") or "x"
        model = config.get(CONF_MODEL, DEFAULT_MODEL)
        voice = config.get(CONF_VOICE)
        speed = float(config.get(CONF_SPEED, DEFAULT_SPEED))
        fmt = (config.get(CONF_FORMAT, DEFAULT_FORMAT) or DEFAULT_FORMAT).lower()
        sample_rate = int(config.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE))
        pad_ms = int(config.get(CONF_PAD_MS, DEFAULT_PAD_MS))

        entity = KokoroTTSEntity(
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
        
        async_add_entities([entity])
        _LOGGER.info("KokoroTTSEntity added successfully from YAML")
        
    except Exception as e:
        _LOGGER.error("Failed to setup Kokoro TTS entity from YAML: %s", e, exc_info=True)
        raise

class KokoroTTSEntity(TextToSpeechEntity):
    """Kokoro TTS Entity."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        voice: str | None,
        speed: float,
        fmt: str,
        sample_rate: int,
        pad_ms: int,
    ) -> None:
        """Initialize the TTS entity."""
        try:
            super().__init__()
            self._attr_name = name
            self._attr_unique_id = f"kokoro_tts_{name}"
            self._base_url = base_url
            self._api_key = api_key
            self._model = model
            self._voice = voice
            self._speed = speed
            self._fmt = fmt
            self._sample_rate = sample_rate
            self._pad_ms = pad_ms
            
            # Required TTS entity attributes
            self._attr_default_language = "en"
            self._attr_supported_languages = ["en"]
            self._attr_supported_options = SUPPORTED_OPTIONS
            
            _LOGGER.info("KokoroTTSEntity initialized successfully: name=%s, base_url=%s", name, base_url)
            
        except Exception as e:
            _LOGGER.error("Failed to initialize KokoroTTSEntity: %s", e, exc_info=True)
            raise

    def _handle_http_error(self, status: int, text: str) -> str:
        """Map HTTP status codes to user-friendly error messages."""
        error_map = {
            400: f"Bad request - check your text or options: {text}",
            401: f"Authentication failed - check your API key: {text}",
            403: f"Access forbidden - insufficient permissions: {text}",
            404: f"Service not found - check your base URL: {text}",
            422: f"Invalid request data - check voice/model settings: {text}",
            429: f"Rate limit exceeded - try again later: {text}",
            500: f"Server error - Kokoro service issue: {text}",
            502: f"Bad gateway - service unavailable: {text}",
            503: f"Service temporarily unavailable: {text}",
            504: f"Gateway timeout - service too slow: {text}",
        }
        
        if 400 <= status < 500:
            _LOGGER.warning("Client error %d: %s", status, text)
        else:
            _LOGGER.error("Server error %d: %s", status, text)
            
        return error_map.get(status, f"HTTP {status} error: {text}")

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> TtsAudioType:
        """Get TTS audio from Kokoro API."""
        try:
            _LOGGER.error("=== TTS REQUEST START ===")
            _LOGGER.error("Message: '%s'", message[:100])
            _LOGGER.error("Language: %s", language)
            _LOGGER.error("Options: %s", options)
            _LOGGER.error("Base URL: %s", self._base_url)
            _LOGGER.error("Model: %s", self._model)
            _LOGGER.error("Voice: %s", self._voice)
            
            if not message.strip():
                raise ValueError("Message cannot be empty")

            # Merge provider defaults with per-call options
            opts = options or {}
            voice = opts.get("voice", self._voice)
            speed = float(opts.get("speed", self._speed))
            fmt = (opts.get("format", self._fmt) or self._fmt).lower()
            sample_rate = int(opts.get("sample_rate", self._sample_rate))
            pad_ms = int(opts.get("pad_ms", self._pad_ms))
            volume_multiplier = float(opts.get("volume_multiplier", 1.0))

            _LOGGER.error("Final TTS config: voice=%s, speed=%s, format=%s, sample_rate=%s", 
                         voice, speed, fmt, sample_rate)

            # Build API payload
            payload = {
                "model": self._model,
                "input": message,
                "response_format": fmt,
                "download_format": fmt,
                "speed": speed,
            }
            
            if voice:
                payload["voice"] = voice
            if volume_multiplier != 1.0:
                payload["volume_multiplier"] = volume_multiplier

            headers = {"Content-Type": "application/json"}
            if self._api_key and self._api_key != "x":
                headers["Authorization"] = f"Bearer {self._api_key}"

            url = f"{self._base_url}/v1/audio/speech"
            _LOGGER.error("Making request to URL: %s", url)
            _LOGGER.error("Payload: %s", payload)
            _LOGGER.error("Headers: %s", {k: "***" if k == "Authorization" else v for k, v in headers.items()})

            # Use same timeout as your successful curl test
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                _LOGGER.error("Starting HTTP POST request...")
                async with session.post(url, json=payload, headers=headers) as response:
                    _LOGGER.error("Response received - Status: %s", response.status)
                    _LOGGER.error("Response headers: %s", dict(response.headers))
                    
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error("API error response: %s", error_text)
                        error_msg = self._handle_http_error(response.status, error_text)
                        raise RuntimeError(error_msg)

                    content_type = response.headers.get("content-type", "").lower()
                    _LOGGER.error("Content-Type: %s", content_type)
                    
                    if "application/json" in content_type:
                        # Handle JSON response
                        data = await response.json()
                        _LOGGER.error("JSON response received: %s", str(data)[:200])
                        
                        if isinstance(data, dict):
                            if "audio" in data:
                                _LOGGER.error("Found base64 audio field")
                                try:
                                    audio_bytes = base64.b64decode(data["audio"])
                                    _LOGGER.error("Successfully decoded base64 audio: %d bytes", len(audio_bytes))
                                except Exception as e:
                                    _LOGGER.error("Base64 decode failed: %s", e)
                                    raise RuntimeError(f"Failed to decode base64 audio: {e}")
                            elif "download_url" in data:
                                download_url = data["download_url"]
                                _LOGGER.error("Found download URL: %s", download_url)
                                async with session.get(download_url, timeout=aiohttp.ClientTimeout(total=30)) as dl_resp:
                                    if dl_resp.status != 200:
                                        dl_error = await dl_resp.text()
                                        _LOGGER.error("Download failed: %s", dl_error)
                                        raise RuntimeError(f"Failed to download audio: {dl_error}")
                                    audio_bytes = await dl_resp.read()
                                    _LOGGER.error("Downloaded audio: %d bytes", len(audio_bytes))
                            else:
                                _LOGGER.error("JSON missing audio fields. Keys: %s", list(data.keys()))
                                raise RuntimeError(f"JSON response missing audio fields: {list(data.keys())}")
                        else:
                            _LOGGER.error("Unexpected JSON type: %s", type(data))
                            raise RuntimeError(f"Unexpected JSON response type: {type(data)}")
                    else:
                        # Handle binary audio response
                        _LOGGER.error("Binary response received")
                        audio_bytes = await response.read()
                        _LOGGER.error("Binary audio received: %d bytes", len(audio_bytes))

                    if not audio_bytes:
                        _LOGGER.error("Empty audio data received")
                        raise RuntimeError("Received empty audio data")

                    # Apply padding if requested and format is WAV
                    if pad_ms > 0 and fmt == "wav":
                        _LOGGER.error("Applying %d ms padding", pad_ms)
                        silence_samples = int((sample_rate * pad_ms) / 1000)
                        silence_bytes = b'\x00' * (silence_samples * 2)
                        audio_bytes = silence_bytes + audio_bytes + silence_bytes

                    _LOGGER.error("=== TTS SUCCESS: %d bytes, format: %s ===", len(audio_bytes), fmt)
                    return fmt, audio_bytes

        except Exception as e:
            _LOGGER.error("=== TTS FAILED ===")
            _LOGGER.error("Exception type: %s", type(e).__name__)
            _LOGGER.error("Exception message: %s", str(e))
            _LOGGER.error("Full traceback:", exc_info=True)
            _LOGGER.error("=== END TTS FAILED ===")
            # Re-raise the exception so HA can handle it
            raise