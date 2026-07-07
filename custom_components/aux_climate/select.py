"""Select platform for Broadlink AC horizontal swing."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN, MANUFACTURER
from .broadlink.ac_db import ac_db, version as ac_version

_LOGGER = logging.getLogger(__name__)

# Horizontal swing options from ac_db.STATIC.FIXATION.HORIZONTAL
HORIZONTAL_OPTIONS = [
    "LEFT_FIX",
    "LEFT_FLAP",
    "LEFT_RIGHT_FIX",
    "LEFT_RIGHT_FLAP",
    "RIGHT_FIX",
    "RIGHT_FLAP",
    "ON",
    "OFF",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Broadlink AC select platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    device: ac_db = data["device"]
    mac = data["mac"]

    async_add_entities([BroadlinkAcHorizontalSwing(device, mac)], False)


class BroadlinkAcHorizontalSwing(SelectEntity):
    """Horizontal swing mode selector."""

    _attr_options = HORIZONTAL_OPTIONS

    def __init__(self, device: ac_db, mac: str) -> None:
        """Initialize horizontal swing select."""
        self._device = device
        self._attr_name = "水平摆风"
        self._attr_unique_id = f"{mac}_fixation_h"
        self._attr_icon = "mdi:swap-horizontal"
        self._attr_current_option = "LEFT_RIGHT_FIX"

    @property
    def device_info(self):
        """Return device info to group under one device."""
        return {
            "identifiers": {(DOMAIN, self._device.status["macaddress"])},
        }

    async def async_update(self) -> None:
        """Fetch latest state from the device."""
        try:
            status = await self.hass.async_add_executor_job(
                self._device.get_ac_status
            )
            if status:
                val = status.get("fixation_h")
                if val and val in self._attr_options:
                    self._attr_current_option = val
        except Exception as ex:
            _LOGGER.warning("更新水平摆风状态失败: %s", ex)

    async def async_select_option(self, option: str) -> None:
        """Change the horizontal swing mode."""
        try:
            await self.hass.async_add_executor_job(
                self._device.set_fixation_h, option
            )
            self._attr_current_option = option
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("设置水平摆风失败: %s", ex)
