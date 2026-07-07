"""Broadlink AC integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .broadlink.ac_db import ac_db, ConnectTimeout, version as ac_version

_LOGGER = __import__("logging").getLogger(__name__)

DOMAIN = "aux_climate"
MANUFACTURER = "AUX"

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Broadlink AC from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    mac = entry.data[CONF_MAC]
    name = entry.data[CONF_NAME]
    mac_bytes = bytearray.fromhex(mac)

    try:
        device = await hass.async_add_executor_job(
            _create_device, host, port, mac_bytes, name
        )
    except ConnectTimeout:
        _LOGGER.error("连接空调超时: %s:%s", host, port)
        return False
    except Exception as ex:
        _LOGGER.error("初始化空调失败: %s", ex)
        return False

    # Register the device in HA device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, mac)},
        manufacturer=MANUFACTURER,
        name=name,
        model="AUX AC",
        sw_version=ac_version,
        configuration_url=f"http://{host}:{port}",
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "device": device,
        "name": name,
        "mac": mac,
        "host": host,
        "port": port,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _create_device(host: str, port: int, mac_bytes: bytearray, name: str) -> ac_db:
    """Create device instance (blocking network calls)."""
    dev = ac_db(
        host=(host, port),
        mac=mac_bytes,
        name=name,
    )
    return dev
