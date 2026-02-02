"""Binary sensor platform for InelNET integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, DATA_CONNECTION_STATUS

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up InelNET binary sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]

    entities = [
        InelNetConnectivitySensor(hass, entry, client),
    ]

    async_add_entities(entities)


class InelNetConnectivitySensor(BinarySensorEntity):
    """Binary sensor indicating InelNET controller connectivity."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Connection Status"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client,
    ) -> None:
        """Initialize the connectivity sensor."""
        self.hass = hass
        self._entry = entry
        self._client = client
        self._attr_unique_id = f"inelnet_{entry.entry_id}_connected"
        self._attr_is_on = True  # Assume connected initially
        self._consecutive_failures = 0

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Check connectivity periodically
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._check_connectivity,
                SCAN_INTERVAL,
            )
        )

        # Initial check
        await self._check_connectivity()

    async def _check_connectivity(self, now=None) -> None:
        """Check if the InelNET controller is reachable."""
        try:
            is_connected = await self._client.test_connection()

            if is_connected:
                self._consecutive_failures = 0
                if not self._attr_is_on:
                    _LOGGER.info("InelNET controller is back online")
                self._attr_is_on = True
            else:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 3:
                    if self._attr_is_on:
                        _LOGGER.warning("InelNET controller appears offline")
                    self._attr_is_on = False

            # Store connection status for other components
            if DOMAIN in self.hass.data and self._entry.entry_id in self.hass.data[DOMAIN]:
                self.hass.data[DOMAIN][self._entry.entry_id][DATA_CONNECTION_STATUS] = self._attr_is_on

            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.debug("Connectivity check error: %s", err)
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self._attr_is_on = False
                self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        return {
            "host": data.get("host", "unknown"),
            "consecutive_failures": self._consecutive_failures,
        }
