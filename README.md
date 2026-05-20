# Plex Cast Control

A Home Assistant custom integration that adds Plex-native next/previous controls for Chromecast / Google Cast devices running the Plex Cast app.

This is useful when Home Assistant's standard `media_player.media_next_track` and `media_player.media_previous_track` actions are unsupported during Plex playback on Cast devices.

## What it does

Plex Cast Control provides:

- Proxy media player entities that expose working next/previous buttons to normal Home Assistant media-player cards
- `plex_cast_control.next`
- `plex_cast_control.previous`

The integration uses the Plex Cast namespace exposed by Chromecast devices running the Plex app.

No Plex token is required.

## Requirements

- Home Assistant
- A Chromecast / Google Cast device or Cast speaker group
- Home Assistant's Cast integration working for the target device
- Plex playback active on that Cast device when using Plex-specific next/previous controls

## Installation

Copy this integration into Home Assistant:

```text
/config/custom_components/plex_cast_control/
```

Restart Home Assistant.

Then add the integration from the UI:

```text
Settings → Devices & services → Add integration → Plex Cast Control
```

Select the source Cast media player entity you want to wrap, then give the proxy a name.

You can add multiple entries, one per Cast device or Cast speaker group.

## Proxy media player

After adding an entry through the integration setup flow, Plex Cast Control creates a proxy `media_player` entity.

Use that proxy entity in your dashboard instead of the original Cast entity.

Example:

```yaml
type: media-control
entity: media_player.living_room_speaker_plex_proxy
```

The proxy entity mirrors the source Cast media player and only adds next/previous support while the source Cast device is running Plex.

When Plex is not active, the proxy mirrors the source entity's normal supported features and does not force Plex-specific next/previous behavior.

## Services

The integration also exposes services directly.

These services should target the original Cast media player entity, not the proxy entity.

### Next

```yaml
action: plex_cast_control.next
data:
  entity_id: media_player.your_cast_device
```

### Previous

```yaml
action: plex_cast_control.previous
data:
  entity_id: media_player.your_cast_device
```

## Previous-track behavior

Plex Cast previous-track behavior is position-aware:

- Near the start of a track, previous goes to the previous track.
- Later in a track, previous normally restarts the current track.

This integration accounts for that behavior so the proxy's previous button behaves like a typical previous-track button.

## Limitations

- This is Plex-specific.
- It does not fix generic Chromecast next/previous support for non-Plex Cast apps.
- It only adds Plex-native next/previous behavior while the target Cast device is running the Plex Cast app.
