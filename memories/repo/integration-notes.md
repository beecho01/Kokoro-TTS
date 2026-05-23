# Kokoro TTS Integration - Key Decisions & Notes

## API Compatibility (as of May 2026)
- `/v1/audio/voices` now returns `[{"id": ..., "name": ...}]` by default (not plain strings)
  - Use `?legacy=true` for plain string format
  - Our config_flow handles both formats
- `/v1/audio/speech` supports `lang_code` parameter (single-letter: a, b, j, z, e, f, h, i, p)
- `/v1/audio/speech` supports `stream: False` for non-streaming responses
- `volume_multiplier` is a per-call API parameter
- API default format is `mp3` (not `wav`)
- API default speed is `1.0` (not `0.9`)
- `ClientSSLError` is a subclass of `ClientConnectorError` - must catch SSL first

## Config Flow Pattern
- Filter changes detected by checking if persona is empty (no persona selected = filter change)
- Persona display names are contextual based on active filters
- Connection test runs in step 1 before proceeding to step 2
- Reauth flow added for API key updates

## Type Hints
- `ConfigFlowResult` not available in older HA versions - omit return type annotations on async_step methods
- Use `from __future__ import annotations` in all files