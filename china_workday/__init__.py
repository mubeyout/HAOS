"""中国工作日集成 - 牛马日历。"""

from __future__ import annotations

from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .china_holidays import get_china_holiday_data, get_makeup_days, parse_important_dates_input, get_holidays_with_cache
from .const import (
    CONF_ADD_HOLIDAYS,
    CONF_EXCLUDES,
    CONF_IMPORTANT_DATES,
    CONF_REMOVE_HOLIDAYS,
    CONF_WORKDAYS,
    DEFAULT_NAME,
    LOGGER,
    PLATFORMS,
)
from .util import validate_dates

type WorkdayConfigEntry = ConfigEntry[None]


async def async_setup_entry(hass: HomeAssistant, entry: WorkdayConfigEntry) -> bool:
    """设置中国工作日集成。"""

    # 验证并处理添加/移除的节假日
    calc_add_holidays = cast(
        list[str], validate_dates(entry.options.get(CONF_ADD_HOLIDAYS, ""))
    )
    calc_remove_holidays: list[str] = validate_dates(
        entry.options.get(CONF_REMOVE_HOLIDAYS, "")
    )

    # 获取工作日和排除日期配置
    workdays = entry.options.get(CONF_WORKDAYS, [])
    excludes = entry.options.get(CONF_EXCLUDES, [])

    # 解析重要日期
    important_dates_input = entry.options.get(CONF_IMPORTANT_DATES, "")
    important_dates = parse_important_dates_input(important_dates_input)

    # 获取中国法定节假日数据（初始化时强制刷新缓存）
    year = dt_util.now().year

    # 强制刷新今年的节假日数据（初始化时）
    china_holidays = await get_holidays_with_cache(hass, year, force_refresh=True)
    next_year_holidays = await get_holidays_with_cache(hass, year + 1, force_refresh=True)

    # 获取补班日
    makeup_days = get_makeup_days(year) + get_makeup_days(year + 1)

    if china_holidays:
        LOGGER.info(f"成功获取 {year} 年节假日数据，共 {len(china_holidays)} 个")
    else:
        LOGGER.warning(f"未能获取 {year} 年节假日数据")

    # 存储配置到 runtime_data
    entry.runtime_data = {
        "workdays": workdays,
        "excludes": excludes,
        "add_holidays": calc_add_holidays,
        "remove_holidays": calc_remove_holidays,
        "important_dates": important_dates,
        "china_holidays": china_holidays or [],
        "next_year_holidays": next_year_holidays or [],
        "makeup_days": makeup_days,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WorkdayConfigEntry) -> bool:
    """卸载中国工作日集成。"""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
