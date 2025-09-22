from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = [Platform.TTS]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Kokoro TTS component."""
    # Register WebSocket command for audio preview
    try:
        from homeassistant.components.websocket_api import async_register_command
        from .config_flow import websocket_preview_audio
        async_register_command(hass, websocket_preview_audio)
    except ImportError:
        # WebSocket API not available, skip preview functionality
        pass
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kokoro TTS from a config entry."""
    
    # For TTS platforms, we need to forward the setup to the TTS platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)