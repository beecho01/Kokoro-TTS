# custom_components/kokoro_tts/tts.py
from __future__ import annotations
from typing import Any, Tuple
import logging
import voluptuous as vol
import aiohttp
import asyncio
import base64
import json

from homeassistant.components.tts import (
    PLATFORM_SCHEMA,
    Provider,
)
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
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up TTS platform via YAML configuration."""
    _LOGGER.debug("async_setup_platform called with config: %s", config)
    provider = await async_get_engine(hass, config, discovery_info)
    async_add_entities([provider])

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up TTS platform via config entry."""
    _LOGGER.debug("async_setup_entry called with entry data: %s", config_entry.data)
    provider = await async_get_engine(hass, config_entry.data)
    async_add_entities([provider])

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

class KokoroProvider(Provider):
    """Kokoro TTS Provider."""

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
        """Initialize the provider."""
        self._name = name
        self._base_url = base_url
        self._api_key = api_key
        self._model = model
        self._voice = voice
        self._speed = speed
        self._fmt = fmt
        self._sample_rate = sample_rate
        self._pad_ms = pad_ms
        _LOGGER.debug("KokoroProvider initialized: name=%s, base_url=%s", name, base_url)

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return "en"

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["en"]

    @property
    def supported_options(self) -> list[str]:
        """Return list of supported options."""
        return SUPPORTED_OPTIONS

    @property
    def name(self) -> str:
        """Return name of the TTS provider."""
        return self._name

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
    ) -> Tuple[str, bytes]:
        """Get TTS audio from Kokoro API."""
        _LOGGER.debug("Getting TTS audio for message: %s, language: %s, options: %s", message, language, options)
        
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

        _LOGGER.debug("Final options: voice=%s, speed=%s, format=%s, sample_rate=%s, pad_ms=%s, volume_multiplier=%s", 
                     voice, speed, fmt, sample_rate, pad_ms, volume_multiplier)

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
        _LOGGER.debug("Making request to: %s with payload: %s", url, payload)

        timeout = aiohttp.ClientTimeout(total=30)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    _LOGGER.debug("Response status: %s", response.status)
                    
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = self._handle_http_error(response.status, error_text)
                        raise RuntimeError(error_msg)

                    content_type = response.headers.get("content-type", "").lower()
                    _LOGGER.debug("Response content-type: %s", content_type)
                    
                    if "application/json" in content_type:
                        # Handle JSON response (might contain base64 audio or download URL)
                        data = await response.json()
                        _LOGGER.debug("JSON response received")
                        
                        if isinstance(data, dict):
                            # Check for base64 audio
                            if "audio" in data:
                                _LOGGER.debug("Found base64 audio in response")
                                try:
                                    audio_bytes = base64.b64decode(data["audio"])
                                except Exception as e:
                                    raise RuntimeError(f"Failed to decode base64 audio: {e}")
                            # Check for download URL
                            elif "download_url" in data:
                                download_url = data["download_url"]
                                _LOGGER.debug("Found download URL: %s", download_url)
                                async with session.get(download_url) as dl_resp:
                                    if dl_resp.status != 200:
                                        dl_error = await dl_resp.text()
                                        raise RuntimeError(f"Failed to download audio from {download_url}: {dl_error}")
                                    audio_bytes = await dl_resp.read()
                            else:
                                raise RuntimeError(f"JSON response missing 'audio' or 'download_url' fields: {data}")
                        elif isinstance(data, str):
                            raise RuntimeError(f"Unexpected JSON string response: {data}")
                        else:
                            raise RuntimeError(f"Unexpected JSON response type: {type(data)}")
                    else:
                        # Handle binary audio response
                        _LOGGER.debug("Binary audio response received")
                        audio_bytes = await response.read()

                    _LOGGER.debug("Audio received: %d bytes", len(audio_bytes))

                    # Apply padding if requested and format is WAV
                    if pad_ms > 0 and fmt == "wav":
                        _LOGGER.debug("Applying %d ms padding to WAV audio", pad_ms)
                        # Simple padding implementation - you might want to enhance this
                        silence_samples = int((sample_rate * pad_ms) / 1000)
                        silence_bytes = b'\x00' * (silence_samples * 2)  # 16-bit samples
                        # This is a simplified approach - proper WAV padding requires header manipulation
                        audio_bytes = silence_bytes + audio_bytes + silence_bytes

                    return fmt, audio_bytes

        except aiohttp.ClientError as e:
            _LOGGER.error("Network error connecting to Kokoro TTS: %s", e)
            raise RuntimeError(f"Network error: {e}")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout connecting to Kokoro TTS")
            raise RuntimeError("Request timeout - Kokoro service too slow")
        except Exception as e:
            _LOGGER.error("Unexpected error in async_get_tts_audio: %s", e)
            raise RuntimeError(f"Unexpected error: {e}")