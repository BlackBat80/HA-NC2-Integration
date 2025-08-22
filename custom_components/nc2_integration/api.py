import asyncio
import logging
from typing import Any, Dict, List

import aiohttp

from .const import (
    API_LOGIN,
    API_RELAY_CONTROL,
    API_LUMINAIRES_DIM,
    API_LUMINAIRES_COLOR_TEMP,
    API_DEVICES_LIST,
)

_LOGGER = logging.getLogger(__name__)


class NC2ApiClient:
    """API Client for the NC2 Controller."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ):
        """Initialize the API client."""
        self._host = host
        self._username = username
        self._password = password
        self._session = session
        self._token = None
        self.devices: List[Dict[str, Any]] = []

    async def _request(
        self, method: str, path: str, data: Dict[str, Any] | None = None
    ) -> Dict[str, Any] | None:
        """Make an API request."""
        url = f"http://{self._host}{path}"
        headers = {
            "Content-Type": "application/json",
            "accept": "*/*",
        }
        if self._token:
            headers["Authorization"] = self._token

        _LOGGER.debug("Request: %s %s, data=%s", method, url, data)
        async with self._session.request(method, url, json=data, headers=headers) as resp:
            resp.raise_for_status()

            if resp.content_type == "application/json":
                response_data = await resp.json()
                _LOGGER.debug("Response: %s", response_data)
                return response_data
            
            return None

    async def authenticate(self) -> None:
        """Authenticate and get the token."""
        _LOGGER.info("Authenticating with NC2 Controller at %s", self._host)
        try:
            payload = {"login": self._username, "password": self._password}
            response = await self._request("post", API_LOGIN, payload)
            self._token = response.get("token")
            if not self._token:
                raise Exception("Authentication failed: No token received.")
            _LOGGER.info("Authentication successful.")
        except Exception as ex:
            _LOGGER.error("Authentication failed: %s", ex)
            raise

    

    async def control_relay(self, relay_id: int, turn_on: bool) -> None:
        """Control a relay."""
        path = API_RELAY_CONTROL.format(relay_id=relay_id)
        payload = {"on": turn_on}
        await self._request("post", path, payload)

    async def get_relays_status(self, module_id: int = 1) -> list[dict[str, any]]:
        """Get the status of all relays on a module."""
        path = f"/api/v1/modules/relay/{module_id}"
        try:
            response = await self._request("get", path)
            return response.get("relays", [])
        except Exception as ex:
            _LOGGER.error("Failed to get relays status: %s", ex)
            return []

    async def set_luminaire_level(self, luminaire_id: int, brightness: int) -> None:
        """Set the brightness level of a luminaire."""
        path = API_LUMINAIRES_DIM.format(luminaire_id=luminaire_id)
        payload = {"lvl": brightness}
        await self._request("post", path, payload)

    async def set_luminaire_temperature(self, luminaire_id: int, temperature_mireds: int) -> None:
        """Set the color temperature of a luminaire."""
        path = API_LUMINAIRES_COLOR_TEMP.format(luminaire_id=luminaire_id)
        # Convert mireds to Kelvin
        temperature_kelvin = round(1_000_000 / temperature_mireds)
        payload = {
            "lightTemperature": temperature_kelvin,
            "colorType": "LIGHT_TEMPERATURE",
            "async": True,
        }
        await self._request("post", path, payload)

    async def get_luminaires(self) -> list[dict[str, any]]:
        """Get a list of all luminaires from all buses."""
        all_luminaires = []
        for bus_id in range(1, 4):  # Buses 1, 2, 3
            path = f"/api/v1/buses/{bus_id}/luminaires"
            try:
                # I am assuming the response from this endpoint is a list of luminaire objects.
                # If the structure is different, we may need to adjust this.
                response = await self._request("get", path)
                if isinstance(response, list):
                    all_luminaires.extend(response)
            except Exception as ex:
                _LOGGER.error("Failed to get luminaires from bus %d: %s", bus_id, ex)
        return all_luminaires
