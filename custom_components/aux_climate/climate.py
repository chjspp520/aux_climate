"""Climate platform for Broadlink AC integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN, MANUFACTURER
from .broadlink.ac_db import ac_db, version as ac_version

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

HVAC_MODE_MAP = {
    "off": HVACMode.OFF,
    "cool": HVACMode.COOL,
    "heat": HVACMode.HEAT,
    "dry": HVACMode.DRY,
    "fan_only": HVACMode.FAN_ONLY,
    "auto": HVACMode.AUTO,
}

HVAC_MODE_TO_BROADLINK = {
    HVACMode.COOL: "cool",
    HVACMode.HEAT: "heat",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fan_only",
    HVACMode.AUTO: "auto",
    HVACMode.OFF: "off",
}

FAN_MODE_TO_BROADLINK = {
    "Auto": "AUTO",
    "Low": "LOW",
    "Medium": "MEDIUM",
    "High": "HIGH",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Broadlink AC climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    device: ac_db = data["device"]
    name = data["name"]
    mac = data["mac"]

    async_add_entities(
        [BroadlinkAcClimate(device, name, mac)], update_before_add=False
    )


class BroadlinkAcClimate(ClimateEntity):
    """Representation of a Broadlink AC via local network."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 16
    _attr_max_temp = 32

    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.AUTO,
    ]
    _attr_fan_modes = ["Auto", "Low", "Medium", "High", "Turbo", "Mute"]
    _attr_swing_modes = [
        "TOP", "MIDDLE1", "MIDDLE2", "MIDDLE3",
        "BOTTOM", "SWING", "AUTO",
    ]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    # Default state before first poll
    _attr_fan_mode = "Auto"
    _attr_hvac_mode = HVACMode.OFF
    _attr_swing_mode = "AUTO"
    _attr_current_temperature = None
    _attr_target_temperature = 26

    def __init__(self, device: ac_db, name: str, unique_id: str) -> None:
        """Initialize the climate entity."""
        self._device = device
        self._attr_name = name
        self._attr_unique_id = f"{unique_id}_climate"

    @property
    def device_info(self):
        """Return device info to group under one device."""
        return {
            "identifiers": {(DOMAIN, self._device.status["macaddress"])},
        }

    async def _async_execute(self, func, *args, **kwargs):
        """Execute a blocking method in the executor."""
        return await self.hass.async_add_executor_job(func, *args, **kwargs)

    def _process_status(self, status: dict):
        """Update HA state attributes from Broadlink status dict."""
        if not status:
            return

        ambient = status.get("ambient_temp")
        if ambient is not None:
            self._attr_current_temperature = float(ambient)

        temp = status.get("temp")
        if temp is not None:
            self._attr_target_temperature = float(temp)

        mode_ha = status.get("mode_homeassistant", "off")
        self._attr_hvac_mode = HVAC_MODE_MAP.get(mode_ha, HVACMode.OFF)

        fan = status.get("fanspeed_homeassistant")
        if fan and fan in self._attr_fan_modes:
            self._attr_fan_mode = fan

        swing = status.get("fixation_v")
        if swing and swing in self._attr_swing_modes:
            self._attr_swing_mode = swing

    async def async_update(self) -> None:
        """Poll the device for current status."""
        try:
            status = await self._async_execute(self._device.get_ac_status)
            self._process_status(status)
        except Exception as ex:
            _LOGGER.warning("更新空调状态失败: %s", ex)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        bl_mode = HVAC_MODE_TO_BROADLINK.get(hvac_mode)
        if bl_mode is None:
            return

        try:
            if hvac_mode == HVACMode.OFF:
                status = await self._async_execute(self._device.switch_off)
            else:
                status = await self._async_execute(
                    self._device.set_homeassistant_mode, bl_mode
                )
            self._process_status(status)
        except Exception as ex:
            _LOGGER.error("设置空调模式失败: %s", ex)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            status = await self._async_execute(
                self._device.set_temperature, float(temperature)
            )
            self._process_status(status)
        except Exception as ex:
            _LOGGER.error("设置空调温度失败: %s", ex)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        try:
            if fan_mode == "Turbo":
                status = await self._async_execute(self._device.set_turbo, "ON")
            elif fan_mode == "Mute":
                status = await self._async_execute(self._device.set_mute, "ON")
            else:
                bl_fan = FAN_MODE_TO_BROADLINK.get(fan_mode, "AUTO")
                status = await self._async_execute(
                    self._device.set_fanspeed, bl_fan
                )
            self._process_status(status)
        except Exception as ex:
            _LOGGER.error("设置空调风速失败: %s", ex)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set swing (fixation) mode."""
        bl_swing = swing_mode
        try:
            status = await self._async_execute(
                self._device.set_fixation_v, bl_swing
            )
            self._process_status(status)
        except Exception as ex:
            _LOGGER.error("设置空调扫风模式失败: %s", ex)

    async def async_turn_on(self) -> None:
        """Turn the AC on."""
        try:
            status = await self._async_execute(self._device.switch_on)
            self._process_status(status)
        except Exception as ex:
            _LOGGER.error("开启空调失败: %s", ex)

    async def async_turn_off(self) -> None:
        """Turn the AC off."""
        try:
            status = await self._async_execute(self._device.switch_off)
            self._process_status(status)
        except Exception as ex:
            _LOGGER.error("关闭空调失败: %s", ex)
