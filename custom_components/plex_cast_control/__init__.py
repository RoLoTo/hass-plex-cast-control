"""Plex Cast Control custom integration."""

from __future__ import annotations

import logging
import time

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    PREVIOUS_DOUBLE_PRESS_DELAY_SECONDS,
    PREVIOUS_RESTART_THRESHOLD_SECONDS,
    SERVICE_NEXT,
    SERVICE_PREVIOUS,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_ENTITY_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    }
)


def _get_cast_name_from_entity(hass: HomeAssistant, entity_id: str) -> str:
    """Resolve HA media_player entity_id to Chromecast friendly name."""
    state = hass.states.get(entity_id)

    if state is None:
        raise ValueError(f"Entity not found: {entity_id}")

    cast_name = state.attributes.get("friendly_name")

    if not cast_name:
        raise ValueError(f"Entity has no friendly_name: {entity_id}")

    return cast_name


def _get_plex_controller_sync(cast_name: str):
    """Find Chromecast by friendly name and return Plex controller plus browser."""
    import pychromecast
    from pychromecast.controllers.plex import PlexController

    chromecasts, browser = pychromecast.get_listed_chromecasts(
        friendly_names=[cast_name],
        timeout=5,
    )

    if not chromecasts:
        browser.stop_discovery()
        raise RuntimeError(f"Cast device not found: {cast_name}")

    cast = chromecasts[0]
    cast.wait()

    plex = PlexController()
    cast.register_handler(plex)
    plex.update_status()

    return plex, browser


def _plex_next_sync(cast_name: str) -> None:
    """Send Plex next command using the Plex Cast namespace."""
    plex, browser = _get_plex_controller_sync(cast_name)

    try:
        plex.next()
    finally:
        browser.stop_discovery()


def _plex_previous_sync(cast_name: str) -> None:
    """Send Plex previous command using the Plex Cast namespace."""
    plex, browser = _get_plex_controller_sync(cast_name)

    try:
        plex.update_status()
        time.sleep(0.3)

        position = getattr(plex.status, "adjusted_current_time", None)

        if callable(position):
            position = position()

        if position is None:
            position = getattr(plex.status, "current_time", None) or 0

        _LOGGER.info("Plex Cast position before previous: %s", position)

        plex.previous()

        if position > PREVIOUS_RESTART_THRESHOLD_SECONDS:
            time.sleep(PREVIOUS_DOUBLE_PRESS_DELAY_SECONDS)
            plex.previous()

    finally:
        browser.stop_discovery()


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Plex Cast Control services."""

    async def handle_next(call: ServiceCall) -> None:
        entity_ids = call.data.get(ATTR_ENTITY_ID)

        if not entity_ids:
            raise ValueError("entity_id is required")

        entity_id = entity_ids[0]
        cast_name = _get_cast_name_from_entity(hass, entity_id)

        _LOGGER.info("Sending Plex Cast next command to %s from %s", cast_name, entity_id)

        await hass.async_add_executor_job(_plex_next_sync, cast_name)

    async def handle_previous(call: ServiceCall) -> None:
        entity_ids = call.data.get(ATTR_ENTITY_ID)

        if not entity_ids:
            raise ValueError("entity_id is required")

        entity_id = entity_ids[0]
        cast_name = _get_cast_name_from_entity(hass, entity_id)

        _LOGGER.info(
            "Sending Plex Cast previous command to %s from %s",
            cast_name,
            entity_id,
        )

        await hass.async_add_executor_job(_plex_previous_sync, cast_name)

    hass.services.async_register(
        DOMAIN,
        SERVICE_NEXT,
        handle_next,
        schema=SERVICE_ENTITY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_PREVIOUS,
        handle_previous,
        schema=SERVICE_ENTITY_SCHEMA,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Plex Cast Control from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Plex Cast Control config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
