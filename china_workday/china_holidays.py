"""中国节假日和农历工具函数 - 在线API版本。

使用在线API获取节假日和农历数据，无需额外依赖。
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import LOGGER

# API 地址
CHINA_HOLIDAY_API = "https://timor.tech/api/holiday/year"
LUNAR_CALENDAR_API = "http://timor.tech/api/lunar/calendar"

# 缓存文件路径
CACHE_DIR = Path(".storage/china_workday")
CHINA_HOLIDAYS_CACHE = CACHE_DIR / "china_holidays_cache.json"

# 缓存更新间隔（天）
CACHE_UPDATE_INTERVAL = 30  # 30天（每月更新）


# ============================================================================
# 节假日数据获取（在线API）
# ============================================================================

async def fetch_holidays_from_api(hass: HomeAssistant, year: int) -> list[dict[str, Any]]:
    """从在线API获取节假日数据。

    Args:
        hass: Home Assistant实例
        year: 年份

    Returns:
        节假日列表
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{CHINA_HOLIDAY_API}/{year}"

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("code") == 0:
                        holiday_data = data.get("holiday", {})

                        # 第一步：收集所有休息日（排除补班日）
                        rest_days = []
                        for holiday_date, info in holiday_data.items():
                            if not isinstance(info, dict):
                                continue

                            # 检查是否为真正的休息日
                            is_holiday = info.get("holiday", False)
                            name = info.get("name", "")

                            # 排除补班日（名称包含"补班"或 holiday=false）
                            if "补班" in name or not is_holiday:
                                continue

                            # 确保日期包含年份
                            if len(holiday_date) == 5 and "-" in holiday_date:
                                holiday_date = f"{year}-{holiday_date}"

                            rest_days.append(holiday_date)

                        # 第二步：按日期排序
                        rest_days.sort()

                        # 第三步：分组连续日期并识别节假日
                        holidays = _group_and_identify_holidays(rest_days, year)

                        LOGGER.info(f"从API获取 {year} 年节假日数据，共 {len(holidays)} 个节假日")
                        return holidays

        LOGGER.warning(f"API获取 {year} 年节假日失败")
        return get_static_holidays(year)

    except Exception as err:
        LOGGER.error(f"获取节假日数据出错: {err}")
        return get_static_holidays(year)


def _group_and_identify_holidays(holiday_dates: list[str], year: int) -> list[dict[str, Any]]:
    """将连续的节假日日期分组并识别节假日名称。

    Args:
        holiday_dates: 节假日日期列表
        year: 年份

    Returns:
        节假日列表，每个包含date、name、days
    """
    if not holiday_dates:
        return []

    holidays = []
    i = 0

    while i < len(holiday_dates):
        current_date = date.fromisoformat(holiday_dates[i])
        start_date = current_date
        end_date = current_date

        # 找到连续的日期
        j = i + 1
        while j < len(holiday_dates):
            next_date = date.fromisoformat(holiday_dates[j])
            if (next_date - end_date).days == 1:
                end_date = next_date
                j += 1
            else:
                break

        # 计算这个节假日的天数
        days_count = (end_date - start_date).days + 1

        # 根据日期范围识别节假日名称
        holiday_name = _identify_holiday_by_date(start_date, end_date, year)

        holidays.append({
            "date": start_date.isoformat(),
            "name": holiday_name,
            "days": days_count
        })

        i = j  # 跳到下一组

    return holidays


def _identify_holiday_by_date(start_date: date, end_date: date, year: int) -> str:
    """根据日期范围识别节假日名称。

    Args:
        start_date: 开始日期
        end_date: 结束日期
        year: 年份

    Returns:
        节假日名称
    """
    month = start_date.month
    day = start_date.day
    days = (end_date - start_date).days + 1

    # 元旦 (1月1日，1天)
    if month == 1 and day == 1:
        return "元旦"

    # 春节 (1月底2月初，8天)
    if month == 1 or (month == 2 and day <= 15):
        if days >= 7:
            return "春节"

    # 清明节 (4月4-6日，3天)
    if month == 4 and day >= 4 and day <= 6:
        return "清明节"

    # 劳动节 (5月1日，5天)
    if month == 5 and day == 1:
        return "劳动节"

    # 端午节 (6月，3天)
    if month == 6 and days == 3:
        return "端午节"

    # 中秋节 (9月，3天)
    if month == 9 and days == 3:
        return "中秋节"

    # 国庆节 (10月1日，7天)
    if month == 10 and day == 1:
        return "国庆节"

    # 默认返回通用名称
    return "节假日"


def _get_holiday_days(holiday_name: str) -> int:
    """根据节假日名称返回天数。"""
    if "春节" in holiday_name:
        return 8
    elif "国庆" in holiday_name:
        return 7
    elif "劳动节" in holiday_name:
        return 5
    elif "清明" in holiday_name:
        return 3
    elif "端午" in holiday_name:
        return 3
    elif "中秋" in holiday_name:
        return 3
    else:
        return 1


# ============================================================================
# 静态备份数据（API失败时使用）
# ============================================================================

def get_static_holidays(year: int) -> list[dict[str, Any]]:
    """获取静态节假日数据。"""
    static_data = {
        "2024": [
            {"date": "2024-01-01", "name": "元旦", "days": 1},
            {"date": "2024-02-10", "name": "春节", "days": 8},
            {"date": "2024-04-04", "name": "清明节", "days": 3},
            {"date": "2024-05-01", "name": "劳动节", "days": 5},
            {"date": "2024-06-10", "name": "端午节", "days": 3},
            {"date": "2024-09-15", "name": "中秋节", "days": 3},
            {"date": "2024-10-01", "name": "国庆节", "days": 7},
        ],
        "2025": [
            {"date": "2025-01-01", "name": "元旦", "days": 1},
            {"date": "2025-01-28", "name": "春节", "days": 8},
            {"date": "2025-04-04", "name": "清明节", "days": 3},
            {"date": "2025-05-01", "name": "劳动节", "days": 5},
            {"date": "2025-05-31", "name": "端午节", "days": 3},
            {"date": "2025-09-06", "name": "中秋节", "days": 3},
            {"date": "2025-10-01", "name": "国庆节", "days": 7},
        ],
        "2026": [
            {"date": "2026-01-01", "name": "元旦", "days": 1},
            {"date": "2026-02-16", "name": "春节", "days": 8},
            {"date": "2026-04-05", "name": "清明节", "days": 3},
            {"date": "2026-05-01", "name": "劳动节", "days": 5},
            {"date": "2026-06-19", "name": "端午节", "days": 3},
            {"date": "2026-09-25", "name": "中秋节", "days": 3},
            {"date": "2026-10-01", "name": "国庆节", "days": 7},
        ],
    }

    return static_data.get(str(year), [])


# ============================================================================
# 农历转换（在线API）
# ============================================================================

async def lunar_to_solar_api(hass: HomeAssistant, lunar_year: int, lunar_month: int, lunar_day: int) -> date | None:
    """农历转公历（使用在线API）。

    Args:
        hass: Home Assistant实例
        lunar_year: 农历年
        lunar_month: 农历月
        lunar_day: 农历日

    Returns:
        公历日期，失败返回 None
    """
    try:
        async with aiohttp.ClientSession() as session:
            # 构建农历日期字符串
            lunar_date_str = f"{lunar_year:04d}-{lunar_month:02d}-{lunar_day:02d}"
            url = f"{LUNAR_CALENDAR_API}?d={lunar_date_str}"

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("code") == 0:
                        lunar_data = data.get("data", {})
                        solar_date_str = lunar_data.get("solar", "")

                        if solar_date_str:
                            solar_date = date.fromisoformat(solar_date_str)
                            return solar_date

        return None

    except Exception as err:
        LOGGER.error(f"农历转换出错: {err}")
        return None


async def get_lunar_date_api(hass: HomeAssistant, target_date: date) -> dict[str, Any] | None:
    """获取指定日期的农历信息（使用在线API）。

    Args:
        hass: Home Assistant实例
        target_date: 公历日期

    Returns:
        农历信息字典
    """
    try:
        async with aiohttp.ClientSession() as session:
            date_str = target_date.strftime("%Y-%m-%d")
            url = f"{LUNAR_CALENDAR_API}?d={date_str}"

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("code") == 0:
                        lunar_data = data.get("data", {})

                        return {
                            "year": lunar_data.get("lunar_year", 0),
                            "month": lunar_data.get("lunar_month", 0),
                            "day": lunar_data.get("lunar_day", 0),
                            "month_name": lunar_data.get("lunar_month_cn", ""),
                            "day_name": lunar_data.get("lunar_day_cn", ""),
                            "gz_date": lunar_data.get("gzday", ""),
                            "animal": lunar_data.get("animal", ""),
                        }

        return None

    except Exception as err:
        LOGGER.error(f"获取农历信息出错: {err}")
        return None


# ============================================================================
# 缓存管理
# ============================================================================

async def _load_cache(cache_path: Path) -> dict[str, Any] | None:
    """加载缓存文件（异步）。"""
    try:
        if cache_path.exists():
            # 在单独的线程中读取文件，避免阻塞事件循环
            import asyncio
            loop = asyncio.get_event_loop()

            def read_file():
                with open(cache_path, "r", encoding="utf-8") as f:
                    return f.read()

            content = await loop.run_in_executor(None, read_file)
            return json.loads(content)
    except Exception as err:
        LOGGER.warning(f"加载缓存文件失败: {err}")
    return None


async def _save_cache(cache_path: Path, data: dict[str, Any]) -> None:
    """保存缓存文件（异步）。"""
    try:
        def ensure_dir_and_write():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
            cache_path.write_text(json_content, encoding="utf-8")

        # 在单独的线程中创建目录和写入文件，避免阻塞事件循环
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ensure_dir_and_write)
    except Exception as err:
        LOGGER.warning(f"保存缓存文件失败: {err}")


async def get_holidays_with_cache(hass: HomeAssistant, year: int, force_refresh: bool = False) -> list[dict[str, Any]]:
    """获取节假日数据（带缓存）。

    Args:
        hass: Home Assistant实例
        year: 年份
        force_refresh: 是否强制刷新缓存

    Returns:
        节假日列表
    """
    cache_data = await _load_cache(CHINA_HOLIDAYS_CACHE)

    # 检查缓存是否有效
    if not force_refresh and cache_data and str(year) in cache_data:
        cache_time_str = cache_data.get("cache_time", "2020-01-01")
        try:
            cache_time = datetime.fromisoformat(cache_time_str)
            days_since_update = (datetime.now() - cache_time).days

            if days_since_update < CACHE_UPDATE_INTERVAL:
                LOGGER.debug(f"使用缓存的 {year} 年节假日数据（{days_since_update}天前更新）")
                return cache_data[str(year)]["holidays"]
        except Exception as err:
            LOGGER.warning(f"缓存时间解析失败: {err}")

    # 缓存无效或强制刷新，重新获取数据
    LOGGER.info(f"刷新 {year} 年节假日数据...")
    holidays = await fetch_holidays_from_api(hass, year)

    if holidays:
        # 更新缓存
        cache_data = cache_data or {}
        cache_data[str(year)] = {
            "holidays": holidays,
            "last_update": datetime.now().isoformat()
        }
        cache_data["cache_time"] = datetime.now().isoformat()

        await _save_cache(CHINA_HOLIDAYS_CACHE, cache_data)
        LOGGER.info(f"节假日缓存已更新: {len(holidays)} 个节日")

    return holidays


# ============================================================================
# 重要日期解析（支持公历+农历）
# ============================================================================

# 静态农历转换数据（2026年，备用）
STATIC_LUNAR_TO_SOLAR_2026 = {
    "01-01": "2026-02-17",  # 农历正月初一
    "02-27": "2026-04-14",  # 农历二月二十七
    "03-23": "2026-05-09",  # 农历三月二十三
}


def parse_important_dates_input(input_str: str) -> list[dict[str, str]]:
    """解析重要日期配置（支持公历和农历）。

    支持格式：
    - 公历: MM-DD=名称 或 YYYY-MM-DD=名称
    - 农历: LMM-DD=名称 或 LYYYY-MM-DD=名称

    例如:
    - 01-01=元旦
    - 05-20=生日
    - L02-27=生日（农历二月二十七）
    """
    important_dates = []

    if not input_str:
        return important_dates

    # 标准化分隔符
    normalized = input_str.replace("，", ",").replace(";", ",")

    for item in normalized.split(","):
        item = item.strip()
        if not item:
            continue

        if "=" in item:
            parts = item.split("=", 1)
            if len(parts) == 2:
                date_str, name = parts[0].strip(), parts[1].strip()

                # 判断是否为农历
                is_lunar = date_str.startswith("L")
                date_val = date_str[1:] if is_lunar else date_str

                # 验证日期格式
                if "-" in date_val:
                    parts = date_val.split("-")
                    if len(parts) in [2, 3]:
                        important_dates.append({
                            "date": date_val,
                            "name": name,
                            "type": "lunar" if is_lunar else "solar"
                        })

    return important_dates


async def calculate_next_important_date(
    hass: HomeAssistant,
    important_dates: list[dict[str, str]],
    from_date: date
) -> dict[str, Any] | None:
    """计算下一个重要日期（支持公历和农历）。

    Args:
        hass: Home Assistant实例
        important_dates: 重要日期列表
        from_date: 起始日期

    Returns:
        下一个重要日期信息
    """
    if not important_dates:
        LOGGER.warning("重要日期列表为空")
        return None

    LOGGER.info(f"计算下一个重要日期，起始日期: {from_date}，重要日期数量: {len(important_dates)}")
    for item in important_dates:
        LOGGER.info(f"  - {item['date']} ({item['type']}): {item['name']}")

    current_year = from_date.year
    candidates = []

    for item in important_dates:
        date_str = item["date"]
        date_type = item["type"]
        name = item["name"]

        target_date = None

        if date_type == "solar":
            # 公历日期
            parts = date_str.split("-")
            if len(parts) == 2:
                # MM-DD 格式
                month, day = int(parts[0]), int(parts[1])
                try:
                    target_date = date(current_year, month, day)
                    if target_date < from_date:
                        target_date = date(current_year + 1, month, day)
                except ValueError:
                    continue
            elif len(parts) == 3:
                # YYYY-MM-DD 格式
                try:
                    target_date = date.fromisoformat(date_str)
                except ValueError:
                    continue

        elif date_type == "lunar":
            # 农历日期 - 优先使用在线API转换，失败时使用静态数据
            parts = date_str.split("-")
            if len(parts) == 2:
                # LMM-DD 格式
                lunar_month, lunar_day = int(parts[0]), int(parts[1])

                # 先尝试静态数据（更可靠）
                lunar_key = f"{lunar_month:02d}-{lunar_day:02d}"
                if current_year == 2026 and lunar_key in STATIC_LUNAR_TO_SOLAR_2026:
                    try:
                        target_date = date.fromisoformat(STATIC_LUNAR_TO_SOLAR_2026[lunar_key])
                        if target_date < from_date:
                            # 已过去，尝试明年的农历（简单处理，假设明年同一天）
                            # 实际应该计算，这里暂时跳过
                            LOGGER.info(f"农历 {lunar_key} 的公历日期 {target_date} 已过去")
                            target_date = None
                    except Exception:
                        pass

                # 如果静态数据没有，尝试 API
                if not target_date:
                    for year_offset in [0, 1]:
                        try:
                            solar_date = await lunar_to_solar_api(
                                hass, current_year + year_offset, lunar_month, lunar_day
                            )
                            if solar_date and solar_date >= from_date:
                                target_date = solar_date
                                break
                        except Exception:
                            continue
            elif len(parts) == 3:
                # LYYYY-MM-DD 格式
                lunar_year, lunar_month, lunar_day = int(parts[0]), int(parts[1]), int(parts[2])
                try:
                    target_date = await lunar_to_solar_api(
                        hass, lunar_year, lunar_month, lunar_day
                    )
                    # API失败，尝试静态数据
                    if not target_date and lunar_year == 2026:
                        lunar_key = f"{lunar_month:02d}-{lunar_day:02d}"
                        if lunar_key in STATIC_LUNAR_TO_SOLAR_2026:
                            target_date = date.fromisoformat(STATIC_LUNAR_TO_SOLAR_2026[lunar_key])
                except Exception:
                    # 尝试静态数据
                    lunar_key = f"{lunar_month:02d}-{lunar_day:02d}"
                    if lunar_year == 2026 and lunar_key in STATIC_LUNAR_TO_SOLAR_2026:
                        try:
                            target_date = date.fromisoformat(STATIC_LUNAR_TO_SOLAR_2026[lunar_key])
                        except Exception:
                            continue

        if target_date and target_date >= from_date:
            days_until = (target_date - from_date).days
            candidates.append({
                "date": target_date.isoformat(),
                "name": name,
                "days_until": days_until
            })
            LOGGER.info(f"候选日期: {target_date.isoformat()} ({name}), 距今 {days_until} 天")

    # 返回最近的一个
    if candidates:
        candidates.sort(key=lambda x: x["days_until"])
        result = candidates[0]
        LOGGER.info(f"找到下一个重要日期: {result['date']} ({result['name']}), 距今 {result['days_until']} 天")
        return result

    LOGGER.warning("没有找到未来的重要日期")
    return None


# ============================================================================
# 补班日数据（从API获取 + 静态备份）
# ============================================================================

STATIC_MAKEUP_DAYS = {
    "2024": ["2024-02-04", "2024-02-18", "2024-04-07", "2024-04-28", "2024-05-11", "2024-09-14", "2024-09-29", "2024-10-12"],
    "2025": ["2025-01-26", "2025-02-08", "2025-04-06", "2025-04-27", "2025-05-04", "2025-09-28", "2025-10-11"],
    "2026": ["2026-01-04", "2026-02-14", "2026-02-28", "2026-05-09", "2026-09-20", "2026-10-10"],
}


async def fetch_makeup_days_from_api(hass: HomeAssistant, year: int) -> list[str]:
    """从API获取补班日列表。

    Args:
        hass: Home Assistant实例
        year: 年份

    Returns:
        补班日列表（YYYY-MM-DD格式）
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{CHINA_HOLIDAY_API}/{year}"

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("code") == 0:
                        holiday_data = data.get("holiday", {})
                        makeup_days = []

                        for holiday_date, info in holiday_data.items():
                            if not isinstance(info, dict):
                                continue

                            name = info.get("name", "")

                            # 检查是否为补班日（名称包含"补班"）
                            if "补班" in name:
                                # 确保日期包含年份
                                if len(holiday_date) == 5 and "-" in holiday_date:
                                    holiday_date = f"{year}-{holiday_date}"

                                makeup_days.append(holiday_date)

                        makeup_days.sort()
                        LOGGER.info(f"从API获取 {year} 年补班日数据，共 {len(makeup_days)} 个")
                        return makeup_days

        LOGGER.warning(f"API获取 {year} 年补班日失败，使用静态数据")
        return STATIC_MAKEUP_DAYS.get(str(year), [])

    except Exception as err:
        LOGGER.error(f"获取补班日数据出错: {err}")
        return STATIC_MAKEUP_DAYS.get(str(year), [])


def get_makeup_days(year: int) -> list[str]:
    """获取指定年份的补班日列表（静态数据，兼容接口）。"""
    return STATIC_MAKEUP_DAYS.get(str(year), [])


# ============================================================================
# 兼容性接口
# ============================================================================

async def get_china_holiday_data(hass: HomeAssistant, year: int) -> list[dict[str, Any]]:
    """获取指定年份的中国节假日数据列表（异步接口）。"""
    return await get_holidays_with_cache(hass, year, force_refresh=False)


async def fetch_lunar_date(hass: HomeAssistant, target_date: date) -> dict[str, Any] | None:
    """获取指定日期的农历信息（异步接口）。"""
    return await get_lunar_date_api(hass, target_date)


# ============================================================================
# 周类型计算
# ============================================================================

def calculate_week_type(check_date: date, start_date: date | None) -> str | None:
    """计算周类型（大周/小周）。"""
    if not start_date:
        return None

    days_diff = (check_date - start_date).days
    if days_diff < 0:
        return None

    weeks_diff = days_diff // 7
    return "大周" if weeks_diff % 2 == 0 else "小周"


# ============================================================================
# 工具函数
# ============================================================================

def get_next_china_holiday(
    holidays_data: list[dict[str, Any]],
    from_date: date
) -> dict[str, Any] | None:
    """获取下一个中国法定节假日。"""
    for holiday in sorted(holidays_data, key=lambda x: x["date"]):
        holiday_date = date.fromisoformat(holiday["date"])
        if holiday_date >= from_date:
            days_until = (holiday_date - from_date).days
            return {
                "name": holiday["name"],
                "date": holiday["date"],
                "days_until": days_until,
                "duration": holiday.get("days", 1)
            }

    return None
