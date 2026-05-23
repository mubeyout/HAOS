"""中国工作日传感器。"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import WorkdayConfigEntry
from .china_holidays import (
    get_china_holiday_data,
    get_makeup_days,
    parse_important_dates_input,
)
from .const import (
    CONF_ENABLE_WEEK_TYPE,
    CONF_IMPORTANT_DATES,
    CONF_WEEK_TYPE_START_DATE,
    CONF_WORKDAYS,
    CONF_EXCLUDES,
    DEFAULT_NAME,
    SENSOR_CHINA_HOLIDAY_DURATION,
    SENSOR_DAYS_UNTIL_CHINA_HOLIDAY,
    SENSOR_DAYS_UNTIL_IMPORTANT,
    SENSOR_DAYS_UNTIL_NEXT_RESTDAY,
    SENSOR_NEXT_CHINA_HOLIDAY,
    SENSOR_NEXT_CHINA_HOLIDAY_START,
    SENSOR_NEXT_IMPORTANT_DATE,
    SENSOR_NEXT_IMPORTANT_DATE_NAME,
    SENSOR_WEEK_TYPE,
    LOGGER,
)
from .entity import BaseWorkdayEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WorkdayConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """设置中国工作日传感器。"""
    sensor_name: str = entry.options.get(CONF_NAME, DEFAULT_NAME)
    entry_id = entry.entry_id

    # 获取配置
    important_dates_input = entry.options.get(CONF_IMPORTANT_DATES, "")
    important_dates = parse_important_dates_input(important_dates_input)

    enable_week_type = entry.options.get(CONF_ENABLE_WEEK_TYPE, False)
    week_type_start_date = entry.options.get(CONF_WEEK_TYPE_START_DATE)

    # 获取节假日数据
    year = dt_util.now().year
    china_holidays = await get_china_holiday_data(hass, year)
    china_holidays_next = await get_china_holiday_data(hass, year + 1)
    all_holidays = (china_holidays or []) + (china_holidays_next or [])

    # 按日期排序节假日数据
    all_holidays = sorted(all_holidays, key=lambda x: x["date"])

    # 创建所有传感器实体
    sensors = [
        # 中国法定节假日相关传感器
        NextChinaHolidaySensor(entry, entry_id, sensor_name, all_holidays),
        NextChinaHolidayStartDateSensor(entry, entry_id, sensor_name, all_holidays),
        DaysUntilChinaHolidaySensor(entry, entry_id, sensor_name, all_holidays),
        ChinaHolidayDurationSensor(entry, entry_id, sensor_name, all_holidays),

        # 周类型传感器
        WeekTypeSensor(entry, entry_id, sensor_name, enable_week_type, week_type_start_date),

        # 重要日期相关传感器
        NextImportantDateSensor(entry, entry_id, sensor_name, important_dates, hass),
        NextImportantDateNameSensor(entry, entry_id, sensor_name, important_dates, hass),
        DaysUntilImportantSensor(entry, entry_id, sensor_name, important_dates, hass),

        # 距离下个休息日传感器
        DaysUntilNextRestdaySensor(entry, entry_id, sensor_name),

        # 假期余额传感器（牛马专属）
        HolidayBalanceSensor(entry, entry_id, sensor_name),
    ]

    async_add_entities(sensors)


class ChinaHolidaySensor(BaseWorkdayEntity, SensorEntity):
    """中国法定节假日传感器基类。"""

    def __init__(
        self,
        entry: WorkdayConfigEntry,
        entry_id: str,
        name: str,
        holidays_data: list[dict[str, Any]],
    ) -> None:
        """初始化传感器。"""
        workdays = entry.options.get(CONF_WORKDAYS, [])
        excludes = entry.options.get(CONF_EXCLUDES, [])

        super().__init__(
            entry.runtime_data,
            workdays,
            excludes,
            0,
            name,
            entry_id,
        )
        self._holidays_data = holidays_data

    def _get_next_holiday(self) -> dict[str, Any] | None:
        """获取下一个节假日。"""
        if not self._holidays_data:
            return None

        today = dt_util.now().date()

        for holiday in self._holidays_data:
            try:
                holiday_date = date.fromisoformat(holiday["date"])
                if holiday_date >= today:
                    return holiday
            except (ValueError, KeyError) as err:
                LOGGER.warning(f"跳过无效节假日数据: {holiday}, 错误: {err}")
                continue

        return None


class NextChinaHolidaySensor(ChinaHolidaySensor):
    """下一个中国法定节假日名称传感器。"""

    _attr_translation_key = SENSOR_NEXT_CHINA_HOLIDAY

    def __init__(self, entry: WorkdayConfigEntry, entry_id: str, name: str, holidays_data: list[dict[str, Any]]):
        super().__init__(entry, entry_id, name, holidays_data)
        self._attr_unique_id = f"{entry_id}_{SENSOR_NEXT_CHINA_HOLIDAY}"

    def update_data(self, now: datetime) -> None:
        """更新数据。"""
        next_holiday = self._get_next_holiday()
        self._attr_native_value = next_holiday["name"] if next_holiday else "无"


class NextChinaHolidayStartDateSensor(ChinaHolidaySensor):
    """下一个中国法定节假日开始日期传感器。"""

    _attr_translation_key = SENSOR_NEXT_CHINA_HOLIDAY_START

    def __init__(self, entry: WorkdayConfigEntry, entry_id: str, name: str, holidays_data: list[dict[str, Any]]):
        super().__init__(entry, entry_id, name, holidays_data)
        self._attr_unique_id = f"{entry_id}_{SENSOR_NEXT_CHINA_HOLIDAY_START}"

    def update_data(self, now: datetime) -> None:
        """更新数据。"""
        next_holiday = self._get_next_holiday()
        self._attr_native_value = next_holiday["date"] if next_holiday else None


class DaysUntilChinaHolidaySensor(ChinaHolidaySensor):
    """距离下一个中国法定节假日天数传感器。"""

    _attr_translation_key = SENSOR_DAYS_UNTIL_CHINA_HOLIDAY
    _attr_native_unit_of_measurement = "天"

    def __init__(self, entry: WorkdayConfigEntry, entry_id: str, name: str, holidays_data: list[dict[str, Any]]):
        super().__init__(entry, entry_id, name, holidays_data)
        self._attr_unique_id = f"{entry_id}_{SENSOR_DAYS_UNTIL_CHINA_HOLIDAY}"

    def update_data(self, now: datetime) -> None:
        """更新数据。"""
        next_holiday = self._get_next_holiday()
        if next_holiday:
            holiday_date = date.fromisoformat(next_holiday["date"])
            today = now.date()
            self._attr_native_value = (holiday_date - today).days
        else:
            self._attr_native_value = None


class ChinaHolidayDurationSensor(ChinaHolidaySensor):
    """下一个中国法定节假日时长传感器。"""

    _attr_translation_key = SENSOR_CHINA_HOLIDAY_DURATION
    _attr_native_unit_of_measurement = "天"

    def __init__(self, entry: WorkdayConfigEntry, entry_id: str, name: str, holidays_data: list[dict[str, Any]]):
        super().__init__(entry, entry_id, name, holidays_data)
        self._attr_unique_id = f"{entry_id}_{SENSOR_CHINA_HOLIDAY_DURATION}"

    def update_data(self, now: datetime) -> None:
        """更新数据。"""
        next_holiday = self._get_next_holiday()
        self._attr_native_value = next_holiday.get("days", 1) if next_holiday else None


class WeekTypeSensor(BaseWorkdayEntity, SensorEntity):
    """周类型传感器（大周/小周）。"""

    _attr_translation_key = SENSOR_WEEK_TYPE

    def __init__(
        self,
        entry: WorkdayConfigEntry,
        entry_id: str,
        name: str,
        enable_week_type: bool,
        week_type_start_date: str | None,
    ) -> None:
        """初始化传感器。"""
        workdays = entry.options.get(CONF_WORKDAYS, [])
        excludes = entry.options.get(CONF_EXCLUDES, [])

        super().__init__(
            entry.runtime_data,
            workdays,
            excludes,
            0,
            name,
            entry_id,
        )

        self._enable_week_type = enable_week_type
        self._week_type_start_date = week_type_start_date

        if self._week_type_start_date:
            try:
                self._start_date = date.fromisoformat(self._week_type_start_date)
            except ValueError:
                self._start_date = None
        else:
            self._start_date = None

        self._attr_unique_id = f"{entry_id}_{SENSOR_WEEK_TYPE}"

    def update_data(self, now: datetime) -> None:
        """更新数据。"""
        if not self._enable_week_type or not self._start_date:
            self._attr_native_value = "无"
            return

        from .china_holidays import calculate_week_type

        week_type = calculate_week_type(now.date(), self._start_date)
        self._attr_native_value = week_type if week_type else "无"


class ImportantDateSensor(BaseWorkdayEntity, SensorEntity):
    """重要日期传感器基类。"""

    def __init__(
        self,
        entry: WorkdayConfigEntry,
        entry_id: str,
        name: str,
        important_dates: list[dict[str, str]],
        hass: HomeAssistant,
    ) -> None:
        """初始化传感器。"""
        workdays = entry.options.get(CONF_WORKDAYS, [])
        excludes = entry.options.get(CONF_EXCLUDES, [])

        super().__init__(
            entry.runtime_data,
            workdays,
            excludes,
            0,
            name,
            entry_id,
        )
        self._important_dates = important_dates
        self._hass = hass
        self._cached_next_date: dict[str, Any] | None = None
        self._last_update_date: date | None = None

    async def async_added_to_hass(self) -> None:
        """首次添加时计算重要日期。"""
        # 在异步上下文中预计算重要日期
        await self._precalculate_important_date()
        # 调用父类方法设置监听器
        await super().async_added_to_hass()

    async def _precalculate_important_date(self) -> None:
        """预计算下一个重要日期（异步）。"""
        if not self._important_dates:
            LOGGER.warning("重要日期列表为空，请检查配置")
            self._cached_next_date = None
            self._last_update_date = dt_util.now().date()
            return

        from .china_holidays import calculate_next_important_date

        today = dt_util.now().date()
        try:
            result = await calculate_next_important_date(self._hass, self._important_dates, today)
            self._cached_next_date = result
            self._last_update_date = today

            if result:
                LOGGER.info(f"重要日期预计算成功: {result['name']} ({result['date']}), 距今 {result['days_until']} 天")
            else:
                LOGGER.warning(f"未找到未来的重要日期: {self._important_dates}")
        except Exception as err:
            LOGGER.error(f"预计算重要日期失败: {err}")
            self._cached_next_date = None
            self._last_update_date = today

    @callback
    def point_in_time_listener(self, time_date: datetime) -> None:
        """监听时间点：每天重新计算重要日期并更新状态。"""
        # 安排异步任务重新计算
        self.hass.async_create_task(self._daily_recalculate())
        # 更新状态并设置下次监听
        self._update_state_and_setup_listener()

    async def _daily_recalculate(self) -> None:
        """每天重新计算重要日期。"""
        await self._precalculate_important_date()
        # 写入状态
        self.async_write_ha_state()

    def _get_next_important_date(self) -> dict[str, Any] | None:
        """获取下一个重要日期（同步版本，使用预计算的缓存）。"""
        if not self._important_dates:
            LOGGER.warning("重要日期列表为空，请检查配置")
            return None

        # 返回预计算的缓存
        return self._cached_next_date


class NextImportantDateSensor(ImportantDateSensor):
    """下一个重要日期传感器。"""

    _attr_translation_key = SENSOR_NEXT_IMPORTANT_DATE

    def __init__(self, entry: WorkdayConfigEntry, entry_id: str, name: str, important_dates: list[dict[str, str]], hass: HomeAssistant):
        super().__init__(entry, entry_id, name, important_dates, hass)
        self._attr_unique_id = f"{entry_id}_{SENSOR_NEXT_IMPORTANT_DATE}"

    def update_data(self, now: datetime) -> None:
        """更新数据（使用预计算的缓存）。"""
        next_date = self._get_next_important_date()
        self._attr_native_value = next_date["date"] if next_date else None


class NextImportantDateNameSensor(ImportantDateSensor):
    """下一个重要日期名称传感器。"""

    _attr_translation_key = SENSOR_NEXT_IMPORTANT_DATE_NAME

    def __init__(self, entry: WorkdayConfigEntry, entry_id: str, name: str, important_dates: list[dict[str, str]], hass: HomeAssistant):
        super().__init__(entry, entry_id, name, important_dates, hass)
        self._attr_unique_id = f"{entry_id}_{SENSOR_NEXT_IMPORTANT_DATE_NAME}"

    def update_data(self, now: datetime) -> None:
        """更新数据（使用预计算的缓存）。"""
        next_date = self._get_next_important_date()
        self._attr_native_value = next_date["name"] if next_date else "无"


class DaysUntilImportantSensor(ImportantDateSensor):
    """距离下一个重要日期天数传感器。"""

    _attr_translation_key = SENSOR_DAYS_UNTIL_IMPORTANT
    _attr_native_unit_of_measurement = "天"

    def __init__(self, entry: WorkdayConfigEntry, entry_id: str, name: str, important_dates: list[dict[str, str]], hass: HomeAssistant):
        super().__init__(entry, entry_id, name, important_dates, hass)
        self._attr_unique_id = f"{entry_id}_{SENSOR_DAYS_UNTIL_IMPORTANT}"

    def update_data(self, now: datetime) -> None:
        """更新数据（使用预计算的缓存）。"""
        next_date = self._get_next_important_date()
        self._attr_native_value = next_date["days_until"] if next_date else None


class DaysUntilNextRestdaySensor(BaseWorkdayEntity, SensorEntity):
    """距离下一个休息日天数传感器。"""

    _attr_translation_key = SENSOR_DAYS_UNTIL_NEXT_RESTDAY
    _attr_native_unit_of_measurement = "天"

    def __init__(
        self,
        entry: WorkdayConfigEntry,
        entry_id: str,
        name: str,
    ) -> None:
        """初始化传感器。"""
        workdays = entry.options.get(CONF_WORKDAYS, [])
        excludes = entry.options.get(CONF_EXCLUDES, [])

        super().__init__(
            entry.runtime_data,
            workdays,
            excludes,
            0,
            name,
            entry_id,
        )
        self._attr_unique_id = f"{entry_id}_{SENSOR_DAYS_UNTIL_NEXT_RESTDAY}"

    def update_data(self, now: datetime) -> None:
        """更新数据。"""
        # 查找下一个休息日
        check_date = now.date() + timedelta(days=1)
        days_until = 1

        while days_until <= 365:  # 最多查找一年
            if not self.date_is_workday(check_date):
                self._attr_native_value = days_until
                return
            check_date += timedelta(days=1)
            days_until += 1

        self._attr_native_value = None


class HolidayBalanceSensor(BaseWorkdayEntity, SensorEntity):
    """假期余额传感器 - 牛马专属！"""

    def __init__(
        self,
        entry: WorkdayConfigEntry,
        entry_id: str,
        name: str,
    ) -> None:
        """初始化传感器。"""
        workdays = entry.options.get(CONF_WORKDAYS, [])
        excludes = entry.options.get(CONF_EXCLUDES, [])

        super().__init__(
            entry.runtime_data,
            workdays,
            excludes,
            0,
            name,
            entry_id,
        )
        self._attr_unique_id = f"{entry_id}_holiday_balance"
        self._attr_translation_key = "holiday_balance"

    def update_data(self, now: datetime) -> None:
        """更新数据。"""
        today = now.date()

        # 判断今天是否为工作日
        is_today_workday = self.date_is_workday(today)

        if is_today_workday:
            # 工作日：检查明天是否开始休息
            tomorrow = today + timedelta(days=1)
            if not self.date_is_workday(tomorrow):
                # 明天开始休息，计算连续休息天数
                rest_days_count = 0
                check_date = tomorrow

                while rest_days_count <= 365:
                    if self.date_is_workday(check_date):
                        break
                    rest_days_count += 1
                    check_date += timedelta(days=1)

                # 如果明天开始休息且连续≥2天
                if rest_days_count >= 2:
                    self._attr_native_value = "明天开始浪！"
                else:
                    # 明天休息但只有1天
                    self._attr_native_value = "好消息:明天休息，坏消息:只有一天！"
            else:
                # 明天也是工作日
                self._attr_native_value = "想什么呢！继续搬砖"
        else:
            # 休息日：计算剩余休息天数
            check_date = today + timedelta(days=1)
            rest_days_count = 0

            # 计算从明天开始的连续休息日天数
            while rest_days_count <= 365:
                if self.date_is_workday(check_date):
                    # 找到下一个工作日，停止计数
                    break
                rest_days_count += 1
                check_date += timedelta(days=1)

            # 根据剩余休息天数显示不同消息
            if rest_days_count == 0:
                # 明天就是工作日（剩余0天休息日）
                self._attr_native_value = "牛马明天回笼！"
            elif rest_days_count >= 3:
                # 余额充足（≥3天）
                self._attr_native_value = f"显示余额（{rest_days_count}天）充足，继续浪！"
            elif rest_days_count == 1:
                # 余额不足（1天）
                self._attr_native_value = f"显示余额（{rest_days_count}天）不足不能浪了"
            else:
                # 其他情况（如2天或超过一年）
                self._attr_native_value = f"还有{rest_days_count}天又要搬砖了！"
