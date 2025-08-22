import logging
import voluptuous as vol
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from .api import NC2ApiClient

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD, default="admin"): str,
    }
)

async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> None:
    """Validate the user input allows us to connect."""
    session = aiohttp_client.async_get_clientsession(hass)
    client = NC2ApiClient(
        host=data[CONF_HOST],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        session=session,
    )
    await client.authenticate()


class NC2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NC2 Controller."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except Exception:
                _LOGGER.exception("Failed to connect to NC2 controller")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
