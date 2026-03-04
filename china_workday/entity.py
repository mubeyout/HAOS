"""工作日实体基类。"""

from __future__ import annotations

from abc import abstractmethod
from datetime import date, datetime, timedelta

from homeassistant.core import CALLBACK_TYPE, ServiceResponse, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from .const import ALLOWED_DAYS, DOMAIN


class BaseWorkdayEntity(Entity):
    """工作日实体基类。"""

    _attr_has_entity_name = True
    _attr_translation_key = DOMAIN
    _attr_should_poll = False
    unsub: CALLBACK_TYPE | None = None

    def __init__(
        self,
        runtime_data: dict | None,
        workdays: list[str],
        excludes: list[str],
        days_offset: int,
        name: str,
        entry_id: str,
    ) -> None:
        """初始化工作日实体。"""
        self._runtime_data = runtime_data or {}
        self._workdays = workdays
        self._excludes = excludes
        self._days_offset = days_offset
        self._attr_unique_id = entry_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="China Workday",
            model="Custom",
            name=name,
        )

    def is_include(self, day: str, now: date) -> bool:
        """检查给定日期是否在包含列表中。"""
        if day in self._workdays:
            return True

        # 检查是否为中国节假日
        if "holiday" in self._workdays:
            china_holidays = self._runtime_data.get("china_holidays", [])
            next_year_holidays = self._runtime_data.get("next_year_holidays", [])
            all_holidays = china_holidays + next_year_holidays

            for holiday in all_holidays:
                try:
                    holiday_date = date.fromisoformat(holiday["date"])
                    if holiday_date == now:
                        return True
                except (ValueError, KeyError):
                    continue

        return False

    def is_exclude(self, day: str, now: date) -> bool:
        """检查给定日期是否在排除列表中。"""
        if day in self._excludes:
            return True

        # 检查是否为排除的节假日
        if "holiday" in self._excludes:
            china_holidays = self._runtime_data.get("china_holidays", [])
            next_year_holidays = self._runtime_data.get("next_year_holidays", [])
            all_holidays = china_holidays + next_year_holidays

            for holiday in all_holidays:
                try:
                    holiday_date = date.fromisoformat(holiday["date"])
                    if holiday_date == now:
                        return True
                except (ValueError, KeyError):
                    continue

        return False

    def is_makeup_day(self, check_date: date) -> bool:
        """检查是否为补班日。"""
        makeup_days = self._runtime_data.get("makeup_days", [])
        if makeup_days:
            date_str = check_date.strftime("%Y-%m-%d")
            return date_str in makeup_days
        return False

    def get_china_holiday_name(self, check_date: date) -> str | None:
        """获取指定日期的中国节假日名称。"""
        china_holidays = self._runtime_data.get("china_holidays", [])
        next_year_holidays = self._runtime_data.get("next_year_holidays", [])
        all_holidays = china_holidays + next_year_holidays

        for holiday in all_holidays:
            try:
                holiday_date = date.fromisoformat(holiday["date"])
                if holiday_date == check_date:
                    return holiday.get("name")
            except (ValueError, KeyError):
                continue

        return None

    def get_next_interval(self, now: datetime) -> datetime:
        """计算下次更新的时间。"""
        tomorrow = dt_util.as_local(now) + timedelta(days=1)
        return dt_util.start_of_local_day(tomorrow)

    def _update_state_and_setup_listener(self) -> None:
        """更新状态并设置下次更新的监听器。"""
        now = dt_util.now()
        self.update_data(now)
        self.unsub = async_track_point_in_utc_time(
            self.hass, self.point_in_time_listener, self.get_next_interval(now)
        )

    @callback
    def point_in_time_listener(self, time_date: datetime) -> None:
        """获取最新数据并更新状态。"""
        self._update_state_and_setup_listener()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """首次设置时更新。"""
        self._update_state_and_setup_listener()

    @abstractmethod
    def update_data(self, now: datetime) -> None:
        """更新数据。"""

    def check_date(self, check_date: date) -> ServiceResponse:
        """服务：检查指定日期是否为工作日。"""
        return {"workday": self.date_is_workday(check_date)}

    def date_is_workday(self, check_date: date) -> bool:
        """检查指定日期是否为工作日。"""
        # 默认为非工作日
        is_workday = False

        # 检查是否为补班日（强制工作）
        if self.is_makeup_day(check_date):
            return True

        # 获取ISO星期几 (1 = 周一, 7 = 周日)
        adjusted_date = check_date + timedelta(days=self._days_offset)
        day = adjusted_date.isoweekday() - 1
        day_of_week = ALLOWED_DAYS[day]

        # 检查是否在工作日列表中
        if self.is_include(day_of_week, adjusted_date):
            is_workday = True

        # 检查是否在排除列表中
        if self.is_exclude(day_of_week, adjusted_date):
            is_workday = False

        return is_workday
