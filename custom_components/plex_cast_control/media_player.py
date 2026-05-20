"""Plex Cast Control proxy media player."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_SOURCE_ENTITY,
    DOMAIN,
    PLEX_CAST_APP_ID,
    PLEX_CAST_APP_NAME,
    SERVICE_NEXT,
    SERVICE_PREVIOUS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Plex Cast Control proxy media player from config entry."""
    source_entity = entry.data[CONF_SOURCE_ENTITY]

    async_add_entities(
        [
            PlexCastControlProxy(
                hass=hass,
                name=entry.title,
                source_entity=source_entity,
                unique_id=entry.entry_id,
            )
        ]
    )


class PlexCastControlProxy(MediaPlayerEntity):
    """Proxy media player that adds Plex Cast next/previous support."""

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        source_entity: str,
        unique_id: str,
    ) -> None:
        """Initialize proxy."""
        self.hass = hass
        self._attr_name = name
        self._attr_unique_id = f"plex_cast_control_{unique_id}"
        self._source_entity = source_entity
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to source entity changes."""

        @callback
        def _source_changed(event) -> None:
            self.async_write_ha_state()

        self._remove_listener = async_track_state_change_event(
            self.hass,
            [self._source_entity],
            _source_changed,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from source entity changes."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    @property
    def source_state(self):
        """Return source entity state."""
        return self.hass.states.get(self._source_entity)

    def _is_plex_cast(self) -> bool:
        """Return whether the source entity is currently running Plex Cast."""
        state = self.source_state

        if state is None:
            return False

        return (
            state.attributes.get("app_id") == PLEX_CAST_APP_ID
            or state.attributes.get("app_name") == PLEX_CAST_APP_NAME
        )

    @property
    def available(self) -> bool:
        """Return whether source entity is available."""
        state = self.source_state
        return state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)

    @property
    def state(self) -> str | None:
        """Mirror source entity state."""
        state = self.source_state
        if state is None:
            return STATE_UNAVAILABLE
        return state.state

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Mirror source features and add Plex next/previous only while Plex is active."""
        state = self.source_state

        source_features = 0
        if state is not None:
            source_features = int(state.attributes.get("supported_features", 0))

        features = source_features

        if self._is_plex_cast():
            features |= MediaPlayerEntityFeature.NEXT_TRACK
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK

        return MediaPlayerEntityFeature(features)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Mirror source media attributes."""
        state = self.source_state

        if state is None:
            return {
                "source_entity": self._source_entity,
                "plex_cast_control_proxy": True,
                "plex_cast_active": False,
            }

        attrs = dict(state.attributes)
        attrs["source_entity"] = self._source_entity
        attrs["plex_cast_control_proxy"] = True
        attrs["plex_cast_active"] = self._is_plex_cast()

        return attrs

    async def _call_source_media_service(
        self,
        service: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Call a standard media_player service on the source entity."""
        service_data = {ATTR_ENTITY_ID: self._source_entity}

        if data:
            service_data.update(data)

        await self.hass.services.async_call(
            "media_player",
            service,
            service_data,
            blocking=True,
        )

    async def async_media_next_track(self) -> None:
        """Send next command."""
        if self._is_plex_cast():
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_NEXT,
                {ATTR_ENTITY_ID: self._source_entity},
                blocking=True,
            )
            return

        await self._call_source_media_service("media_next_track")

    async def async_media_previous_track(self) -> None:
        """Send previous command."""
        if self._is_plex_cast():
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_PREVIOUS,
                {ATTR_ENTITY_ID: self._source_entity},
                blocking=True,
            )
            return

        await self._call_source_media_service("media_previous_track")

    async def async_media_play_pause(self) -> None:
        """Toggle play/pause on source entity."""
        await self._call_source_media_service("media_play_pause")

    async def async_media_play(self) -> None:
        """Play source entity."""
        await self._call_source_media_service("media_play")

    async def async_media_pause(self) -> None:
        """Pause source entity."""
        await self._call_source_media_service("media_pause")

    async def async_media_stop(self) -> None:
        """Stop source entity."""
        await self._call_source_media_service("media_stop")

    async def async_set_volume_level(self, volume: float) -> None:
        """Set source volume."""
        await self._call_source_media_service(
            "volume_set",
            {"volume_level": volume},
        )

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute source volume."""
        await self._call_source_media_service(
            "volume_mute",
            {"is_volume_muted": mute},
        )

    async def async_media_seek(self, position: float) -> None:
        """Seek source media."""
        await self._call_source_media_service(
            "media_seek",
            {"seek_position": position},
        )
