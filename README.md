# Plex Cast Control

A Home Assistant custom integration that adds working Plex-native next/previous controls for Chromecast / Cast devices running the Plex Cast app.

This is useful when Home Assistant's standard media_player.media_next_track and media_player.media_previous_track actions are unsupported on a Cast media player during Plex playback.

## What it does

Plex Cast Control provides:

- plex_cast_control.next
- plex_cast_control.previous
- optional proxy media player entities that expose working next/previous buttons to normal media-player cards

The integration uses the Plex Cast namespace exposed by Chromecast devices running the Plex app.

## Requirements

- Home Assistant
- A Chromecast / Google Cast device
- Plex playback active on that Cast device
- Home Assistant's Cast integration working for the target device

No Plex token is required.

## Local installation

Copy this folder into Home Assistant:

    /config/custom_components/plex_cast_control/

Restart Home Assistant.

Add this to configuration.yaml:

    plex_cast_control:

## Services

Next:

    action: plex_cast_control.next
    data:
      entity_id: media_player.your_cast_device

Previous:

    action: plex_cast_control.previous
    data:
      entity_id: media_player.your_cast_device

## Proxy media player

To create a proxy media player that works with normal HA media cards:

    media_player:
      - platform: plex_cast_control
        name: My Speaker Plex Control
        source_entity: media_player.my_speaker

Then point your media card at the proxy entity.

Example:

    type: media-control
    entity: media_player.my_speaker_plex_control

The proxy entity mirrors the source Cast media player and only adds next/previous support while the source Cast device is running Plex.

## Notes

Plex previous-track behavior is position-aware:

- near the start of a track, previous goes to the previous track
- later in a track, previous normally restarts the current track

This integration accounts for that behavior so previous works like a typical previous-track button.

## Limitations

- This is Plex-specific.
- It does not fix generic Chromecast next/previous support.
- It only works when the target Cast device is running the Plex Cast app.
