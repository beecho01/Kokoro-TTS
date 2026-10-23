"""Kokoro TTS Home Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

# Entity unique IDs used to be "kokoro_tts_<name>". The name is the same for
# every entry, so a second entry's entity collided with the first and was
# never created.
LEGACY_UNIQUE_ID_PREFIX = "kokoro_tts_"

PLATFORMS = [Platform.TTS]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Kokoro TTS component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kokoro TTS from a config entry."""
    await _async_migrate_unique_id(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_migrate_unique_id(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Move this entry's entity from the legacy unique ID to the entry ID.

    The entity keeps its entity_id and user customisations, so assist
    pipelines and automations that reference it keep working.
    """

    @callback
    def _migrate(entity_entry: er.RegistryEntry) -> dict[str, str] | None:
        if entity_entry.unique_id.startswith(LEGACY_UNIQUE_ID_PREFIX):
            _LOGGER.debug(
                "Migrating %s unique ID from %s to %s",
                entity_entry.entity_id,
                entity_entry.unique_id,
                entry.entry_id,
            )
            return {"new_unique_id": entry.entry_id}
        return None

    await er.async_migrate_entries(hass, entry.entry_id, _migrate)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
