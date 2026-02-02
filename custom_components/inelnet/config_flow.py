"""Config flow for InelNET integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_DEVICES,
    CONF_CHANNEL,
    CONF_TRAVEL_TIME,
    CONF_FACADE,
    CONF_FLOOR,
    CONF_SHADED,
    DEFAULT_TRAVEL_TIME,
    FACADES,
    FLOORS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, host: str) -> bool:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"http://{host}", timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


class InelNetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for InelNET."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._devices: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - host configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            # Test connection
            if await validate_connection(self.hass, host):
                self._host = host
                return await self.async_step_devices()
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="192.168.1.66"): str,
            }),
            errors=errors,
            description_placeholders={
                "default_ip": "192.168.1.66",
            },
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            num_devices = user_input.get("num_devices", 1)
            return await self.async_step_device_config(device_index=0, total=num_devices)

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema({
                vol.Required("num_devices", default=16): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=32)
                ),
            }),
            errors=errors,
        )

    async def async_step_device_config(
        self,
        user_input: dict[str, Any] | None = None,
        device_index: int = 0,
        total: int = 1,
    ) -> FlowResult:
        """Configure individual devices."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Save this device
            device = {
                CONF_CHANNEL: user_input[CONF_CHANNEL],
                CONF_NAME: user_input[CONF_NAME],
                CONF_TRAVEL_TIME: user_input.get(CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME),
                CONF_FACADE: user_input.get(CONF_FACADE, "S"),
                CONF_FLOOR: user_input.get(CONF_FLOOR, "parter"),
                CONF_SHADED: user_input.get(CONF_SHADED, False),
            }
            self._devices.append(device)

            # Check if more devices to configure
            if device_index + 1 < total:
                return await self.async_step_device_config(
                    device_index=device_index + 1,
                    total=total,
                )
            else:
                # All devices configured, create entry
                return self.async_create_entry(
                    title=f"InelNET ({self._host})",
                    data={
                        CONF_HOST: self._host,
                        CONF_DEVICES: self._devices,
                    },
                )

        # Show form for this device
        return self.async_show_form(
            step_id="device_config",
            data_schema=vol.Schema({
                vol.Required(CONF_CHANNEL, default=device_index + 1): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=32)
                ),
                vol.Required(CONF_NAME, default=f"Jaluzeaua {device_index + 1}"): str,
                vol.Optional(CONF_TRAVEL_TIME, default=DEFAULT_TRAVEL_TIME): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=120)
                ),
                vol.Optional(CONF_FACADE, default="S"): vol.In(FACADES),
                vol.Optional(CONF_FLOOR, default="parter"): vol.In(FLOORS),
                vol.Optional(CONF_SHADED, default=False): bool,
            }),
            errors=errors,
            description_placeholders={
                "device_num": str(device_index + 1),
                "total_devices": str(total),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return InelNetOptionsFlow(config_entry)


class InelNetOptionsFlow(config_entries.OptionsFlow):
    """Handle InelNET options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "retry_count",
                    default=self.config_entry.options.get("retry_count", 2),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
                vol.Optional(
                    "retry_delay",
                    default=self.config_entry.options.get("retry_delay", 0.8),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.3, max=3.0)),
            }),
        )
