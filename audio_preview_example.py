# Example implementation for audio preview
# This would be added to your config_flow.py

import aiohttp
import asyncio
from homeassistant import websocket_api
from homeassistant.core import HomeAssistant, callback

# Add this to your config flow constants
CONF_PREVIEW_TEXT = "preview_text"
DEFAULT_PREVIEW_TEXT = "Hello, this is a preview of the selected persona."

# Add preview support to your form schema
def _details_schema_with_preview(models: list[str], personas: list[str], user_input: dict | None = None) -> vol.Schema:
    """Schema for details step with audio preview support."""
    # ... existing schema code ...
    
    # Add preview text input
    schema[vol.Optional(CONF_PREVIEW_TEXT, default=DEFAULT_PREVIEW_TEXT)] = cv.string
    
    return vol.Schema(schema)

# WebSocket command for audio preview
@websocket_api.websocket_command(
    {
        vol.Required("type"): "kokoro_tts/start_preview",
        vol.Required("flow_id"): str,
        vol.Required("flow_type"): vol.Any("config_flow", "options_flow"),
        vol.Required("user_input"): dict,
    }
)
@websocket_api.async_response
async def ws_start_audio_preview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Generate audio preview."""
    try:
        user_input = msg["user_input"]
        
        # Get preview settings from user input
        preview_text = user_input.get(CONF_PREVIEW_TEXT, DEFAULT_PREVIEW_TEXT)
        selected_persona = user_input.get(CONF_PERSONA)
        base_url = user_input.get(CONF_BASE_URL)  # Would need to get from flow context
        
        if not selected_persona or not base_url:
            connection.send_error(msg["id"], "missing_config", "Missing persona or base URL")
            return
            
        # Convert display name to technical name
        technical_persona = get_technical_persona_name(selected_persona)
        
        # Generate preview audio
        try:
            models, personas = await _discover_models_and_personas(base_url, "")
            
            # Create a temporary TTS request
            payload = {
                "model": user_input.get(CONF_MODEL, "kokoro"),
                "input": preview_text,
                "voice": technical_persona,
                "response_format": "wav",
                "speed": user_input.get(CONF_SPEED, 0.9),
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{base_url}/v1/audio/speech", json=payload) as resp:
                    if resp.status == 200:
                        audio_data = await resp.read()
                        
                        # Send audio data as base64
                        import base64
                        audio_b64 = base64.b64encode(audio_data).decode()
                        
                        connection.send_result(msg["id"])
                        connection.send_message({
                            "type": "event",
                            "event": {
                                "type": "audio_preview",
                                "audio_data": audio_b64,
                                "audio_format": "wav",
                                "persona": selected_persona,
                                "text": preview_text
                            }
                        })
                    else:
                        connection.send_error(msg["id"], "preview_failed", f"TTS request failed: {resp.status}")
                        
        except Exception as e:
            connection.send_error(msg["id"], "preview_error", str(e))
            
    except Exception as e:
        connection.send_error(msg["id"], "unexpected_error", str(e))

# Add preview setup to your config flow class
class KokoroConfigFlow(config_entries.ConfigFlow):
    # ... existing code ...
    
    @staticmethod
    async def async_setup_preview(hass: HomeAssistant) -> None:
        """Set up preview WS API."""
        websocket_api.async_register_command(hass, ws_start_audio_preview)

# Update your form display to include preview
def _details_schema(models: list[str], personas: list[str], user_input: dict | None = None) -> vol.Schema:
    """Schema for details step with dynamic selectors."""
    # ... existing schema code ...
    
    # Add preview text field
    schema[vol.Optional(CONF_PREVIEW_TEXT, default=ui.get(CONF_PREVIEW_TEXT, DEFAULT_PREVIEW_TEXT))] = cv.string
    
    result = vol.Schema(schema)
    return result

# Update async_show_form calls to include preview
return self.async_show_form(
    step_id="details",
    data_schema=schema,
    preview="kokoro_tts",  # This enables the preview system
)