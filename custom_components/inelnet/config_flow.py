"""Config flow for InelNET integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    BooleanSelector,
)

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
        self._num_devices: int = 1
        self._current_device: int = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - host configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            # Check if already configured
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            # Test connection
            if await validate_connection(self.hass, host):
                self._host = host
                return await self.async_step_devices()
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="192.168.1.66"): TextSelector(),
            }),
            errors=errors,
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device count configuration step."""
        if user_input is not None:
            self._num_devices = user_input.get("num_devices", 1)
            self._current_device = 0
            self._devices = []
            return await self.async_step_device_config()

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema({
                vol.Required("num_devices", default=1): NumberSelector(
                    NumberSelectorConfig(min=1, max=32, mode=NumberSelectorMode.BOX)
                ),
            }),
        )

    async def async_step_device_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure individual devices one by one."""
        if user_input is not None:
            # Save this device
            device = {
                CONF_CHANNEL: int(user_input[CONF_CHANNEL]),
                CONF_NAME: user_input[CONF_NAME],
                CONF_TRAVEL_TIME: int(user_input.get(CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME)),
                CONF_FACADE: user_input.get(CONF_FACADE, "S"),
                CONF_FLOOR: user_input.get(CONF_FLOOR, "parter"),
                CONF_SHADED: user_input.get(CONF_SHADED, False),
            }
            self._devices.append(device)
            self._current_device += 1

            # Check if more devices to configure
            if self._current_device < self._num_devices:
                return await self.async_step_device_config()
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
        device_num = self._current_device + 1
        return self.async_show_form(
            step_id="device_config",
            data_schema=vol.Schema({
                vol.Required(CONF_CHANNEL, default=device_num): NumberSelector(
                    NumberSelectorConfig(min=1, max=32, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_NAME, default=f"Blind {device_num}"): TextSelector(),
                vol.Required(CONF_TRAVEL_TIME, default=DEFAULT_TRAVEL_TIME): NumberSelector(
                    NumberSelectorConfig(min=5, max=120, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
                vol.Required(CONF_FACADE, default="S"): SelectSelector(
                    SelectSelectorConfig(options=FACADES, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_FLOOR, default="parter"): SelectSelector(
                    SelectSelectorConfig(options=FLOORS, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_SHADED, default=False): BooleanSelector(),
            }),
            description_placeholders={
                "device_num": str(device_num),
                "total_devices": str(self._num_devices),
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
    """Handle InelNET options - edit, add, remove devices."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._devices: list[dict] = list(config_entry.data.get(CONF_DEVICES, []))
        self._selected_device_index: int | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Main options menu."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "add_device":
                return await self.async_step_add_device()
            elif action == "edit_device":
                return await self.async_step_select_device()
            elif action == "remove_device":
                return await self.async_step_remove_device()
            elif action == "settings":
                return await self.async_step_settings()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action", default="edit_device"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": "edit_device", "label": "Edit existing device"},
                            {"value": "add_device", "label": "Add new device"},
                            {"value": "remove_device", "label": "Remove device"},
                            {"value": "settings", "label": "Connection settings"},
                        ],
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
            description_placeholders={
                "device_count": str(len(self._devices)),
            },
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a device to edit."""
        if user_input is not None:
            self._selected_device_index = int(user_input["device"])
            return await self.async_step_edit_device()

        # Build device list for selection
        device_options = [
            {
                "value": str(i),
                "label": f"Ch.{d[CONF_CHANNEL]}: {d[CONF_NAME]} ({d.get(CONF_FACADE, 'S')})"
            }
            for i, d in enumerate(self._devices)
        ]

        if not device_options:
            return self.async_abort(reason="no_devices")

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({
                vol.Required("device"): SelectSelector(
                    SelectSelectorConfig(
                        options=device_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_edit_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a specific device."""
        if self._selected_device_index is None:
            return await self.async_step_select_device()

        device = self._devices[self._selected_device_index]

        if user_input is not None:
            # Update device
            self._devices[self._selected_device_index] = {
                CONF_CHANNEL: int(user_input[CONF_CHANNEL]),
                CONF_NAME: user_input[CONF_NAME],
                CONF_TRAVEL_TIME: int(user_input[CONF_TRAVEL_TIME]),
                CONF_FACADE: user_input[CONF_FACADE],
                CONF_FLOOR: user_input[CONF_FLOOR],
                CONF_SHADED: user_input[CONF_SHADED],
            }
            return await self._save_and_finish()

        return self.async_show_form(
            step_id="edit_device",
            data_schema=vol.Schema({
                vol.Required(CONF_CHANNEL, default=device.get(CONF_CHANNEL, 1)): NumberSelector(
                    NumberSelectorConfig(min=1, max=32, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_NAME, default=device.get(CONF_NAME, "")): TextSelector(),
                vol.Required(CONF_TRAVEL_TIME, default=device.get(CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME)): NumberSelector(
                    NumberSelectorConfig(min=5, max=120, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
                vol.Required(CONF_FACADE, default=device.get(CONF_FACADE, "S")): SelectSelector(
                    SelectSelectorConfig(options=FACADES, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_FLOOR, default=device.get(CONF_FLOOR, "parter")): SelectSelector(
                    SelectSelectorConfig(options=FLOORS, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_SHADED, default=device.get(CONF_SHADED, False)): BooleanSelector(),
            }),
            description_placeholders={
                "device_name": device.get(CONF_NAME, "Unknown"),
            },
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new device."""
        if user_input is not None:
            new_device = {
                CONF_CHANNEL: int(user_input[CONF_CHANNEL]),
                CONF_NAME: user_input[CONF_NAME],
                CONF_TRAVEL_TIME: int(user_input[CONF_TRAVEL_TIME]),
                CONF_FACADE: user_input[CONF_FACADE],
                CONF_FLOOR: user_input[CONF_FLOOR],
                CONF_SHADED: user_input[CONF_SHADED],
            }
            self._devices.append(new_device)
            return await self._save_and_finish()

        # Find next available channel
        used_channels = {d[CONF_CHANNEL] for d in self._devices}
        next_channel = 1
        while next_channel in used_channels and next_channel <= 32:
            next_channel += 1

        return self.async_show_form(
            step_id="add_device",
            data_schema=vol.Schema({
                vol.Required(CONF_CHANNEL, default=next_channel): NumberSelector(
                    NumberSelectorConfig(min=1, max=32, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_NAME, default=f"Blind {len(self._devices) + 1}"): TextSelector(),
                vol.Required(CONF_TRAVEL_TIME, default=DEFAULT_TRAVEL_TIME): NumberSelector(
                    NumberSelectorConfig(min=5, max=120, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
                vol.Required(CONF_FACADE, default="S"): SelectSelector(
                    SelectSelectorConfig(options=FACADES, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_FLOOR, default="parter"): SelectSelector(
                    SelectSelectorConfig(options=FLOORS, mode=SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_SHADED, default=False): BooleanSelector(),
            }),
        )

    async def async_step_remove_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Remove a device."""
        if user_input is not None:
            index = int(user_input["device"])
            if 0 <= index < len(self._devices):
                del self._devices[index]
            return await self._save_and_finish()

        # Build device list for selection
        device_options = [
            {
                "value": str(i),
                "label": f"Ch.{d[CONF_CHANNEL]}: {d[CONF_NAME]}"
            }
            for i, d in enumerate(self._devices)
        ]

        if not device_options:
            return self.async_abort(reason="no_devices")

        return self.async_show_form(
            step_id="remove_device",
            data_schema=vol.Schema({
                vol.Required("device"): SelectSelector(
                    SelectSelectorConfig(
                        options=device_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit connection settings."""
        if user_input is not None:
            # Update host if changed
            new_data = dict(self.config_entry.data)
            new_data[CONF_HOST] = user_input[CONF_HOST]
            new_data[CONF_DEVICES] = self._devices

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
                options={
                    "retry_count": int(user_input.get("retry_count", 2)),
                    "retry_delay": float(user_input.get("retry_delay", 0.8)),
                },
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=self.config_entry.data.get(CONF_HOST, "192.168.1.66")): TextSelector(),
                vol.Required("retry_count", default=self.config_entry.options.get("retry_count", 2)): NumberSelector(
                    NumberSelectorConfig(min=1, max=5, mode=NumberSelectorMode.BOX)
                ),
                vol.Required("retry_delay", default=self.config_entry.options.get("retry_delay", 0.8)): NumberSelector(
                    NumberSelectorConfig(min=0.3, max=3.0, step=0.1, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
            }),
        )

    async def _save_and_finish(self) -> FlowResult:
        """Save devices and finish options flow."""
        new_data = dict(self.config_entry.data)
        new_data[CONF_DEVICES] = self._devices

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
        )

        # Reload integration to apply changes
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)

        return self.async_create_entry(title="", data={})
