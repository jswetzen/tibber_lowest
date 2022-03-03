"""Tibber lowest price"""
import asyncio
import logging

from .const import DOMAIN

from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.helpers import discovery

from homeassistant import config_entries, core

DEPENDENCIES = ["tibber"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform.
    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_START,
        hass.config_entries.async_forward_entry_setup(entry, "sensor"),
    )
    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Tibber lowest component from yaml configuration."""
    hass.data.setdefault(DOMAIN, config.get(DOMAIN, {}))

    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_START,
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config),
    )
    return True


# def setup(hass: core.HomeAssistant, config: dict):
#    """Setup component."""
#
#    hass.data[DOMAIN] = config[DOMAIN]
#
#    def ha_started(_):
#        discovery.load_platform(hass, "sensor", DOMAIN, {}, config)
#
#    hass.bus.async_listen_once()
#    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, ha_started)
#
#    return True
