"""Config flow for Broadlink AC integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .broadlink.ac_db import gendevice

DOMAIN = "aux_climate"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="空调"): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_MAC): str,
        vol.Optional(CONF_PORT, default=80): int,
    }
)


class BroadlinkAcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Broadlink AC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac = user_input[CONF_MAC].replace(":", "").replace("-", "").lower()
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            name = user_input[CONF_NAME]

            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()

            try:
                mac_bytes = bytearray.fromhex(mac)
                if len(mac_bytes) != 6:
                    errors["mac"] = "MAC地址格式错误，需要6字节（12个十六进制字符）"
                else:
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_NAME: name,
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_MAC: mac,
                        },
                    )
            except ValueError:
                errors["mac"] = "MAC地址格式错误，请输入有效的十六进制字符串"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
