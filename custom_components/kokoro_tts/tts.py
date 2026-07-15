"""Kokoro TTS entity for Home Assistant."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import aiohttp
import base64
import logging
import re

from homeassistant.components.tts.entity import (
    TextToSpeechEntity,
    TTSAudioRequest,
    TTSAudioResponse,
    TtsAudioType,
)
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
    DEFAULT_STREAM_FORMAT,
    DEFAULT_VOLUME_MULTIPLIER,
    DOMAIN,
    LANGUAGE_CODE_MAP,
    STREAM_SAFE_FORMATS,
)

_LOGGER = logging.getLogger(__name__)

# Per-call TTS options exposed to HA services
SUPPORTED_OPTIONS = ["persona", "speed", "format", "sample_rate", "volume_multiplier"]

# Default entity name
DEFAULT_NAME = "kokoro"

# Size of the audio chunks yielded while streaming a sentence.
STREAM_CHUNK_BYTES = 4096

# A sentence ends on terminal punctuation followed by whitespace. Requiring the
# trailing whitespace keeps decimals ("12.5") and mid-generation abbreviations
# from being treated as sentence boundaries.
SENTENCE_END_PATTERN = re.compile(r"[.!?…]+[\"'”’)\]]*\s+")


def split_sentences(buffer: str) -> tuple[list[str], str]:
    """Split a text buffer into complete sentences plus a trailing remainder.

    The remainder is text that has not yet been terminated by punctuation; it is
    kept in the buffer until more text arrives, or flushed when the stream ends.
    """
    sentences: list[str] = []
    last_end = 0
    for match in SENTENCE_END_PATTERN.finditer(buffer):
        sentence = buffer[last_end : match.end()].strip()
        if sentence:
            sentences.append(sentence)
        last_end = match.end()
    return sentences, buffer[last_end:]


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

    def _resolve_options(self, options: dict[str, Any] | None) -> dict[str, Any]:
        """Merge entity defaults with per-call options."""
        opts = options or {}
        return {
            "persona": opts.get("persona", opts.get("voice", self._persona)),
            "speed": float(opts.get("speed", self._speed)),
            "fmt": (opts.get("format", self._fmt) or self._fmt).lower(),
            "volume_multiplier": float(
                opts.get("volume_multiplier", DEFAULT_VOLUME_MULTIPLIER)
            ),
        }

    def _build_payload(
        self, message: str, resolved: dict[str, Any], *, stream: bool
    ) -> dict[str, Any]:
        """Build the /v1/audio/speech request payload."""
        persona = resolved["persona"]
        payload: dict[str, Any] = {
            "model": self._model,
            "input": message,
            "voice": persona or "af_heart",
            "response_format": resolved["fmt"],
            "download_format": resolved["fmt"],
            "speed": resolved["speed"],
            "stream": stream,
        }

        # Add lang_code if we can determine one
        lang_code = self._get_lang_code(persona)
        if lang_code:
            payload["lang_code"] = lang_code

        if resolved["volume_multiplier"] != 1.0:
            payload["volume_multiplier"] = resolved["volume_multiplier"]

        return payload

    def _build_headers(self) -> dict[str, str]:
        """Build the request headers, including auth when configured."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key and self._api_key not in ("x", "not-needed", ""):
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    @property
    def _speech_url(self) -> str:
        """Return the speech endpoint URL."""
        return f"{self._base_url}/v1/audio/speech"

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> TtsAudioType:
        """Get TTS audio from Kokoro API."""
        if not message.strip():
            raise ValueError("Message cannot be empty")

        resolved = self._resolve_options(options)
        fmt = resolved["fmt"]
        payload = self._build_payload(message, resolved, stream=False)
        timeout = aiohttp.ClientTimeout(total=60, connect=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._speech_url, json=payload, headers=self._build_headers()
            ) as response:
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

    def async_supports_streaming_input(self) -> bool:
        """Return True - text can be consumed as it is generated.

        This lets the Assist pipeline forward the conversation agent's output as
        it arrives instead of buffering the whole reply, so synthesis can start
        on the first finished sentence.
        """
        return True

    async def async_stream_tts_audio(
        self, request: TTSAudioRequest
    ) -> TTSAudioResponse:
        """Stream audio, synthesising each sentence as soon as it is complete."""
        resolved = self._resolve_options(request.options)
        fmt = resolved["fmt"]

        # Streaming issues one request per sentence and concatenates the audio.
        # Container formats carrying a per-file header (wav, flac) cannot be
        # concatenated that way, so fall back to a stream-safe format.
        if fmt not in STREAM_SAFE_FORMATS:
            _LOGGER.debug(
                "Format %s cannot be concatenated while streaming, using %s instead",
                fmt,
                DEFAULT_STREAM_FORMAT,
            )
            fmt = DEFAULT_STREAM_FORMAT
            resolved = {**resolved, "fmt": fmt}

        return TTSAudioResponse(
            extension=fmt,
            data_gen=self._async_stream_audio(request.message_gen, resolved),
        )

    async def _async_stream_audio(
        self, message_gen: AsyncGenerator[str], resolved: dict[str, Any]
    ) -> AsyncGenerator[bytes]:
        """Consume the text stream and yield audio for each complete sentence."""
        # No total timeout: the generator lives as long as the agent is talking.
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=60)
        sentence_count = 0

        async with aiohttp.ClientSession(timeout=timeout) as session:
            buffer = ""
            async for chunk in message_gen:
                buffer += chunk
                sentences, buffer = split_sentences(buffer)
                for sentence in sentences:
                    sentence_count += 1
                    async for audio in self._async_stream_sentence(
                        session, sentence, resolved
                    ):
                        yield audio

            # Flush the tail: the last sentence often has no trailing whitespace.
            tail = buffer.strip()
            if tail:
                sentence_count += 1
                async for audio in self._async_stream_sentence(session, tail, resolved):
                    yield audio

        _LOGGER.debug(
            "TTS stream complete: %d sentence(s), format: %s",
            sentence_count,
            resolved["fmt"],
        )

    async def _async_stream_sentence(
        self,
        session: aiohttp.ClientSession,
        message: str,
        resolved: dict[str, Any],
    ) -> AsyncGenerator[bytes]:
        """Synthesise one sentence and yield its audio as it arrives."""
        payload = self._build_payload(message, resolved, stream=True)

        async with session.post(
            self._speech_url, json=payload, headers=self._build_headers()
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                _LOGGER.warning(
                    "Kokoro TTS API error %d: %s", response.status, error_text[:200]
                )
                raise RuntimeError(
                    self._handle_http_error(response.status, error_text)
                )

            async for chunk in response.content.iter_chunked(STREAM_CHUNK_BYTES):
                if chunk:
                    yield chunk
