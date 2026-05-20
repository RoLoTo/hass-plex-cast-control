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
    async_add_entities(
        [
            PlexCastControlProxy(
                hass=hass,
                name=entry.title,
                source_entity=entry.data[CONF_SOURCE_ENTITY],
                unique_id=entry.entry_id,
            )
        ]
    )


class PlexCastControlProxy(MediaPlayerEntity):
    """Proxy media player that overrides Plex Cast next/previous only."""

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

    # ---------------------------------------------------------------------
    # Source state helpers
    # ---------------------------------------------------------------------

    @property
    def source_state(self):
        """Return source entity state."""
        return self.hass.states.get(self._source_entity)

    def _source_attr(self, attr_name: str, default: Any = None) -> Any:
        """Return source entity attribute."""
        state = self.source_state
        if state is None:
            return default
        return state.attributes.get(attr_name, default)

    def _source_features(self) -> int:
        """Return source supported features as int."""
        return int(self._source_attr("supported_features", 0))

    def _source_supports(self, feature: MediaPlayerEntityFeature) -> bool:
        """Return whether source supports a media player feature."""
        return bool(self._source_features() & feature)

    def _is_plex_cast(self) -> bool:
        """Return whether the source entity is currently running Plex Cast."""
        return (
            self._source_attr("app_id") == PLEX_CAST_APP_ID
            or self._source_attr("app_name") == PLEX_CAST_APP_NAME
        )

    async def _delegate(self, service: str, **data: Any) -> None:
        """Delegate a media_player service call to the source entity."""
        service_data = {ATTR_ENTITY_ID: self._source_entity}
        service_data.update(data)

        await self.hass.services.async_call(
            "media_player",
            service,
            service_data,
            blocking=True,
        )

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Subscribe to source entity state changes."""

        @callback
        def _source_changed(event) -> None:
            self.async_write_ha_state()

        self._remove_listener = async_track_state_change_event(
            self.hass,
            [self._source_entity],
            _source_changed,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from source entity state changes."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    # ---------------------------------------------------------------------
    # Core entity state
    # ---------------------------------------------------------------------

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
        """Mirror source features and add Plex next/previous while Plex is active."""
        features = self._source_features()

        if self._is_plex_cast():
            features |= MediaPlayerEntityFeature.NEXT_TRACK
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK

        return MediaPlayerEntityFeature(features)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Mirror source attributes and add proxy metadata."""
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

    # ---------------------------------------------------------------------
    # Mirrored media properties
    # ---------------------------------------------------------------------

    @property
    def volume_level(self) -> float | None:
        return self._source_attr("volume_level")

    @property
    def is_volume_muted(self) -> bool | None:
        return self._source_attr("is_volume_muted")

    @property
    def media_content_id(self) -> str | None:
        return self._source_attr("media_content_id")

    @property
    def media_content_type(self) -> str | None:
        return self._source_attr("media_content_type")

    @property
    def media_duration(self) -> int | float | None:
        return self._source_attr("media_duration")

    @property
    def media_position(self) -> int | float | None:
        return self._source_attr("media_position")

    @property
    def media_position_updated_at(self):
        return self._source_attr("media_position_updated_at")

    @property
    def media_title(self) -> str | None:
        return self._source_attr("media_title")

    @property
    def media_artist(self) -> str | None:
        return self._source_attr("media_artist")

    @property
    def media_album_name(self) -> str | None:
        return self._source_attr("media_album_name")

    @property
    def media_album_artist(self) -> str | None:
        return self._source_attr("media_album_artist")

    @property
    def media_track(self) -> int | None:
        return self._source_attr("media_track")

    @property
    def media_series_title(self) -> str | None:
        return self._source_attr("media_series_title")

    @property
    def media_season(self) -> str | int | None:
        return self._source_attr("media_season")

    @property
    def media_episode(self) -> str | int | None:
        return self._source_attr("media_episode")

    @property
    def media_channel(self) -> str | None:
        return self._source_attr("media_channel")

    @property
    def media_image_url(self) -> str | None:
        return self._source_attr("entity_picture")

    @property
    def app_id(self) -> str | None:
        return self._source_attr("app_id")

    @property
    def app_name(self) -> str | None:
        return self._source_attr("app_name")

    @property
    def source(self) -> str | None:
        return self._source_attr("source")

    @property
    def source_list(self) -> list[str] | None:
        return self._source_attr("source_list")

    @property
    def sound_mode(self) -> str | None:
        return self._source_attr("sound_mode")

    @property
    def sound_mode_list(self) -> list[str] | None:
        return self._source_attr("sound_mode_list")

    @property
    def shuffle(self) -> bool | None:
        return self._source_attr("shuffle")

    @property
    def repeat(self) -> str | None:
        return self._source_attr("repeat")

    # ---------------------------------------------------------------------
    # Transport controls
    # ---------------------------------------------------------------------

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

        await self._delegate("media_next_track")

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

        await self._delegate("media_previous_track")

    async def async_media_play_pause(self) -> None:
        await self._delegate("media_play_pause")

    async def async_media_play(self) -> None:
        await self._delegate("media_play")

    async def async_media_pause(self) -> None:
        await self._delegate("media_pause")

    async def async_media_stop(self) -> None:
        await self._delegate("media_stop")

    async def async_media_seek(self, position: float) -> None:
        await self._delegate("media_seek", seek_position=position)

    async def async_play_media(
        self,
        media_type: str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        """Play media on source entity."""
        await self._delegate(
            "play_media",
            media_content_type=media_type,
            media_content_id=media_id,
            **kwargs,
        )

    # ---------------------------------------------------------------------
    # Volume / power controls
    # ---------------------------------------------------------------------

    async def async_set_volume_level(self, volume: float) -> None:
        await self._delegate("volume_set", volume_level=volume)

    async def async_mute_volume(self, mute: bool) -> None:
        await self._delegate("volume_mute", is_volume_muted=mute)

    async def async_volume_up(self) -> None:
        await self._delegate("volume_up")

    async def async_volume_down(self) -> None:
        await self._delegate("volume_down")

    async def async_turn_on(self) -> None:
        await self._delegate("turn_on")

    async def async_turn_off(self) -> None:
        await self._delegate("turn_off")

    # ---------------------------------------------------------------------
    # Source / sound / playlist controls
    # ---------------------------------------------------------------------

    async def async_select_source(self, source: str) -> None:
        await self._delegate("select_source", source=source)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        await self._delegate("select_sound_mode", sound_mode=sound_mode)

    async def async_set_shuffle(self, shuffle: bool) -> None:
        await self._delegate("shuffle_set", shuffle=shuffle)

    async def async_set_repeat(self, repeat: str) -> None:
        await self._delegate("repeat_set", repeat=repeat)

    async def async_clear_playlist(self) -> None:
        await self._delegate("clear_playlist")

    async def async_join_players(self, group_members: list[str]) -> None:
        await self._delegate("join", group_members=group_members)

    async def async_unjoin_player(self) -> None:
        await self._delegate("unjoin")

