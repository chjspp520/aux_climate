"""Sensor platform for Broadlink AC — indoor temp, humidity, error code."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .broadlink.ac_db import ac_db

_LOGGER = logging.getLogger(__name__)

SENSOR_DEFS = [
    {
        "key": "ambient_temp",
        "name": "室内温度",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    {
        "key": "room_hum",
        "name": "室内湿度",
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water-percent",
    },
    {
        "key": "err_code",
        "name": "错误代码",
        "device_class": None,
        "unit": None,
        "state_class": None,
        "icon": "mdi:alert-circle-outline",
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Broadlink AC sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    device: ac_db = data["device"]
    mac = data["mac"]

    entities = [
        BroadlinkAcSensor(device, mac, defn) for defn in SENSOR_DEFS
    ]
    async_add_entities(entities, False)


class BroadlinkAcSensor(SensorEntity):
    """Representation of a Broadlink AC sensor."""

    _attr_should_poll = True

    def __init__(self, device: ac_db, mac: str, defn: dict) -> None:
        """Initialize the sensor."""
        self._device = device
        self._key = defn["key"]
        self._attr_name = defn["name"]
        self._attr_unique_id = f"{mac}_{defn['key']}"
        self._attr_icon = defn["icon"]

        if defn["device_class"]:
            self._attr_device_class = defn["device_class"]
        if defn["unit"]:
            self._attr_native_unit_of_measurement = defn["unit"]
        if defn["state_class"]:
            self._attr_state_class = defn["state_class"]

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
            if not status:
                status = self._device.status
            val = status.get(self._key) if status else self._device.status.get(self._key)
            self._attr_native_value = val
        except Exception as ex:
            _LOGGER.warning("更新传感器%s失败: %s", self._key, ex)
