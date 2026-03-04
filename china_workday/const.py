"""Add constants for Workday integration."""

from __future__ import annotations

import logging

from homeassistant.const import WEEKDAYS, Platform

LOGGER = logging.getLogger(__package__)

ALLOWED_DAYS = [*WEEKDAYS, "holiday", "makeup_day"]

DOMAIN = "china_workday"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

CONF_WORKDAYS = "workdays"
CONF_EXCLUDES = "excludes"
CONF_ADD_HOLIDAYS = "add_holidays"
CONF_REMOVE_HOLIDAYS = "remove_holidays"

# 新增配置项
CONF_ENABLE_WEEK_TYPE = "enable_week_type"
CONF_WEEK_TYPE_START_DATE = "week_type_start_date"
CONF_IMPORTANT_DATES = "important_dates"

# By default, Monday - Friday are workdays
DEFAULT_WORKDAYS = ["mon", "tue", "wed", "thu", "fri"]
# By default, public holidays, Saturdays and Sundays are excluded from workdays
DEFAULT_EXCLUDES = ["sat", "sun", "holiday"]
DEFAULT_NAME = "牛马日历"

# 传感器唯一ID后缀
SENSOR_WORKDAY = "workday"
SENSOR_RESTDAY = "restday"
SENSOR_NEXT_CHINA_HOLIDAY = "next_china_holiday"
SENSOR_NEXT_CHINA_HOLIDAY_START = "next_china_holiday_start"
SENSOR_DAYS_UNTIL_CHINA_HOLIDAY = "days_until_china_holiday"
SENSOR_CHINA_HOLIDAY_DURATION = "china_holiday_duration"
SENSOR_WEEK_TYPE = "week_type"
SENSOR_NEXT_IMPORTANT_DATE = "next_important_date"
SENSOR_NEXT_IMPORTANT_DATE_NAME = "next_important_date_name"
SENSOR_DAYS_UNTIL_IMPORTANT = "days_until_important"
SENSOR_DAYS_UNTIL_NEXT_RESTDAY = "days_until_next_restday"
