"""Switch platform for Broadlink AC extra features."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN, MANUFACTURER
from .broadlink.ac_db import ac_db, version as ac_version

_LOGGER = logging.getLogger(__name__)


# Extra features available in the Broadlink protocol
EXTRA_SWITCHES = [
    {
        "key": "sleep",
        "name": "睡眠模式",
        "icon": "mdi:sleep",
        "set_func": lambda dev, val: dev.set_sleep("ON" if val else "OFF"),
    },
    {
        "key": "display",
        "name": "面板显示",
        "icon": "mdi:monitor-dashboard",
        "set_func": lambda dev, val: dev.set_display("ON" if val else "OFF"),
    },
    {
        "key": "health",
        "name": "健康模式",
        "icon": "mdi:shield-check",
        "set_func": lambda dev, val: dev.set_health("ON" if val else "OFF"),
    },
    {
        "key": "clean",
        "name": "自清洁",
        "icon": "mdi:water-pump",
        "set_func": lambda dev, val: dev.set_clean("ON" if val else "OFF"),
    },
    {
        "key": "mildew",
        "name": "防霉",
        "icon": "mdi:water-off",
        "set_func": lambda dev, val: dev.set_mildew("ON" if val else "OFF"),
    },
    {
        "key": "mute",
        "name": "静音模式",
        "icon": "mdi:volume-off",
        "set_func": lambda dev, val: dev.set_mute("ON" if val else "OFF"),
    },
    {
        "key": "turbo",
        "name": "强力模式",
        "icon": "mdi:weather-windy",
        "set_func": lambda dev, val: dev.set_turbo("ON" if val else "OFF"),
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Broadlink AC switch platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    device: ac_db = data["device"]
    mac = data["mac"]

    entities = []
    for sw in EXTRA_SWITCHES:
        entities.append(BroadlinkAcSwitch(device, mac, sw))

    # Always add the debug log switch
    entities.append(BroadlinkAcDebugSwitch(device, mac))

    if entities:
        async_add_entities(entities, False)


class BroadlinkAcSwitch(SwitchEntity):
    """Representation of a Broadlink AC extra feature switch."""

    _attr_should_poll = True

    def __init__(self, device: ac_db, mac: str, config: dict) -> None:
        """Initialize the switch."""
        self._device = device
        self._key = config["key"]
        self._set_func = config["set_func"]
        self._attr_name = config["name"]
        self._attr_unique_id = f"{mac}_{config['key']}"
        self._attr_icon = config["icon"]
        self._attr_is_on = False

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
                val = status.get(self._key)
                self._attr_is_on = val == "ON"
        except Exception as ex:
            _LOGGER.warning("更新%s状态失败: %s", self._key, ex)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        try:
            await self.hass.async_add_executor_job(self._set_func, self._device, True)
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("开启%s失败: %s", self._key, ex)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        try:
            await self.hass.async_add_executor_job(self._set_func, self._device, False)
            self._attr_is_on = False
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("关闭%s失败: %s", self._key, ex)


class BroadlinkAcDebugSwitch(SwitchEntity):
    """Switch for enabling/disabling raw payload debug logging."""

    _attr_should_poll = True

    def __init__(self, device: ac_db, mac: str) -> None:
        """Initialize the debug log switch."""
        self._device = device
        self._key = "debug_logging"
        self._attr_name = "调试日志"
        self._attr_unique_id = f"{mac}_debug_logging"
        self._attr_icon = "mdi:text-box-search-outline"
        self._attr_is_on = self._device.get_raw_logging()

    @property
    def device_info(self):
        """Return device info to group under one device."""
        return {
            "identifiers": {(DOMAIN, self._device.status["macaddress"])},
        }

    async def async_update(self) -> None:
        """Fetch latest state from the device."""
        self._attr_is_on = self._device.get_raw_logging()

    async def async_turn_on(self, **kwargs):
        """Turn debug logging on."""
        try:
            await self.hass.async_add_executor_job(self._device.set_raw_logging, True)
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("开启调试日志失败: %s", ex)

    async def async_turn_off(self, **kwargs):
        """Turn debug logging off."""
        try:
            await self.hass.async_add_executor_job(self._device.set_raw_logging, False)
            self._attr_is_on = False
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("关闭调试日志失败: %s", ex)
