import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_PATH, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_START = "start"
CONF_END = "end"
CONF_SIZE = "size"
CONF_PERIODS = "periods"

PERIOD_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_START): cv.positive_int,
        vol.Required(CONF_END): cv.positive_int,
        vol.Required(CONF_SIZE): cv.positive_int,
    }
)

CONF_PERIOD = "period"


class TibberLowestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Tibber Lowest config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # try:
            #     await validate_period(user_input[CONF_PERIOD], self.hass)
            # except ValueError:
            #     errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input
                # Return the form of the next step.
                return self.async_create_entry(title="Tibber Lowest", data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=PERIOD_SCHEMA, errors=errors
        )
