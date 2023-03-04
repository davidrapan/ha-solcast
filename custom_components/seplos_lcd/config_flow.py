"""Config flow for Seplos LCD integration."""
from __future__ import annotations

from typing import Any
import logging
import traceback

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONST_USB_ADDRESS

_LOGGER = logging.getLogger(__name__)


class SeplosFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Seplos."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SeplosOptionFlowHandler:
        """Get the options flow for this handler."""
        try:
            return SeplosOptionFlowHandler(config_entry)
        except Exception:
            _LOGGER.error("async_get_options_flow: %s", traceback.format_exc())


    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        try:
            if user_input is not None:
                return self.async_create_entry(
                    title= "Seplos LCD Communtion", 
                    data = {},
                    options={
                        CONST_USB_ADDRESS: user_input[CONST_USB_ADDRESS],
                    },
                )

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONST_USB_ADDRESS, default=""): str,
                    }
                ),
            )
        except Exception:
            _LOGGER.error("async_step_user: %s", traceback.format_exc())


class SeplosOptionFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        try:
            self.config_entry = config_entry
        except Exception:
            _LOGGER.error("__init__: %s", traceback.format_exc())

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        try:
            if user_input is not None:
                return self.async_create_entry(title="Seplos LCD", data=user_input)

            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONST_USB_ADDRESS,
                            default=self.config_entry.options.get(CONST_USB_ADDRESS),
                        ): str,
                    }
                ),
            )
        except Exception:
            _LOGGER.error("async_step_init: %s", traceback.format_exc())
