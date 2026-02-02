"""Sensor platform for InelNET integration."""
from __future__ import annotations

import logging
import math
from datetime import datetime, date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

from .const import (
    DOMAIN,
    FACADES,
    FACADE_ANGLES,
    CONF_ENABLE_SENSORS,
    DATA_STATISTICS,
)

_LOGGER = logging.getLogger(__name__)

SUN_ENTITY = "sun.sun"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up InelNET sensors based on a config entry."""
    # Check if sensors are enabled
    if not entry.options.get(CONF_ENABLE_SENSORS, True):
        return

    entities: list[SensorEntity] = []

    # Create solar exposure sensors for each facade
    for facade in FACADES:
        entities.append(InelNetSolarExposureSensor(hass, entry, facade))

    # Create energy savings sensor
    entities.append(InelNetEnergySavingsSensor(hass, entry))

    # Create operational statistics sensors
    entities.append(InelNetCommandsCountSensor(hass, entry))
    entities.append(InelNetRuntimeSensor(hass, entry))

    async_add_entities(entities)


class InelNetSolarExposureSensor(SensorEntity):
    """Sensor that calculates solar exposure for a facade."""

    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        facade: str,
    ) -> None:
        """Initialize the solar exposure sensor."""
        self.hass = hass
        self._entry = entry
        self._facade = facade
        self._facade_angle = FACADE_ANGLES[facade]
        self._attr_name = f"Solar Exposure {facade}"
        self._attr_unique_id = f"inelnet_{entry.entry_id}_solar_{facade.lower()}"
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Track sun state changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [SUN_ENTITY],
                self._handle_sun_state_change,
            )
        )

        # Initial calculation
        self._calculate_exposure()

    @callback
    def _handle_sun_state_change(self, event) -> None:
        """Handle sun state changes."""
        self._calculate_exposure()
        self.async_write_ha_state()

    def _calculate_exposure(self) -> None:
        """Calculate solar exposure percentage for this facade."""
        sun_state = self.hass.states.get(SUN_ENTITY)
        if sun_state is None:
            self._attr_native_value = 0
            return

        azimuth = sun_state.attributes.get("azimuth", 0)
        elevation = sun_state.attributes.get("elevation", 0)

        # No exposure at night
        if elevation <= 0:
            self._attr_native_value = 0
            return

        # Calculate angle difference between sun azimuth and facade direction
        angle_diff = abs(azimuth - self._facade_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        # Maximum exposure when sun is perpendicular to facade (angle_diff = 0)
        # Zero exposure when sun is parallel to facade (angle_diff = 90)
        if angle_diff >= 90:
            self._attr_native_value = 0
            return

        # Calculate base exposure (100% when perpendicular, 0% at 90 degrees)
        base_exposure = max(0, 100 - (angle_diff / 90 * 100))

        # Adjust for sun elevation (higher sun = more direct light)
        # Maximum effect at 45 degrees elevation
        elevation_factor = min(1.0, elevation / 45)

        # Final exposure value
        self._attr_native_value = round(base_exposure * elevation_factor)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        sun_state = self.hass.states.get(SUN_ENTITY)
        attrs = {
            "facade": self._facade,
            "facade_angle": self._facade_angle,
        }
        if sun_state:
            attrs["sun_azimuth"] = sun_state.attributes.get("azimuth", 0)
            attrs["sun_elevation"] = sun_state.attributes.get("elevation", 0)
        return attrs


class InelNetEnergySavingsSensor(SensorEntity):
    """Sensor that estimates energy savings from blind usage."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_has_entity_name = True
    _attr_name = "Energy Savings Today"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the energy savings sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"inelnet_{entry.entry_id}_energy_savings"
        self._attr_native_value = 0.0
        self._last_calculation = None
        self._today = date.today()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Update every 15 minutes
        from datetime import timedelta
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._update_savings,
                timedelta(minutes=15),
            )
        )

    @callback
    def _update_savings(self, now=None) -> None:
        """Update energy savings estimation."""
        # Reset daily
        current_date = date.today()
        if current_date != self._today:
            self._today = current_date
            self._attr_native_value = 0.0

        # Get all InelNET covers
        covers = []
        for state in self.hass.states.async_all("cover"):
            if state.entity_id.startswith("cover.inelnet_") or "inelnet" in state.attributes.get("integration", ""):
                covers.append(state)

        if not covers:
            return

        # Calculate potential savings based on:
        # - Closed/partially closed blinds
        # - Solar exposure on their facades
        # - Time of day
        savings_increment = 0.0

        for cover in covers:
            position = cover.attributes.get("current_cover_position", 50)
            facade = cover.attributes.get("facade", "S")

            # Get solar exposure for this facade
            exposure_entity = f"sensor.inelnet_{self._entry.entry_id}_solar_{facade.lower()}"
            exposure_state = self.hass.states.get(exposure_entity)

            if exposure_state:
                try:
                    exposure = float(exposure_state.state)
                except (ValueError, TypeError):
                    exposure = 0

                # More savings when blinds are closed and sun is strong
                closure_factor = (100 - position) / 100  # 0 when open, 1 when closed
                exposure_factor = exposure / 100

                # Estimate: 0.1 kWh per 15 min per blind at max exposure and closed
                savings_increment += 0.1 * closure_factor * exposure_factor

        self._attr_native_value = round(self._attr_native_value + savings_increment, 2)
        self.async_write_ha_state()


class InelNetCommandsCountSensor(SensorEntity):
    """Sensor that counts commands sent today."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_has_entity_name = True
    _attr_name = "Commands Today"
    _attr_icon = "mdi:counter"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the commands count sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"inelnet_{entry.entry_id}_commands_today"
        self._attr_native_value = 0
        self._today = date.today()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Initialize statistics storage
        if DOMAIN not in self.hass.data:
            self.hass.data[DOMAIN] = {}
        if self._entry.entry_id not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][self._entry.entry_id] = {}

        self.hass.data[DOMAIN][self._entry.entry_id][DATA_STATISTICS] = {
            "commands_today": 0,
            "runtime_today": 0.0,
            "last_reset": date.today(),
        }

    def increment_commands(self) -> None:
        """Increment the command counter."""
        current_date = date.today()
        if current_date != self._today:
            self._today = current_date
            self._attr_native_value = 0

        self._attr_native_value += 1
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "date": str(self._today),
        }


class InelNetRuntimeSensor(SensorEntity):
    """Sensor that tracks total runtime today."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_has_entity_name = True
    _attr_name = "Runtime Today"
    _attr_icon = "mdi:timer"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the runtime sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"inelnet_{entry.entry_id}_runtime_today"
        self._attr_native_value = 0.0
        self._today = date.today()

    def add_runtime(self, seconds: float) -> None:
        """Add runtime in seconds."""
        current_date = date.today()
        if current_date != self._today:
            self._today = current_date
            self._attr_native_value = 0.0

        self._attr_native_value = round(self._attr_native_value + (seconds / 60), 1)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "date": str(self._today),
        }
