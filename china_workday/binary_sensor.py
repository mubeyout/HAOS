"""Sensor to indicate whether the current day is a workday."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Final

from holidays import HolidayBase
import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    async_get_current_platform,
)

from . import WorkdayConfigEntry
from .china_holidays import (
    calculate_week_type,
    get_makeup_days,
)
from .const import (
    CONF_ENABLE_WEEK_TYPE,
    CONF_EXCLUDES,
    CONF_WEEK_TYPE_START_DATE,
    CONF_WORKDAYS,
    SENSOR_RESTDAY,
    SENSOR_WORKDAY,
)
from .entity import BaseWorkdayEntity

SERVICE_CHECK_DATE: Final = "check_date"
CHECK_DATE: Final = "check_date"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WorkdayConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Workday sensor."""
    excludes: list[str] = entry.options[CONF_EXCLUDES]
    sensor_name: str = entry.options[CONF_NAME]
    workdays: list[str] = entry.options[CONF_WORKDAYS]
    obj_holidays = entry.runtime_data

    # 获取大周小周配置
    enable_week_type = entry.options.get(CONF_ENABLE_WEEK_TYPE, False)
    week_type_start_date = entry.options.get(CONF_WEEK_TYPE_START_DATE)

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_CHECK_DATE,
        {vol.Required(CHECK_DATE): cv.date},
        "check_date",
        None,
        SupportsResponse.ONLY,
    )

    async_add_entities(
        [
            IsWorkdaySensor(
                obj_holidays,
                workdays,
                excludes,
                sensor_name,
                entry.entry_id,
                enable_week_type,
                week_type_start_date,
            ),
            IsRestdaySensor(
                obj_holidays,
                workdays,
                excludes,
                sensor_name,
                entry.entry_id,
                enable_week_type,
                week_type_start_date,
            ),
        ],
    )


class IsWorkdaySensor(BaseWorkdayEntity, BinarySensorEntity):
    """Implementation of a Workday sensor."""

    # 覆盖基类设置，使用自定义名称
    _attr_has_entity_name = False
    _attr_translation_key = SENSOR_WORKDAY

    def __init__(
        self,
        obj_holidays: HolidayBase,
        workdays: list[str],
        excludes: list[str],
        name: str,
        entry_id: str,
        enable_week_type: bool = False,
        week_type_start_date: str | None = None,
    ) -> None:
        """Initialize the Workday sensor."""
        super().__init__(
            obj_holidays,
            workdays,
            excludes,
            0,  # 不再使用 days_offset
            name,
            entry_id,
        )
        # 覆盖 unique_id，添加后缀
        self._attr_unique_id = f"{entry_id}_{SENSOR_WORKDAY}"
        self._enable_week_type = enable_week_type
        self._week_type_start_date = week_type_start_date

        if self._week_type_start_date:
            try:
                self._start_date = date.fromisoformat(self._week_type_start_date)
            except ValueError:
                self._start_date = None
        else:
            self._start_date = None

        self._attr_extra_state_attributes = {
            CONF_WORKDAYS: workdays,
            CONF_EXCLUDES: excludes,
        }

    def is_makeup_day(self, check_date: date) -> bool:
        """检查是否为补班日。"""
        year = check_date.year
        makeup_days = get_makeup_days(year)
        date_str = check_date.strftime("%Y-%m-%d")
        return date_str in makeup_days

    def date_is_workday(self, check_date: date) -> bool:
        """检查是否为工作日，覆盖基类方法以支持补班日。"""
        is_workday = super().date_is_workday(check_date)

        # 检查补班日：如果今天不是工作日，但是补班日，则为工作日
        if not is_workday and self.is_makeup_day(check_date):
            # 检查补班日是否在工作日配置中
            if "makeup_day" in self._workdays:
                return True

        # 检查大周小周
        if self._enable_week_type and self._start_date:
            week_type = calculate_week_type(check_date, self._start_date)
            if week_type == "小周":
                # 小周周六不工作
                if check_date.weekday() == 5:  # 星期六
                    return False
            elif week_type == "大周":
                # 大周周六工作
                if check_date.weekday() == 5:  # 星期六
                    # 需要在工作日配置中包含周六
                    if "sat" in self._workdays:
                        return True

        return is_workday

    def update_data(self, now: datetime) -> None:
        """Get date and look whether it is a holiday."""
        check_date = now.date()

        # 更新基础状态
        self._attr_is_on = self.date_is_workday(check_date)

        # 更新额外属性
        year = check_date.year
        date_str = check_date.strftime("%Y-%m-%d")

        # 检查是否在中国法定节假日
        china_holiday_name = self.get_china_holiday_name(check_date)
        is_china_holiday = china_holiday_name is not None

        # 检查是否为补班日
        is_makeup = self.is_makeup_day(check_date)

        # 周类型
        week_type = None
        if self._enable_week_type and self._start_date:
            week_type = calculate_week_type(check_date, self._start_date)

        # 计算下一个工作日和休息日
        next_workday = None
        next_restday = None
        days_until_next_workday = None
        days_until_next_restday = None

        search_date = check_date + timedelta(days=1)
        days_count = 1

        while days_count <= 365:
            if self.date_is_workday(search_date):
                if not next_workday:
                    next_workday = search_date.isoformat()
                    days_until_next_workday = days_count
            else:
                if not next_restday:
                    next_restday = search_date.isoformat()
                    days_until_next_restday = days_count

            if next_workday and next_restday:
                break

            search_date += timedelta(days=1)
            days_count += 1

        # 更新属性
        self._attr_extra_state_attributes = {
            CONF_WORKDAYS: self._workdays,
            CONF_EXCLUDES: self._excludes,
            "is_china_holiday": is_china_holiday,
            "china_holiday_name": china_holiday_name,
            "is_makeup_day": is_makeup,
            "week_type": week_type,
            "next_workday": next_workday,
            "days_until_next_workday": days_until_next_workday,
            "next_restday": next_restday,
            "days_until_next_restday": days_until_next_restday,
        }


class IsRestdaySensor(BaseWorkdayEntity, BinarySensorEntity):
    """Implementation of a Restday sensor (opposite of Workday)."""

    # 覆盖基类设置，使用自定义名称
    _attr_has_entity_name = False
    _attr_translation_key = SENSOR_RESTDAY

    def __init__(
        self,
        obj_holidays: HolidayBase,
        workdays: list[str],
        excludes: list[str],
        name: str,
        entry_id: str,
        enable_week_type: bool = False,
        week_type_start_date: str | None = None,
    ) -> None:
        """Initialize the Restday sensor."""
        super().__init__(
            obj_holidays,
            workdays,
            excludes,
            0,
            name,
            entry_id,
        )
        # 覆盖 unique_id，添加后缀
        self._attr_unique_id = f"{entry_id}_{SENSOR_RESTDAY}"
        self._enable_week_type = enable_week_type
        self._week_type_start_date = week_type_start_date

        if self._week_type_start_date:
            try:
                self._start_date = date.fromisoformat(self._week_type_start_date)
            except ValueError:
                self._start_date = None
        else:
            self._start_date = None

        self._attr_extra_state_attributes = {
            CONF_WORKDAYS: workdays,
            CONF_EXCLUDES: excludes,
        }

    def is_makeup_day(self, check_date: date) -> bool:
        """检查是否为补班日。"""
        year = check_date.year
        makeup_days = get_makeup_days(year)
        date_str = check_date.strftime("%Y-%m-%d")
        return date_str in makeup_days

    def date_is_workday(self, check_date: date) -> bool:
        """检查是否为工作日（复用 Workday 逻辑）。"""
        is_workday = super().date_is_workday(check_date)

        # 检查补班日
        if not is_workday and self.is_makeup_day(check_date):
            if "makeup_day" in self._workdays:
                return True

        # 检查大周小周
        if self._enable_week_type and self._start_date:
            week_type = calculate_week_type(check_date, self._start_date)
            if week_type == "小周":
                if check_date.weekday() == 5:
                    return False
            elif week_type == "大周":
                if check_date.weekday() == 5:
                    if "sat" in self._workdays:
                        return True

        return is_workday

    def update_data(self, now: datetime) -> None:
        """Get date and check if it's a restday."""
        check_date = now.date()

        # Restday 是 Workday 的反状态
        self._attr_is_on = not self.date_is_workday(check_date)

        # 更新额外属性
        china_holiday_name = self.get_china_holiday_name(check_date)
        is_china_holiday = china_holiday_name is not None

        self._attr_extra_state_attributes = {
            CONF_WORKDAYS: self._workdays,
            CONF_EXCLUDES: self._excludes,
            "is_china_holiday": is_china_holiday,
            "china_holiday_name": china_holiday_name,
        }

