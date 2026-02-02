"""InelNET Blinds Control integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import asyncio
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_DEVICES,
    CONF_FACADE,
    CONF_FLOOR,
    DEFAULT_TIMEOUT,
    FACADES,
    FLOORS,
    SERVICE_OPEN_FACADE,
    SERVICE_CLOSE_FACADE,
    SERVICE_OPEN_FLOOR,
    SERVICE_CLOSE_FLOOR,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.COVER, Platform.SENSOR, Platform.BINARY_SENSOR]

# Service schemas
SERVICE_FACADE_SCHEMA = vol.Schema({
    vol.Required("facade"): vol.In(FACADES),
    vol.Optional("position", default=None): vol.Any(None, vol.All(vol.Coerce(int), vol.Range(min=0, max=100))),
})

SERVICE_FLOOR_SCHEMA = vol.Schema({
    vol.Required("floor"): vol.In(FLOORS),
    vol.Optional("position", default=None): vol.Any(None, vol.All(vol.Coerce(int), vol.Range(min=0, max=100))),
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up InelNET from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    devices = entry.data.get(CONF_DEVICES, [])

    # Create the InelNET API client
    session = async_get_clientsession(hass)
    client = InelNetClient(session, host)

    # Test connection
    if not await client.test_connection():
        _LOGGER.error("Cannot connect to InelNET at %s", host)
        return False

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "devices": devices,
        "host": host,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def get_covers_by_attribute(hass: HomeAssistant, attribute: str, value: str) -> list:
    """Get all InelNET cover entities matching an attribute value."""
    matching_covers = []
    for state in hass.states.async_all("cover"):
        if not state.entity_id.startswith("cover.inelnet_"):
            continue
        if state.attributes.get(attribute) == value:
            matching_covers.append(state.entity_id)
    return matching_covers


async def async_register_services(hass: HomeAssistant) -> None:
    """Register InelNET services."""

    async def handle_send_command(call: ServiceCall) -> None:
        """Handle the send_command service call."""
        channel = call.data.get("channel")
        action = call.data.get("action")

        for entry_id, data in hass.data[DOMAIN].items():
            if isinstance(data, dict) and "client" in data:
                client = data["client"]
                await client.send_command(channel, action)

    async def handle_open_facade(call: ServiceCall) -> None:
        """Handle open_facade service call."""
        facade = call.data.get("facade")
        covers = get_covers_by_attribute(hass, "facade", facade)

        _LOGGER.debug("Opening facade %s: %s covers found", facade, len(covers))

        for entity_id in covers:
            await hass.services.async_call(
                "cover",
                "open_cover",
                {"entity_id": entity_id},
                blocking=False,
            )

    async def handle_close_facade(call: ServiceCall) -> None:
        """Handle close_facade service call."""
        facade = call.data.get("facade")
        position = call.data.get("position")
        covers = get_covers_by_attribute(hass, "facade", facade)

        _LOGGER.debug("Closing facade %s to position %s: %s covers found", facade, position, len(covers))

        for entity_id in covers:
            if position is not None:
                await hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": position},
                    blocking=False,
                )
            else:
                await hass.services.async_call(
                    "cover",
                    "close_cover",
                    {"entity_id": entity_id},
                    blocking=False,
                )

    async def handle_open_floor(call: ServiceCall) -> None:
        """Handle open_floor service call."""
        floor = call.data.get("floor")
        covers = get_covers_by_attribute(hass, "floor", floor)

        _LOGGER.debug("Opening floor %s: %s covers found", floor, len(covers))

        for entity_id in covers:
            await hass.services.async_call(
                "cover",
                "open_cover",
                {"entity_id": entity_id},
                blocking=False,
            )

    async def handle_close_floor(call: ServiceCall) -> None:
        """Handle close_floor service call."""
        floor = call.data.get("floor")
        position = call.data.get("position")
        covers = get_covers_by_attribute(hass, "floor", floor)

        _LOGGER.debug("Closing floor %s to position %s: %s covers found", floor, position, len(covers))

        for entity_id in covers:
            if position is not None:
                await hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": entity_id, "position": position},
                    blocking=False,
                )
            else:
                await hass.services.async_call(
                    "cover",
                    "close_cover",
                    {"entity_id": entity_id},
                    blocking=False,
                )

    # Register all services
    if not hass.services.has_service(DOMAIN, "send_command"):
        hass.services.async_register(DOMAIN, "send_command", handle_send_command)

    if not hass.services.has_service(DOMAIN, SERVICE_OPEN_FACADE):
        hass.services.async_register(
            DOMAIN, SERVICE_OPEN_FACADE, handle_open_facade, schema=SERVICE_FACADE_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLOSE_FACADE):
        hass.services.async_register(
            DOMAIN, SERVICE_CLOSE_FACADE, handle_close_facade, schema=SERVICE_FACADE_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_OPEN_FLOOR):
        hass.services.async_register(
            DOMAIN, SERVICE_OPEN_FLOOR, handle_open_floor, schema=SERVICE_FLOOR_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLOSE_FLOOR):
        hass.services.async_register(
            DOMAIN, SERVICE_CLOSE_FLOOR, handle_close_floor, schema=SERVICE_FLOOR_SCHEMA
        )


class InelNetClient:
    """Client for communicating with InelNET controller."""

    # Action codes
    ACTION_UP = 160
    ACTION_UP_SHORT = 176
    ACTION_STOP = 144
    ACTION_DOWN = 192
    ACTION_DOWN_SHORT = 208

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        """Initialize the client."""
        self._session = session
        self._host = host
        self._base_url = f"http://{host}"

    async def test_connection(self) -> bool:
        """Test if we can connect to the InelNET controller."""
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with self._session.get(self._base_url) as response:
                    return response.status == 200
        except Exception as err:
            _LOGGER.debug("Connection test failed: %s", err)
            return False

    async def send_command(
        self,
        channel: int | str,
        action: int,
        retries: int = 2,
        retry_delay: float = 0.8
    ) -> bool:
        """Send a command to the InelNET controller."""
        url = f"{self._base_url}/msg.htm"
        data = f"send_ch={channel}&send_act={action}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        for attempt in range(retries):
            try:
                async with asyncio.timeout(DEFAULT_TIMEOUT):
                    async with self._session.post(
                        url,
                        data=data,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            _LOGGER.debug(
                                "Command sent: channel=%s, action=%s",
                                channel, action
                            )
                            if attempt < retries - 1:
                                await asyncio.sleep(retry_delay)
                            return True
            except Exception as err:
                _LOGGER.warning(
                    "Command failed (attempt %d/%d): %s",
                    attempt + 1, retries, err
                )
                if attempt < retries - 1:
                    await asyncio.sleep(retry_delay)

        return False

    async def open_cover(self, channel: int | str) -> bool:
        """Open a cover (send UP command)."""
        return await self.send_command(channel, self.ACTION_UP)

    async def close_cover(self, channel: int | str) -> bool:
        """Close a cover (send DOWN command)."""
        return await self.send_command(channel, self.ACTION_DOWN)

    async def stop_cover(self, channel: int | str) -> bool:
        """Stop a cover."""
        return await self.send_command(channel, self.ACTION_STOP)

    async def open_cover_short(self, channel: int | str) -> bool:
        """Short open movement."""
        return await self.send_command(channel, self.ACTION_UP_SHORT)

    async def close_cover_short(self, channel: int | str) -> bool:
        """Short close movement."""
        return await self.send_command(channel, self.ACTION_DOWN_SHORT)
