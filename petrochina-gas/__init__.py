"""昆仑燃气集成"""
import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_ACCOUNTS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
    """设置集成入口"""
    from .sensor import async_setup_entry as async_setup_sensor

    if not config_entry.data.get(CONF_ACCOUNTS):
        _LOGGER.error("No gas accounts in config")
        return False

    # 设置传感器
    await async_setup_sensor(hass, config_entry)

    _LOGGER.info(f"Setup complete for config entry: {config_entry.entry_id}")
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
    """卸载集成入口"""
    _LOGGER.info(f"Unloading config entry: {config_entry.entry_id}")
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
    """迁移配置条目"""
    _LOGGER.info(f"Migrating config entry from version {config_entry.version}")
    return True


async def async_remove_entry(hass: HomeAssistant, config_entry_id: str) -> None:
    """移除配置条目"""
    _LOGGER.info(f"Removing config entry: {config_entry_id}")
