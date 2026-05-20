"""Config flow for Plex Cast Control."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import CONF_SOURCE_ENTITY, DOMAIN


class PlexCastControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Plex Cast Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors = {}

        if user_input is not None:
            source_entity = user_input[CONF_SOURCE_ENTITY]

            source_state = self.hass.states.get(source_entity)
            default_name = self._default_name_for_source(source_entity)

            if source_state is not None:
                friendly_name = source_state.attributes.get("friendly_name")
                if friendly_name:
                    default_name = f"{friendly_name} Plex Proxy"

            name = user_input.get(CONF_NAME) or default_name

            await self.async_set_unique_id(source_entity)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={
                    CONF_SOURCE_ENTITY: source_entity,
                    CONF_NAME: name,
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=MEDIA_PLAYER_DOMAIN)
                ),
                vol.Optional(CONF_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    def _default_name_for_source(self, source_entity: str) -> str:
        """Return fallback proxy name from an entity ID."""
        object_id = source_entity.split(".", 1)[-1]
        friendly = object_id.replace("_", " ").title()
        return f"{friendly} Plex Proxy"

