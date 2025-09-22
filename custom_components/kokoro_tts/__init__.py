from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.websocket_api import async_register_command

from .const import DOMAIN
from .config_flow import websocket_preview_audio

PLATFORMS = [Platform.TTS]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kokoro TTS from a config entry."""
    
    # Register WebSocket command for audio preview
    async_register_command(hass, websocket_preview_audio)
    
    # For TTS platforms, we need to forward the setup to the TTS platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)