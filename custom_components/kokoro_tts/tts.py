# custom_components/kokoro_tts/tts.py
from __future__ import annotations

import asyncio
import io
import json
import logging
from typing import Any, Tuple

import aiohttp
import voluptuous as vol

from homeassistant.components.tts import (
    PLATFORM_SCHEMA,
    Provider,
)
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

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
async def async_get_engine(hass, config, discovery_info=None):
    """
    Called by HA when the platform is set up via YAML (tts:).
    For UI (config entry) setups, HA will forward the entry data here too,
    so we support both paths by reading from `config` dict.
    """
    name = config.get(CONF_NAME, DEFAULT_NAME)
    base_url = config[CONF_BASE_URL].rstrip("/")
    api_key = config.get(CONF_API_KEY, "x") or "x"
    model = config.get(CONF_MODEL, DEFAULT_MODEL)
    voice = config.get(CONF_VOICE)
    speed = float(config.get(CONF_SPEED, DEFAULT_SPEED))
    fmt = (config.get(CONF_FORMAT, DEFAULT_FORMAT) or DEFAULT_FORMAT).lower()
    sample_rate = int(config.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE))
    pad_ms = int(config.get(CONF_PAD_MS, DEFAULT_PAD_MS))

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


# -------- Provider implementation --------
class KokoroProvider(Provider):
    """Home Assistant TTS Provider for Kokoro FastAPI."""

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
        self._name = name
        self._base_url = base_url
        self._api_key = api_key or "x"
        self._model = model
        self._voice = voice
        self._speed = speed
        self._fmt = fmt
        self._sr = sample_rate
        self._pad_ms = pad_ms

    @property
    def default_language(self) -> str:
        return "en"

    @property
    def supported_languages(self) -> list[str]:
        return ["en"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_options(self) -> list[str]:
        # Allow per-call overrides for these
        return SUPPORTED_OPTIONS

    async def _handle_http_error(self, resp: aiohttp.ClientResponse) -> None:
        """Handle HTTP errors with granular logging and user-friendly messages."""
        try:
            error_text = await resp.text()
        except Exception:
            error_text = "(unable to read error response)"

        if resp.status == 400:
            _LOGGER.warning("Kokoro TTS bad request (400): Invalid parameters or malformed request - %s", error_text)
            raise RuntimeError("Invalid request parameters. Check your model, voice, and format settings.")
        elif resp.status == 401:
            _LOGGER.warning("Kokoro TTS authentication failed (401): Invalid API key - %s", error_text) 
            raise RuntimeError("Authentication failed. Check your API key configuration.")
        elif resp.status == 403:
            _LOGGER.warning("Kokoro TTS access forbidden (403): Insufficient permissions - %s", error_text)
            raise RuntimeError("Access forbidden. Your API key may not have permission for this operation.")
        elif resp.status == 404:
            _LOGGER.warning("Kokoro TTS endpoint not found (404): Check base URL and API version - %s", error_text)
            raise RuntimeError("TTS endpoint not found. Verify your base URL configuration.")
        elif resp.status == 422:
            _LOGGER.warning("Kokoro TTS validation error (422): Invalid input parameters - %s", error_text)
            raise RuntimeError("Input validation failed. Check your text, voice, or model parameters.")
        elif resp.status == 429:
            _LOGGER.warning("Kokoro TTS rate limited (429): Too many requests - %s", error_text)
            raise RuntimeError("Rate limit exceeded. Please wait before making more requests.")
        elif resp.status == 500:
            _LOGGER.error("Kokoro TTS server error (500): Internal server issue - %s", error_text)
            raise RuntimeError("Server error. The TTS service is experiencing issues.")
        elif resp.status == 502:
            _LOGGER.error("Kokoro TTS bad gateway (502): Upstream server issue - %s", error_text)
            raise RuntimeError("Bad gateway. The TTS service may be temporarily unavailable.")
        elif resp.status == 503:
            _LOGGER.error("Kokoro TTS service unavailable (503): Server overloaded or maintenance - %s", error_text)
            raise RuntimeError("Service unavailable. The TTS service may be under maintenance.")
        elif resp.status == 504:
            _LOGGER.error("Kokoro TTS gateway timeout (504): Request took too long - %s", error_text)
            raise RuntimeError("Gateway timeout. The TTS request took too long to process.")
        else:
            _LOGGER.error("Kokoro TTS unexpected HTTP error (%d): %s", resp.status, error_text)
            raise RuntimeError(f"HTTP {resp.status}: {error_text}")

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> Tuple[str, bytes] | None:
        """Generate audio bytes for the given text."""
        opts = options or {}
        voice = opts.get("voice", self._voice)
        speed = float(opts.get("speed", self._speed))
        pad_ms = int(opts.get("pad_ms", self._pad_ms))
        fmt = (opts.get("format") or self._fmt).lower()
        sample_rate = int(opts.get("sample_rate", self._sr))
        volume_multiplier = float(opts.get("volume_multiplier", 1.0))

        # Build Kokoro FastAPI (OpenAI-style) payload
        payload: dict[str, Any] = {
            "model": self._model,
            "input": message,
            "response_format": fmt,  # format we want returned (raw bytes)
            "download_format": fmt,  # if server differentiates, keep aligned
            "stream": False,  # Disable streaming for Home Assistant
        }
        if voice:
            payload["voice"] = voice
        if speed and abs(speed - 1.0) > 1e-6:
            payload["speed"] = speed
        if volume_multiplier and abs(volume_multiplier - 1.0) > 1e-6:
            payload["volume_multiplier"] = volume_multiplier

        url = f"{self._base_url}/v1/audio/speech"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(url, headers=headers, data=json.dumps(payload)) as resp:
                    if resp.status != 200:
                        await self._handle_http_error(resp)

                    # Some Kokoro deployments may return raw bytes directly with audio mime,
                    # others might return JSON (download link or base64 string). Try to detect.
                    ctype = resp.headers.get("Content-Type", "").lower()
                    if "application/json" in ctype:
                        data = await resp.json()
                        # If API returns a direct string (OpenAI style sample?), handle that.
                        if isinstance(data, str):
                            # Assume base64 encoded? If so we would need to decode; keeping raw for now.
                            # Without spec certainty, treat as error to surface debugging.
                            _LOGGER.error("Unexpected JSON string response from Kokoro TTS; expected binary audio or structured data")
                            raise RuntimeError("Unexpected JSON string response; expected binary audio")
                        # Try common keys for sources
                        if "audio" in data and isinstance(data["audio"], str):
                            # Could be base64; attempt decode if it looks like base64
                            import base64, binascii
                            aud_str = data["audio"]
                            try:
                                audio = base64.b64decode(aud_str)
                            except (binascii.Error, ValueError):
                                _LOGGER.error("Failed to decode base64 audio field from Kokoro TTS response")
                                raise RuntimeError("Failed to decode base64 audio field")
                        elif data.get("download_url"):
                            dl = data["download_url"]
                            async with session.get(dl) as dl_resp:
                                if dl_resp.status != 200:
                                    _LOGGER.error("Failed to download audio from URL %s (status %d)", dl, dl_resp.status)
                                    raise RuntimeError(f"Download URL fetch failed {dl_resp.status}")
                                audio = await dl_resp.read()
                        else:
                            _LOGGER.error("JSON response from Kokoro TTS did not contain expected audio or download_url fields")
                            raise RuntimeError("JSON response did not contain audio or download_url")
                    else:
                        audio = await resp.read()
            except aiohttp.ClientError as e:
                _LOGGER.error("Network error connecting to Kokoro TTS at %s: %s", url, e)
                raise RuntimeError(f"Network error: {e}")
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout connecting to Kokoro TTS at %s", url)
                raise RuntimeError("Request timeout")
            except Exception as e:
                _LOGGER.error("Unexpected error during Kokoro TTS request: %s", e)
                raise RuntimeError(f"Unexpected error: {e}")

        # Optional pre-padding only makes sense for WAV (PCM16)
        if pad_ms > 0 and fmt == "wav":
            try:
                audio = _prepend_wav_silence(audio, pad_ms, sample_rate)
            except Exception:
                # If anything goes wrong, fall back to raw audio
                pass

        # Map format to file extension based on API supported formats
        ext_map = {
            "mp3": "mp3",
            "opus": "opus", 
            "flac": "flac",
            "pcm": "wav",  # PCM returns as wav for Home Assistant
            "wav": "wav"
        }
        ext = ext_map.get(fmt, "wav")
        return ext, audio


# -------- Helpers --------
def _prepend_wav_silence(wav_bytes: bytes, pad_ms: int, sample_rate: int) -> bytes:
    """
    Prepend silence to a PCM16 mono/stereo WAV by inserting zero samples and
    rewriting the header accordingly.

    Assumes Kokoro returns linear PCM (sampwidth=2) at requested sample_rate.
    If not PCM16, returns original bytes.
    """
    import wave

    pad_frames = int(round(sample_rate * (pad_ms / 1000.0)))
    if pad_frames <= 0:
        return wav_bytes

    with wave.open(io.BytesIO(wav_bytes), "rb") as r:
        n_channels = r.getnchannels()
        sampwidth = r.getsampwidth()
        framerate = r.getframerate()
        n_frames = r.getnframes()
        comptype = r.getcomptype()
        audio_frames = r.readframes(n_frames)

    # Only handle PCM16 neatly
    if sampwidth != 2 or comptype != "NONE" or framerate != sample_rate:
        return wav_bytes

    # Build silence matching channel count
    silence = b"\x00\x00" * pad_frames * n_channels
    new_frames = silence + audio_frames

    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(n_channels)
        w.setsampwidth(sampwidth)
        w.setframerate(sample_rate)
        w.writeframes(new_frames)

    return out.getvalue()
