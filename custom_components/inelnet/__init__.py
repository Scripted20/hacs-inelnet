"""InelNET Blinds Control integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_HOST, CONF_DEVICES, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.COVER]


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


async def async_register_services(hass: HomeAssistant) -> None:
    """Register InelNET services."""

    async def handle_send_command(call):
        """Handle the send_command service call."""
        channel = call.data.get("channel")
        action = call.data.get("action")

        for entry_id, data in hass.data[DOMAIN].items():
            client = data["client"]
            await client.send_command(channel, action)

    hass.services.async_register(DOMAIN, "send_command", handle_send_command)


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
