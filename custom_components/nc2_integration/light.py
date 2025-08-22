import logging
import json
import math
from typing import Any, Dict

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import mqtt

from .const import DOMAIN
from .api import NC2ApiClient

_LOGGER = logging.getLogger(__name__)

# The correct MQTT topic structure, as confirmed by the user.
MQTT_TOPIC = "nc2/+/back/+/luminaires/+"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NC2 Controller lights from a config entry."""
    nc2_api: NC2ApiClient = hass.data[DOMAIN][entry.entry_id]

    luminaires = await nc2_api.get_luminaires()
    if not luminaires:
        _LOGGER.warning("No luminaires found. Cannot set up lights.")
        return

    lights = [NC2Light(nc2_api, data) for data in luminaires]
    async_add_entities(lights)

    @callback
    def message_received(message: mqtt.ReceiveMessage) -> None:
        """Handle new MQTT messages."""
        _LOGGER.debug("MQTT message received. Topic: %s, Payload: %s", message.topic, message.payload)
        try:
            luminaire_id = int(message.topic.split("/")[-1])
            payload = json.loads(message.payload)

            for light in lights:
                if light.unique_id == f"nc2_luminaire_{luminaire_id}":
                    _LOGGER.debug("Found matching light entity for ID %d. Updating state.", luminaire_id)
                    light.update_state_from_mqtt(payload)
                    break
        except (json.JSONDecodeError, IndexError, ValueError) as e:
            _LOGGER.error("Failed to parse MQTT message: %s. Topic: %s, Payload: %s", e, message.topic, message.payload)

    await mqtt.async_subscribe(hass, MQTT_TOPIC, message_received, 1)


class NC2Light(LightEntity):
    """Representation of an NC2 Controller Light."""

    def __init__(self, api: NC2ApiClient, luminaire_data: Dict[str, Any]) -> None:
        """Initialize the light."""
        self._api = api
        self._luminaire_data = luminaire_data
        self._attr_unique_id = f"nc2_luminaire_{self._luminaire_data.get('id')}"
        self._attr_name = self._luminaire_data.get("name", f"Luminaire {self._luminaire_data.get('id')}")

        self._attr_supported_color_modes = set()
        if self._luminaire_data.get("dimming") is not None:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        if self._luminaire_data.get("lightTemperature") is not None:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)

        if not self._attr_supported_color_modes:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

        self._attr_color_mode = ColorMode.BRIGHTNESS if ColorMode.BRIGHTNESS in self._attr_supported_color_modes else ColorMode.ONOFF
        if ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP

        self._update_state(self._luminaire_data)

    def _update_state(self, data):
        """Update internal state from a data dictionary (REST or MQTT)."""
        self._attr_is_on = data.get("on", False)
        self._attr_brightness = data.get("dimming", 0)
        self._attr_color_temp = data.get("lightTemperature")
        self._luminaire_data["status"] = data.get("status", "offline")

    @property
    def available(self) -> bool:
        return self._luminaire_data.get("status") == "online"

    async def async_turn_on(self, **kwargs: Any) -> None:
        luminaire_id = self._luminaire_data.get("id")
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness or 255)
        if brightness == 0: brightness_percent = 0
        else: brightness_percent = round(((brightness - 1) / 254) * 99 + 1)
        await self._api.set_luminaire_level(luminaire_id, brightness_percent)
        if ATTR_COLOR_TEMP in kwargs:
            await self.async_set_color_temp(kwargs[ATTR_COLOR_TEMP])

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.set_luminaire_level(self._luminaire_data.get("id"), 0)

    async def async_set_color_temp(self, color_temp_mired: int) -> None:
        await self._api.set_luminaire_temperature(self._luminaire_data.get("id"), color_temp_mired)

    @callback
    def update_state_from_mqtt(self, payload: Dict[str, Any]) -> None:
        """Update the light's state from an MQTT message."""
        _LOGGER.debug("Updating state for %s with payload: %s", self.unique_id, payload)
        self._luminaire_data.update(payload)
        
        self._attr_is_on = payload.get("on", self._attr_is_on)
        
        if "dimming" in payload:
            dali_value = payload["dimming"]
            if dali_value == 0:
                self._attr_brightness = 0
            else:
                power_val = ((dali_value - 1) * 3) / 253.0
                percent = math.ceil(10 ** power_val) / 10.0
                self._attr_brightness = round((percent / 100) * 255)

        self._attr_color_temp = payload.get("lightTemperature", self._attr_color_temp)
        self._luminaire_data["status"] = payload.get("status", self._luminaire_data.get("status"))

        self.async_write_ha_state()