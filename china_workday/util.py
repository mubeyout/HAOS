"""中国工作日集成辅助函数。"""

from __future__ import annotations

from datetime import date, timedelta

from homeassistant.util import dt as dt_util

from .const import LOGGER


def validate_dates(holiday_list: list[str] | str) -> list[str]:
    """验证并处理添加/移除的日期列表。"""
    if isinstance(holiday_list, str):
        if not holiday_list:
            return []
        holiday_list = holiday_list.split(",")

    calc_holidays: list[str] = []
    for add_date in holiday_list:
        if not add_date:
            continue

        # 处理日期范围（逗号分隔）
        if add_date.find(",") > 0:
            dates = add_date.split(",", maxsplit=1)
            d1 = dt_util.parse_date(dates[0])
            d2 = dt_util.parse_date(dates[1])
            if d1 is None or d2 is None:
                LOGGER.error("日期范围格式错误: %s", add_date)
                continue
            _range: timedelta = d2 - d1
            for i in range(_range.days + 1):
                day: date = d1 + timedelta(days=i)
                calc_holidays.append(day.strftime("%Y-%m-%d"))
            continue

        # 单个日期
        calc_holidays.append(add_date)

    return calc_holidays
