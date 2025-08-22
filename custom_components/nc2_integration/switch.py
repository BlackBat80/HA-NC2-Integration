import logging
import json
from typing import Any, Dict

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import mqtt

from .const import DOMAIN
from .api import NC2ApiClient

_LOGGER = logging.getLogger(__name__)

MQTT_TOPIC_RELAYS = "nc2/+/back/+/relays/+"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NC2 Controller switches from a config entry."""
    nc2_api: NC2ApiClient = hass.data[DOMAIN][entry.entry_id]

    relays_data = await nc2_api.get_relays_status(1)

    if not relays_data:
        _LOGGER.warning("No relays found on module 1. Cannot set up switches.")
        return

    switches = [NC2Switch(nc2_api, relay_data) for relay_data in relays_data]
    async_add_entities(switches)

    @callback
    def message_received(message: mqtt.ReceiveMessage) -> None:
        """Handle new MQTT messages for relays."""
        try:
            relay_id = int(message.topic.split("/")[-1])
            payload = json.loads(message.payload)

            for switch in switches:
                if switch.unique_id == f"nc2_relay_{relay_id}":
                    switch.update_state_from_mqtt(payload)
                    break
        except (json.JSONDecodeError, IndexError, ValueError) as e:
            _LOGGER.error("Failed to parse MQTT message for relay: %s. Topic: %s, Payload: %s", e, message.topic, message.payload)

    await mqtt.async_subscribe(hass, MQTT_TOPIC_RELAYS, message_received, 1)


class NC2Switch(SwitchEntity):
    """Representation of an NC2 Controller Switch."""

    def __init__(self, api: NC2ApiClient, relay_data: Dict[str, Any]) -> None:
        """Initialize the switch."""
        self._api = api
        self._relay_data = relay_data
        self._attr_name = f"Relay {relay_data.get('id')}"
        self._attr_unique_id = f"nc2_relay_{relay_data.get('id')}"
        self._attr_is_on = self._relay_data.get("on", False)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        relay_id = self._relay_data.get("id")
        await self._api.control_relay(relay_id, True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        relay_id = self._relay_data.get("id")
        await self._api.control_relay(relay_id, False)
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def update_state_from_mqtt(self, payload: Dict[str, Any]) -> None:
        """Update the switch's state from an MQTT message."""
        if "on" in payload:
            self._attr_is_on = payload["on"]
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True