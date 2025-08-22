"""The NC2 Controller integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN
from .api import NC2ApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["switch", "light"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NC2 Controller from a config entry."""

    host = entry.data.get("host")
    username = entry.data.get("username")
    password = entry.data.get("password")

    session = aiohttp_client.async_get_clientsession(hass)
    nc2_api = NC2ApiClient(host, username, password, session)

    try:
        await nc2_api.authenticate()
    except Exception as ex:
        _LOGGER.error("Failed to connect to NC2 Controller at %s: %s", host, ex)
        raise ConfigEntryNotReady from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = nc2_api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
