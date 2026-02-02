"""Cover platform for InelNET integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    CONF_DEVICES,
    CONF_CHANNEL,
    CONF_NAME,
    CONF_TRAVEL_TIME,
    CONF_FACADE,
    CONF_FLOOR,
    CONF_SHADED,
    DEFAULT_TRAVEL_TIME,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up InelNET covers based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    devices = data["devices"]

    entities = []
    for device in devices:
        entities.append(
            InelNetCover(
                client=client,
                channel=device[CONF_CHANNEL],
                name=device[CONF_NAME],
                travel_time=device.get(CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME),
                facade=device.get(CONF_FACADE),
                floor=device.get(CONF_FLOOR),
                shaded=device.get(CONF_SHADED, False),
                entry_id=entry.entry_id,
            )
        )

    async_add_entities(entities)


class InelNetCover(CoverEntity):
    """Representation of an InelNET blind/cover."""

    _attr_device_class = CoverDeviceClass.BLIND
    _attr_has_entity_name = True

    def __init__(
        self,
        client,
        channel: int,
        name: str,
        travel_time: int,
        facade: str | None,
        floor: str | None,
        shaded: bool,
        entry_id: str,
    ) -> None:
        """Initialize the cover."""
        self._client = client
        self._channel = channel
        self._attr_name = name
        self._travel_time = travel_time
        self._facade = facade
        self._floor = floor
        self._shaded = shaded
        self._entry_id = entry_id

        # State tracking (estimated position since InelNET has no feedback)
        self._position: int = 50  # Start at 50% (unknown)
        self._is_moving: bool = False
        self._move_start_time: datetime | None = None
        self._move_start_position: int = 50
        self._move_direction: str | None = None  # 'up' or 'down'
        self._move_target: int | None = None

        # Unique ID
        self._attr_unique_id = f"inelnet_{entry_id}_{channel}"

        # Supported features
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover (0-100, 100 is fully open)."""
        if self._is_moving:
            return self._calculate_current_position()
        return self._position

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        return self._position <= 2

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        return self._is_moving and self._move_direction == "up"

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        return self._is_moving and self._move_direction == "down"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "channel": self._channel,
            "travel_time": self._travel_time,
            "facade": self._facade,
            "floor": self._floor,
            "shaded": self._shaded,
            "estimated_position": True,  # Indicate position is estimated
        }

    def _calculate_current_position(self) -> int:
        """Calculate current position based on movement time."""
        if not self._is_moving or not self._move_start_time:
            return self._position

        elapsed = (datetime.now() - self._move_start_time).total_seconds()
        travel_time = self._travel_time

        if self._move_target is not None:
            # Moving to specific position
            distance = abs(self._move_target - self._move_start_position)
            duration = (distance / 100) * travel_time
            progress = min(elapsed / duration, 1.0) if duration > 0 else 1.0

            if self._move_direction == "up":
                return int(self._move_start_position + (self._move_target - self._move_start_position) * progress)
            else:
                return int(self._move_start_position - (self._move_start_position - self._move_target) * progress)
        else:
            # Moving fully open or closed
            progress = min(elapsed / travel_time, 1.0)
            if self._move_direction == "up":
                return int(self._move_start_position + (100 - self._move_start_position) * progress)
            else:
                return int(self._move_start_position * (1 - progress))

    async def _start_movement(
        self, direction: str, target: int | None = None
    ) -> None:
        """Start tracking movement."""
        self._is_moving = True
        self._move_start_time = datetime.now()
        self._move_start_position = self._position
        self._move_direction = direction
        self._move_target = target

        # Schedule position updates
        self.async_write_ha_state()

        # Calculate duration
        if target is not None:
            distance = abs(target - self._position)
            duration = (distance / 100) * self._travel_time
        else:
            if direction == "up":
                distance = 100 - self._position
            else:
                distance = self._position
            duration = (distance / 100) * self._travel_time

        # Schedule movement completion
        if duration > 0:
            self.hass.loop.call_later(
                duration,
                lambda: self.hass.async_create_task(self._complete_movement())
            )

    async def _complete_movement(self) -> None:
        """Complete the movement and update position."""
        if not self._is_moving:
            return

        if self._move_target is not None:
            self._position = self._move_target
        elif self._move_direction == "up":
            self._position = 100
        else:
            self._position = 0

        self._is_moving = False
        self._move_start_time = None
        self._move_direction = None
        self._move_target = None
        self.async_write_ha_state()

    async def _stop_movement(self) -> None:
        """Stop movement and save current position."""
        if self._is_moving:
            self._position = self._calculate_current_position()
            self._is_moving = False
            self._move_start_time = None
            self._move_direction = None
            self._move_target = None
            self.async_write_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        _LOGGER.debug("Opening cover %s (channel %s)", self._attr_name, self._channel)
        await self._stop_movement()  # Stop any current movement
        if await self._client.open_cover(self._channel):
            await self._start_movement("up")

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        _LOGGER.debug("Closing cover %s (channel %s)", self._attr_name, self._channel)
        await self._stop_movement()
        if await self._client.close_cover(self._channel):
            await self._start_movement("down")

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        _LOGGER.debug("Stopping cover %s (channel %s)", self._attr_name, self._channel)
        if await self._client.stop_cover(self._channel):
            await self._stop_movement()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        _LOGGER.debug(
            "Setting cover %s (channel %s) to position %s",
            self._attr_name, self._channel, position
        )

        await self._stop_movement()

        current = self._position
        if abs(position - current) < 3:
            return  # Close enough

        direction = "up" if position > current else "down"
        duration = abs(position - current) / 100 * self._travel_time

        # Send command
        if direction == "up":
            await self._client.open_cover(self._channel)
        else:
            await self._client.close_cover(self._channel)

        await self._start_movement(direction, target=position)

        # Schedule stop command
        async def send_stop():
            await asyncio.sleep(duration)
            if self._is_moving and self._move_target == position:
                await self._client.stop_cover(self._channel)
                await self._stop_movement()
                self._position = position
                self.async_write_ha_state()

        self.hass.async_create_task(send_stop())
