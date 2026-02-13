# -*- coding: utf-8 -*-
"""The PetroChina Gas Statistics integration."""

import logging
from typing import List
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ACCOUNTS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: List[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up PetroChina Gas Statistics from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading entry: {config_entry.title}")
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    _LOGGER.debug(f"Unload platforms for entry: {config_entry.title}, success: {unload_ok}")
    hass.data[DOMAIN].pop(config_entry.entry_id)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    _LOGGER.info("Removing entry: account %s", entry.data.get("user_code", "unknown"))
