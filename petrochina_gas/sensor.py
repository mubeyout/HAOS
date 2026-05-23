"""Sensors for Kunming Gas integration.

包含以下传感器类型：
1. 表端余额 (balance)
2. 所属燃气公司 (gas_company)
3. 户号 (user_code)
4. 用户名 (customer_name)
5. 地址 (address)
6. 最近表读数 (meter_reading)
7. 最近通讯时间 (last_communication)
8. 待上表金额 (owe_amount)
9. 上次缴费金额 (last_payment)
10. 上次缴费时间 (last_payment_date)
11. 上月用气量 (monthly_volume)
12. 上月用气金额 (monthly_cost)
13. 本月用气量 (current_month_volume)
14. 本月用气金额 (current_month_cost)
15. 近31天累计用量 (recent_monthly_usage)
16. 近31天用气费用 (recent_monthly_cost)
17. 最近一日用气量 (last_day_usage)
18. 最近一日用气时间 (last_day_usage_time)
19. 今年用气量 (yearly_volume)
20. 今年用气金额 (yearly_cost)
21. 当前阶梯 (ladder_stage)
22. 当前阶梯单价 (ladder_unit_price)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict, List

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    CONF_USER_CODE,
    CONF_CID,
    CONF_TERMINAL_TYPE,
    CONF_ACCOUNTS,
    CONF_SETTINGS,
    CONF_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_MDM_CODE,
    CONF_OPEN_ID,
    CONF_UNION_ID,
    CONF_MOBILE,
    CONF_PASSWORD,
    CONF_COMPANY_ID,
    SUFFIX_BAL,
    SUFFIX_ADDRESS,
    SUFFIX_LADDER_STAGE,
    SUFFIX_MONTHLY_VOLUME,
    SUFFIX_MONTHLY_COST,
    SUFFIX_YEARLY_VOLUME,
    SUFFIX_YEARLY_COST,
    SUFFIX_LAST_PAYMENT,
    SUFFIX_LAST_PAYMENT_DATE,
    SUFFIX_OWE_AMOUNT,
    SUFFIX_METER_READING,
    SUFFIX_LAST_COMMUNICATION,
    SUFFIX_CURRENT_MONTH_COST,
    SUFFIX_CURRENT_MONTH_VOLUME,
    SUFFIX_LAST_DAY_USAGE,
    SUFFIX_LAST_DAY_USAGE_TIME,
    SUFFIX_LAST_DAY_USAGE_COST,
    SUFFIX_RECENT_MONTHLY_COST,
    SUFFIX_RECENT_MONTHLY_USAGE,
    ATTR_KEY_LAST_UPDATE,
    ATTR_KEY_CUSTOMER_NAME,
    ATTR_KEY_ADDRESS,
    ATTR_KEY_ACCOUNT_ID,
    ATTR_KEY_METER_TYPE,
    ATTR_KEY_LADDER_STAGE,
    ATTR_KEY_LADDER_UNIT_PRICE,
    ATTR_KEY_LAST_PAYMENT_DATE,
    ATTR_KEY_LAST_PAYMENT_AMOUNT,
    DATA_TOTAL_GAS_VOLUME,
)
from .gas_client import GasHttpClient

_LOGGER = logging.getLogger(__name__)


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """解析时间字符串为 datetime 对象（带时区）"""
    if not datetime_str or datetime_str == "未知":
        return None

    # 尝试解析多种时间格式
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",  # Date only format for payment records
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            # 添加本地时区信息（中国时区 UTC+8）
            return dt.replace(tzinfo=timezone(timedelta(hours=8)))
        except (ValueError, TypeError):
            continue

    _LOGGER.debug(f"Failed to parse datetime: {datetime_str}")
    return None


def format_date_cn(dt: Optional[datetime]) -> str:
    """格式化日期为中文格式（如：2026年1月2日）"""
    if not dt:
        return ""
    return f"{dt.year}年{dt.month}月{dt.day}日"


def format_datetime_cn(dt: Optional[datetime]) -> str:
    """格式化日期时间为中文格式（如：2026年2月14日 01:28）"""
    if not dt:
        return ""
    return f"{dt.year}年{dt.month}月{dt.day}日 {dt.hour:02d}:{dt.minute:02d}"


def calculate_cost_by_ladder(
    volume: float,
    ladder_config: list[dict]
) -> tuple[int, float, float]:
    """
    根据用量和阶梯配置计算费用（分段累加）

    阶梯计费逻辑：
    - 第1阶梯(0-360m³): 前360m³按2.97元/m³
    - 第2阶梯(360-540m³): 超出360的部分按3.56元/m³
    - 第3阶梯(540m³以上): 超出540的部分按4.46元/m³

    例如：400m³的费用 = 360×2.97 + (400-360)×3.56

    参数:
        volume: 用气量 (m³)
        ladder_config: 阶梯配置列表 [{"start": 0, "end": 360, "price": 2.97}, ...]

    返回:
        (当前阶梯级别, 当前阶梯单价, 总费用)
    """
    if not ladder_config or volume == 0:
        return 1, 0, 0

    total_cost = 0
    remaining_volume = volume
    current_stage = 0
    current_price = 0

    for ladder in ladder_config:
        start = ladder.get("start", 0)
        end = ladder.get("end", float("inf"))
        price = ladder.get("price", 0)

        # 计算当前阶梯的可用量
        ladder_volume = end - start

        if remaining_volume <= ladder_volume:
            # 用量完全在当前阶梯内
            total_cost += remaining_volume * price
            current_stage = ladder_config.index(ladder) + 1
            current_price = price
            break
        else:
            # 用量超出当前阶梯，计满当前阶梯后继续
            total_cost += ladder_volume * price
            remaining_volume -= ladder_volume
            current_stage = ladder_config.index(ladder) + 1
            current_price = price

    return (current_stage, current_price, round(total_cost, 2))


# ============================================
# Base Sensor Class
# ============================================

class GasBaseSensor(CoordinatorEntity, SensorEntity):
    """昆仑燃气传感器基类"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
        entity_suffix: str,
    ) -> None:
        """初始化传感器"""
        SensorEntity.__init__(self)
        CoordinatorEntity.__init__(self, coordinator)
        self._account_number = account_number
        self._entity_suffix = entity_suffix
        self._attr_extra_state_attributes = {}
        self._attr_available = False

    @property
    def unique_id(self) -> str:
        """返回唯一ID"""
        return f"{DOMAIN}.{self._account_number}.{self._entity_suffix}"

    @property
    def name(self) -> str | None:
        """返回传感器名称"""
        return f"{self._account_number}-{self._entity_suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息"""
        return DeviceInfo(
            identifiers={(DOMAIN, self._account_number)},
            name=f"GasAccount-{self._account_number}",
            manufacturer="Kunming Gas",
            model="Virtual Gas Meter",
        )

    @property
    def should_poll(self) -> bool:
        """默认不轮询"""
        return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """处理协调器更新"""
        try:
            account_data = self.coordinator.data.get(self._account_number)
        except AttributeError:
            _LOGGER.warning("%s coordinator not available", self.unique_id)
            self._attr_available = False
            self.async_write_ha_state()
            return

        if account_data is None:
            _LOGGER.warning("%s not found in coordinator data", self.unique_id)
            self._attr_available = False
            self.async_write_ha_state()
            return

        new_native_value = account_data.get(self._entity_suffix)
        if new_native_value is None:
            _LOGGER.debug("%s data not found in coordinator data", self.unique_id)
            self._attr_available = False
            self.async_write_ha_state()
            return

        if new_native_value == STATE_UNAVAILABLE:
            _LOGGER.debug("%s data is unavailable", self.unique_id)
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_native_value = new_native_value
        self._attr_available = True
        self.async_write_ha_state()


# ============================================
# Sensor Classes
# ============================================

class GasBalanceSensor(GasBaseSensor):
    """表端余额传感器"""
    _attr_icon = "mdi:currency-cny"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_BAL)
        # 货币单位：使用 native_unit_of_measurement，Home Assistant 会根据 device_class 自动处理显示
        self._attr_native_unit_of_measurement = "CNY"


class GasCustomerInfoSensor(GasBaseSensor):
    """所属燃气公司传感器"""
    _attr_icon = "mdi:office-building"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "gas_company")
        self._attr_extra_state_attributes = {
            "company_name": "云南中石油昆仑燃气有限公司昆明分公司",
            "company_type": "天然气",
        }


class GasUserCodeSensor(GasBaseSensor):
    """户号传感器"""
    _attr_icon = "mdi:numeric"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "user_code")


class GasUserNameSensor(GasBaseSensor):
    """用户名传感器"""
    _attr_icon = "mdi:account-circle"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "customer_name")


class GasAddressSensor(GasBaseSensor):
    """地址传感器"""
    _attr_icon = "mdi:map-marker"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_ADDRESS)


class GasMeterReadingSensor(GasBaseSensor):
    """最近表读数传感器"""
    _attr_icon = "mdi:gauge"
    _attr_device_class = SensorDeviceClass.GAS

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_METER_READING)
        self._attr_native_unit_of_measurement = "m³"


class GasLastCommunicationSensor(GasBaseSensor):
    """最近通讯时间传感器"""
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_LAST_COMMUNICATION)


class GasOweAmountSensor(GasBaseSensor):
    """待上表金额传感器"""
    _attr_icon = "mdi:cash-clock"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_OWE_AMOUNT)
        self._attr_native_unit_of_measurement = "CNY"


class GasLastPaymentSensor(GasBaseSensor):
    """上次缴费金额传感器"""
    _attr_icon = "mdi:receipt"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_LAST_PAYMENT)
        self._attr_native_unit_of_measurement = "CNY"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """返回额外的状态属性"""
        value = self.native_value
        if isinstance(value, (int, float)):
            # 安全访问 coordinator.data
            try:
                date_value = self.coordinator.data.get(self._account_number, {}).get(ATTR_KEY_LAST_PAYMENT_DATE, "未知")
            except (AttributeError, KeyError):
                date_value = "未知"
            return {
                ATTR_KEY_LAST_PAYMENT_DATE: date_value,
            }
        return {}


class GasLastPaymentDateSensor(GasBaseSensor):
    """上次缴费时间传感器"""
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_LAST_PAYMENT_DATE)

    @property
    def native_value(self) -> Optional[datetime]:
        """返回解析后的日期时间对象"""
        try:
            date_str = self.coordinator.data.get(self._account_number, {}).get(SUFFIX_LAST_PAYMENT_DATE)
            return parse_datetime(date_str) if date_str else None
        except AttributeError:
            return None


class GasMonthlyVolumeSensor(GasBaseSensor):
    """上月用气量传感器"""
    _attr_icon = "mdi:calendar-month"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_MONTHLY_VOLUME)
        self._attr_native_unit_of_measurement = "m³"


class GasMonthlyCostSensor(GasBaseSensor):
    """上月用气费用传感器"""
    _attr_icon = "mdi:currency-cny"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_MONTHLY_COST)
        self._attr_native_unit_of_measurement = "CNY"


class CurrentMonthCostSensor(GasBaseSensor):
    """本月用气费用传感器"""
    _attr_icon = "mdi:calendar-check"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_CURRENT_MONTH_COST)
        self._attr_native_unit_of_measurement = "CNY"


class CurrentMonthVolumeSensor(GasBaseSensor):
    """本月用气量传感器"""
    _attr_icon = "mdi:calendar-check"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_CURRENT_MONTH_VOLUME)
        self._attr_native_unit_of_measurement = "m³"


class RecentMonthlyUsageSensor(GasBaseSensor):
    """近31天累计用量传感器"""
    _attr_icon = "mdi:chart-line"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_RECENT_MONTHLY_USAGE)
        self._attr_native_unit_of_measurement = "m³"


class LastDayUsageSensor(GasBaseSensor):
    """最近一日用气量传感器"""
    _attr_icon = "mdi:calendar-today"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_LAST_DAY_USAGE)
        self._attr_native_unit_of_measurement = "m³"


class LastDayUsageTimeSensor(GasBaseSensor):
    """最近一日用气时间传感器"""
    _attr_icon = "mdi:clock"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_LAST_DAY_USAGE_TIME)


class LastDayUsageCostSensor(GasBaseSensor):
    """最近一日用气费用传感器"""
    _attr_icon = "mdi:cash"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "last_day_usage_cost")
        self._attr_native_unit_of_measurement = "CNY"


class RecentMonthlyCostSensor(GasBaseSensor):
    """近31天用气费用传感器"""
    _attr_icon = "mdi:calendar-today"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_RECENT_MONTHLY_COST)
        self._attr_native_unit_of_measurement = "CNY"


class YearlyVolumeSensor(GasBaseSensor):
    """今年用气量传感器"""
    _attr_icon = "mdi:chart-bar"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_YEARLY_VOLUME)
        self._attr_native_unit_of_measurement = "m³"


class YearlyCostSensor(GasBaseSensor):
    """今年用气费用传感器"""
    _attr_icon = "mdi:cash-multiple"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_YEARLY_COST)
        self._attr_native_unit_of_measurement = "CNY"


class LadderStageSensor(GasBaseSensor):
    """当前阶梯传感器"""
    _attr_icon = "mdi:stairs"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, ATTR_KEY_LADDER_STAGE)


class LadderUnitPriceSensor(GasBaseSensor):
    """当前阶梯单价传感器"""
    _attr_icon = "mdi:tag"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, ATTR_KEY_LADDER_UNIT_PRICE)
        self._attr_native_unit_of_measurement = "CNY/m³"


# ============================================
# Coordinator
# ============================================

class GasCoordinator(DataUpdateCoordinator):
    """昆仑燃气数据协调器"""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """初始化协调器"""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),  # 每小时更新一次
        )
        self._config_entry = config_entry
        self._config = config_entry.data
        self.data: Dict[str, Any] = {}

        # 存储每个账户的 HTTP 客户端
        self._clients: Dict[str, GasHttpClient] = {}
        # 标记是否已登录
        self._logged_in: Dict[str, bool] = {}
        # 首次刷新标记（用于快速返回基础数据）
        self._first_refresh_done = False

    async def _get_or_create_client(self, user_code: str, cid: int, terminal_type: int) -> GasHttpClient:
        """获取或创建HTTP客户端"""
        if user_code not in self._clients:
            self._clients[user_code] = GasHttpClient(
                user_code=user_code,
                cid=cid,
                terminal_type=terminal_type
            )
            self._logged_in[user_code] = False

        # 从配置中读取认证信息并设置
        settings = self._config.get(CONF_SETTINGS, {})
        account_config = self._config.get(CONF_ACCOUNTS, {}).get(user_code, {})

        # 优先使用账户级别的认证信息，其次使用全局设置
        mobile = account_config.get(CONF_MOBILE) or settings.get(CONF_MOBILE)
        password = account_config.get(CONF_PASSWORD) or settings.get(CONF_PASSWORD)
        company_id = account_config.get(CONF_COMPANY_ID) or settings.get(CONF_COMPANY_ID)

        # 调试日志：检查认证信息
        _LOGGER.debug(f"Config for {user_code}: mobile={bool(mobile)}, password_set={bool(password)}, company_id={company_id}")

        client = self._clients[user_code]

        # 如果有手机号和密码，尝试自动登录
        if mobile and password:
            # 检查是否已登录且token仍然有效
            if self._logged_in.get(user_code, False) and client._token:
                _LOGGER.debug(f"Already logged in for {user_code}, skipping login")
            else:
                try:
                    _LOGGER.info(f"🔐 Attempting password login for {user_code} with {mobile}")
                    success = await self.hass.async_add_executor_job(
                        client.password_login,
                        mobile,
                        password,
                        company_id
                    )
                    if success:
                        self._logged_in[user_code] = True
                        _LOGGER.info(f"✅ Password login successful for {user_code}")
                    else:
                        _LOGGER.warning(f"⚠️  Password login failed for {user_code}")
                        self._logged_in[user_code] = False
                except Exception as err:
                    _LOGGER.warning(f"⚠️  Password login error for {user_code}: {err}")
                    self._logged_in[user_code] = False
        else:
            _LOGGER.warning(f"⚠️  No mobile/password found for {user_code}, using public API only")
            self._logged_in[user_code] = False

        return client

    async def _async_login_if_needed(self, user_code: str, client: GasHttpClient) -> bool:
        """如果需要，执行登录"""
        if self._logged_in.get(user_code, False):
            return True

        settings = self._config.get(CONF_SETTINGS, {})
        wechat_code = settings.get("wechat_code", "")
        union_id = settings.get("union_id", "")

        # 如果没有提供微信授权码，跳过登录
        if not wechat_code:
            _LOGGER.info(f"No WeChat code provided for {user_code}, using public API only")
            return False

        # 执行登录
        try:
            _LOGGER.info(f"Attempting WeChat login for {user_code}")
            success = await self.hass.async_add_executor_job(
                client.login,
                wechat_code,
                union_id
            )

            if success:
                self._logged_in[user_code] = True
                _LOGGER.info(f"Login successful for {user_code}")
                return True
            else:
                _LOGGER.error(f"Login failed for {user_code}")
                return False

        except Exception as err:
            _LOGGER.error(f"Login error for {user_code}: {err}")
            return False

    async def _async_refresh_account_data(self, user_code: str, cid: int, terminal_type: int) -> dict:
        """刷新单个账户的所有数据"""
        client = await self._get_or_create_client(user_code, cid, terminal_type)
        account_data = {}

        # 定义一个辅助函数来执行API调用，处理403错误
        async def call_with_relogin(func, *args, **kwargs):
            """执行API调用，如果403则尝试重新登录"""
            max_retries = 1  # 最多重试1次（重新登录后重试）

            for attempt in range(max_retries + 1):
                try:
                    result = await self.hass.async_add_executor_job(func, *args, **kwargs)
                    return result
                except Exception as err:
                    error_str = str(err)
                    # 检测403错误
                    if "403" in error_str and attempt < max_retries:
                        _LOGGER.warning(f"⚠️  Got 403 for {user_code}, attempting to re-login...")

                        # 尝试重新登录
                        settings = self._config.get(CONF_SETTINGS, {})
                        account_config = self._config.get(CONF_ACCOUNTS, {}).get(user_code, {})
                        mobile = account_config.get(CONF_MOBILE) or settings.get(CONF_MOBILE)
                        password = account_config.get(CONF_PASSWORD) or settings.get(CONF_PASSWORD)
                        company_id = account_config.get(CONF_COMPANY_ID) or settings.get(CONF_COMPANY_ID)

                        if mobile and password:
                            try:
                                success = await self.hass.async_add_executor_job(
                                    client.password_login,
                                    mobile,
                                    password,
                                    company_id
                                )
                                if success:
                                    _LOGGER.info(f"✅ Re-login successful for {user_code}, retrying request...")
                                    continue  # 重试请求
                            except Exception as login_err:
                                _LOGGER.error(f"❌ Re-login failed for {user_code}: {login_err}")

                    # 如果重新登录失败或没有凭证，返回错误
                    _LOGGER.error(f"Error calling API for {user_code}: {err}")
                    raise

        # 1. 获取基础数据（公开API，无需认证）
        try:
            user_debt = await call_with_relogin(client.get_user_debt)
            if user_debt:
                account_data.update({
                    SUFFIX_BAL: user_debt.remote_meter_balance,
                    "customer_name": user_debt.customer_name,
                    SUFFIX_ADDRESS: user_debt.address,
                    "account_id": user_debt.account_id,
                    SUFFIX_METER_READING: user_debt.reading_last_time,
                    SUFFIX_LAST_COMMUNICATION: parse_datetime(user_debt.remote_meter_last_communication_time),
                    "meter_type": user_debt.meter_type,
                    "mdm_code": user_debt.mdm_code,
                    "user_code": user_debt.user_code,
                    "gas_company": "云南中石油昆仑燃气有限公司昆明分公司",
                })
                if user_debt.mdm_code:
                    client._mdm_code = user_debt.mdm_code
                    _LOGGER.info(f"Got mdm_code from API: {user_debt.mdm_code}")
        except Exception as err:
            _LOGGER.error(f"Error getting user debt for {user_code}: {err}")

        # 2. 如果已登录，获取认证后的数据
        has_auth = hasattr(client, '_token') and client._token and client._mdm_code
        _LOGGER.info(f"Checking auth for {user_code}: has_token={bool(client._token)}, has_mdm={bool(client._mdm_code)}")

        if has_auth:
            # 获取缴费记录
            try:
                _LOGGER.info(f"Fetching payment records for {user_code}...")
                payment_records = await call_with_relogin(
                    client.get_payment_records,
                    1,  # page
                    10  # page_size
                )

                _LOGGER.debug(f"Payment records response: {payment_records}")

                if payment_records and "error" in payment_records:
                    _LOGGER.warning(f"Payment records API error: {payment_records['error']}")
                    account_data.update({
                        SUFFIX_LAST_PAYMENT: 0,
                        ATTR_KEY_LAST_PAYMENT_DATE: "认证失败",
                        SUFFIX_OWE_AMOUNT: 0,
                    })
                elif payment_records and "recordsInfoList" in payment_records:
                    records = payment_records["recordsInfoList"]
                    if records:
                        last_payment = records[0]
                        account_data.update({
                            SUFFIX_LAST_PAYMENT: float(last_payment.get('payAmount', 0)),
                            ATTR_KEY_LAST_PAYMENT_DATE: last_payment.get('operationDate', ''),
                            SUFFIX_OWE_AMOUNT: float(last_payment.get('oweAmount', 0)),
                        })
                    else:
                        account_data.update({
                            SUFFIX_LAST_PAYMENT: 0,
                            ATTR_KEY_LAST_PAYMENT_DATE: "无缴费记录",
                            SUFFIX_OWE_AMOUNT: 0,
                        })
            except Exception as err:
                _LOGGER.error(f"Error getting payment records for {user_code}: {err}")
                account_data.update({
                    SUFFIX_LAST_PAYMENT: 0,
                    ATTR_KEY_LAST_PAYMENT_DATE: "获取失败",
                    SUFFIX_OWE_AMOUNT: 0,
                })

            # 获取月度用量（包含阶梯价格信息）
            try:
                monthly_data = await call_with_relogin(
                    client.get_monthly_usage,
                    1,  # page
                    7   # page_size (7 months)
                )

                if monthly_data and "error" not in monthly_data:
                    # 解析阶梯价格配置
                    rate_items = monthly_data.get("rateItemInfo", [])

                    # 构建阶梯配置列表
                    ladder_config = []
                    for item in rate_items:
                        ladder_config.append({
                            "start": float(item.get("beginVolume", 0)),
                            "end": float(item.get("endVolume", float("inf"))),
                            "price": float(item.get("price", 0)),
                        })

                    # 解析月度用量记录
                    records = monthly_data.get("recordsInfo", [])

                    # 直接从API获取本年累计用量（阶梯信息中的实时数据）
                    yearly_volume = float(monthly_data.get(DATA_TOTAL_GAS_VOLUME, 0))

                    if len(records) >= 2:
                        # 获取数据
                        last_month = records[-2]  # 上月
                        current_month = records[-1]  # 当前月

                        last_month_volume = float(last_month.get("gasVolume", 0))
                        current_month_volume = float(current_month.get("gasVolume", 0))

                        # 计算费用：使用用量和阶梯配置计算
                        _, _, last_month_cost = calculate_cost_by_ladder(last_month_volume, ladder_config)
                        _, _, current_month_cost_calc = calculate_cost_by_ladder(current_month_volume, ladder_config)

                        account_data.update({
                            SUFFIX_MONTHLY_VOLUME: last_month_volume,
                            SUFFIX_MONTHLY_COST: last_month_cost,  # 使用计算值而非API返回值
                            SUFFIX_CURRENT_MONTH_VOLUME: current_month_volume,  # 本月用量
                            SUFFIX_CURRENT_MONTH_COST: current_month_cost_calc,  # 使用计算值
                        })

                        # 使用计算函数确定当前阶梯和费用
                        current_ladder, ladder_unit_price, yearly_cost_calc = calculate_cost_by_ladder(yearly_volume, ladder_config)

                        account_data.update({
                            SUFFIX_YEARLY_VOLUME: yearly_volume,
                            SUFFIX_YEARLY_COST: yearly_cost_calc,  # 使用计算值
                            ATTR_KEY_LADDER_STAGE: current_ladder,
                            ATTR_KEY_LADDER_UNIT_PRICE: ladder_unit_price,
                        })
                    elif len(records) == 1:
                        # 只有一个月的数据
                        current_month = records[0]
                        current_month_volume = float(current_month.get("gasVolume", 0))
                        _, _, current_month_cost = calculate_cost_by_ladder(current_month_volume, ladder_config)

                        account_data.update({
                            SUFFIX_MONTHLY_VOLUME: 0,
                            SUFFIX_MONTHLY_COST: 0,
                            SUFFIX_CURRENT_MONTH_COST: current_month_cost,
                            SUFFIX_YEARLY_VOLUME: current_month_volume,
                            SUFFIX_YEARLY_COST: current_month_cost,
                            ATTR_KEY_LADDER_STAGE: 1,
                            ATTR_KEY_LADDER_UNIT_PRICE: ladder_config[0]["price"],
                        })
                    else:
                        account_data.update({
                            SUFFIX_MONTHLY_VOLUME: 0,
                            SUFFIX_MONTHLY_COST: 0,
                            SUFFIX_CURRENT_MONTH_COST: 0,
                            SUFFIX_YEARLY_VOLUME: 0,
                            SUFFIX_YEARLY_COST: 0,
                            ATTR_KEY_LADDER_STAGE: 1,
                            ATTR_KEY_LADDER_UNIT_PRICE: 0,
                        })

            except Exception as err:
                _LOGGER.error(f"Error getting monthly usage for {user_code}: {err}")
                account_data.update({
                    SUFFIX_MONTHLY_VOLUME: 0,
                    SUFFIX_MONTHLY_COST: 0,
                    SUFFIX_CURRENT_MONTH_VOLUME: 0,
                    SUFFIX_CURRENT_MONTH_COST: 0,
                    SUFFIX_YEARLY_VOLUME: 0,
                    SUFFIX_YEARLY_COST: 0,
                    ATTR_KEY_LADDER_STAGE: 1,
                    ATTR_KEY_LADDER_UNIT_PRICE: 0,
                })

            # 获取每日用量（用于last_day_usage和recent_usage）
            try:
                daily_usage = await call_with_relogin(
                    client.get_daily_usage,
                    31  # 31 days
                )

                _LOGGER.debug(f"Daily usage response for {user_code}: {daily_usage}")

                if daily_usage and "daily_volumes" in daily_usage:
                    daily_volumes = daily_usage["daily_volumes"]
                    _LOGGER.info(f"✅ Got {len(daily_volumes)} daily records for {user_code}")

                    if daily_volumes:
                        # 最近一天数据 (索引0是最新的)
                        last_day = daily_volumes[0]
                        last_day_volume = last_day.get("volume", 0)
                        last_day_reading = last_day.get("reading", 0)  # 表读数

                        account_data.update({
                            SUFFIX_LAST_DAY_USAGE: last_day_volume,
                            SUFFIX_LAST_DAY_USAGE_TIME: last_day.get("date", ""),
                            SUFFIX_METER_READING: last_day_reading,  # 更新表读数为最新值
                        })

                        # 计算近31天累计用量和费用
                        recent_monthly_volume = sum(d.get("volume", 0) for d in daily_volumes)

                        # 获取当前阶梯单价用于计算费用
                        ladder_unit_price = account_data.get(ATTR_KEY_LADDER_UNIT_PRICE, 0)

                        # 新增：计算最近一日用气费用
                        last_day_cost = round(last_day_volume * ladder_unit_price, 2)

                        recent_monthly_cost = round(recent_monthly_volume * ladder_unit_price, 2)

                        account_data.update({
                            SUFFIX_RECENT_MONTHLY_USAGE: recent_monthly_volume,  # 近31天累计
                            SUFFIX_RECENT_MONTHLY_COST: recent_monthly_cost,  # 近31天费用
                            SUFFIX_LAST_DAY_USAGE_COST: last_day_cost,  # 最近一日费用（新增）
                        })
                    else:
                        account_data.update({
                            SUFFIX_LAST_DAY_USAGE: 0,
                            SUFFIX_LAST_DAY_USAGE_TIME: "",
                            SUFFIX_RECENT_MONTHLY_USAGE: 0,
                            SUFFIX_RECENT_MONTHLY_COST: 0,
                            SUFFIX_LAST_DAY_USAGE_COST: 0,  # 最近一日费用（新增）
                        })
                else:
                    account_data.update({
                        SUFFIX_LAST_DAY_USAGE: 0,
                        SUFFIX_LAST_DAY_USAGE_TIME: "",
                        SUFFIX_RECENT_MONTHLY_USAGE: 0,
                        SUFFIX_RECENT_MONTHLY_COST: 0,
                        SUFFIX_LAST_DAY_USAGE_COST: 0,  # 最近一日费用（新增）
                    })
            except Exception as err:
                _LOGGER.error(f"Error getting daily usage for {user_code}: {err}")
                account_data.update({
                    SUFFIX_LAST_DAY_USAGE: 0,
                    SUFFIX_LAST_DAY_USAGE_TIME: "",
                    SUFFIX_RECENT_MONTHLY_USAGE: 0,
                    SUFFIX_RECENT_MONTHLY_COST: 0,
                    SUFFIX_LAST_DAY_USAGE_COST: 0,  # 最近一日费用（新增）
                })

            # 同样需要更新异常处理中的 current_month_volume
            if SUFFIX_CURRENT_MONTH_VOLUME not in account_data:
                account_data[SUFFIX_CURRENT_MONTH_VOLUME] = 0

        else:
            # 未登录时，设置默认值
            account_data.update({
                SUFFIX_LAST_PAYMENT: 0,
                SUFFIX_OWE_AMOUNT: 0,
                SUFFIX_MONTHLY_VOLUME: 0,
                SUFFIX_MONTHLY_COST: 0,
                SUFFIX_CURRENT_MONTH_COST: 0,
                SUFFIX_CURRENT_MONTH_VOLUME: 0,
                SUFFIX_YEARLY_VOLUME: 0,
                SUFFIX_YEARLY_COST: 0,
                SUFFIX_LAST_DAY_USAGE: 0,
                SUFFIX_LAST_DAY_USAGE_TIME: "",
                SUFFIX_RECENT_MONTHLY_COST: 0,
                SUFFIX_RECENT_MONTHLY_USAGE: 0,
                SUFFIX_LAST_DAY_USAGE_COST: 0,  # 最近一日费用（新增）
                ATTR_KEY_LADDER_STAGE: 1,
                ATTR_KEY_LADDER_UNIT_PRICE: 0,
            })

        return account_data

    async def _async_update_data(self) -> dict[str, Any]:
        """更新所有账户数据"""
        _LOGGER.info("Updating all gas accounts data")

        for account_number, account_config in self._config.get(CONF_ACCOUNTS, {}).items():
            user_code = account_config.get(CONF_USER_CODE)
            cid = account_config.get(CONF_CID, 2)
            terminal_type = account_config.get(CONF_TERMINAL_TYPE, 7)

            try:
                # 首次刷新：快速模式，只获取基础数据
                if not self._first_refresh_done:
                    _LOGGER.info(f"First refresh for {user_code}, fetching basic data first...")
                    account_data = await self._async_refresh_basic_data(user_code, cid, terminal_type)
                    self.data[account_number] = account_data
                    self._first_refresh_done = True
                    _LOGGER.info(f"Basic data loaded for {user_code}, will fetch full data in background")

                    # 在后台继续获取完整数据
                    hass = self.hass
                    hass.async_create_task(
                        self._async_fetch_full_data(account_number, user_code, cid, terminal_type)
                    )
                else:
                    # 后续刷新：获取完整数据
                    account_data = await self._async_refresh_account_data(user_code, cid, terminal_type)
                    self.data[account_number] = account_data
                    _LOGGER.debug(f"Updated data for {account_number} (user_code: {user_code})")

            except Exception as err:
                _LOGGER.error(f"Failed to update data for {account_number}: {err}")
                self.data[account_number] = {}

        return self.data

    async def _async_refresh_basic_data(self, user_code: str, cid: int, terminal_type: int) -> dict:
        """快速刷新基础数据（用于首次加载）"""
        account_data = {}
        client = await self._get_or_create_client(user_code, cid, terminal_type)

        # 只获取基础余额信息（公开 API，快速）
        try:
            user_debt = await self.hass.async_add_executor_job(client.get_user_debt)
            if user_debt:
                account_data.update({
                    SUFFIX_BAL: user_debt.remote_meter_balance,
                    "customer_name": user_debt.customer_name,
                    SUFFIX_ADDRESS: user_debt.address,
                    "account_id": user_debt.account_id,
                    SUFFIX_METER_READING: user_debt.reading_last_time,
                    SUFFIX_LAST_COMMUNICATION: parse_datetime(user_debt.remote_meter_last_communication_time),
                    "meter_type": user_debt.meter_type,
                    "mdm_code": user_debt.mdm_code,
                    "user_code": user_debt.user_code,
                    "gas_company": "云南中石油昆仑燃气有限公司昆明分公司",
                })
                # 设置 mdm_code 到 client
                if user_debt.mdm_code:
                    client._mdm_code = user_debt.mdm_code
        except Exception as err:
            _LOGGER.error(f"Error getting basic data for {user_code}: {err}")

        # 设置默认值避免传感器显示未知
        defaults = {
            "gas_company": "云南中石油昆仑燃气有限公司昆明分公司",
            SUFFIX_LAST_PAYMENT: 0,
            ATTR_KEY_LAST_PAYMENT_DATE: "加载中...",
            SUFFIX_OWE_AMOUNT: 0,
            SUFFIX_MONTHLY_VOLUME: 0,
            SUFFIX_MONTHLY_COST: 0,
            SUFFIX_CURRENT_MONTH_COST: 0,
            SUFFIX_CURRENT_MONTH_VOLUME: 0,
            SUFFIX_YEARLY_VOLUME: 0,
            SUFFIX_YEARLY_COST: 0,
            SUFFIX_LAST_DAY_USAGE: 0,
            SUFFIX_LAST_DAY_USAGE_TIME: "",
            SUFFIX_RECENT_MONTHLY_COST: 0,
            SUFFIX_RECENT_MONTHLY_USAGE: 0,
            ATTR_KEY_LADDER_STAGE: 1,
            ATTR_KEY_LADDER_UNIT_PRICE: 0,
        }
        account_data.update({k: v for k, v in defaults.items() if k not in account_data})

        return account_data

    async def _async_fetch_full_data(self, account_number: str, user_code: str, cid: int, terminal_type: int):
        """后台任务：获取完整数据"""
        try:
            _LOGGER.info(f"Background fetch for {user_code}...")
            account_data = await self._async_refresh_account_data(user_code, cid, terminal_type)

            # 合并到现有数据（保留已有数据，只更新新获取的数据）
            if account_number in self.data:
                existing_data = self.data[account_number]
                existing_data.update(account_data)
                self.data[account_number] = existing_data
            else:
                self.data[account_number] = account_data

            _LOGGER.info(f"Full data loaded for {user_code}")

            # 通知所有传感器更新
            self.async_update_listeners()
        except Exception as err:
            # 检查是否是已知的超时问题
            if "timeout" in str(err).lower():
                _LOGGER.warning(f"Background fetch timeout for {user_code}: {err}")
                _LOGGER.info(f"Using cached data for {user_code}, will retry later")
            else:
                _LOGGER.error(f"Background fetch failed for {user_code}: {err}")


# ============================================
# Setup Entry
# ============================================

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup sensors from a config entry created in integrations UI."""

    if not config_entry.data.get(CONF_ACCOUNTS):
        _LOGGER.info("No gas accounts in config, exit entry setup")
        return

    coordinator = GasCoordinator(hass, config_entry)

    all_sensors = []

    for account_number, _ in config_entry.data[CONF_ACCOUNTS].items():
        # 创建所有传感器（优化后共20个）
        all_sensors.append(GasBalanceSensor(coordinator, account_number))
        all_sensors.append(GasCustomerInfoSensor(coordinator, account_number))
        all_sensors.append(GasUserCodeSensor(coordinator, account_number))
        all_sensors.append(GasUserNameSensor(coordinator, account_number))
        all_sensors.append(GasAddressSensor(coordinator, account_number))
        all_sensors.append(GasMeterReadingSensor(coordinator, account_number))
        all_sensors.append(GasLastCommunicationSensor(coordinator, account_number))
        all_sensors.append(GasOweAmountSensor(coordinator, account_number))
        all_sensors.append(GasLastPaymentSensor(coordinator, account_number))
        all_sensors.append(GasLastPaymentDateSensor(coordinator, account_number))
        # 月度数据
        all_sensors.append(GasMonthlyVolumeSensor(coordinator, account_number))
        all_sensors.append(GasMonthlyCostSensor(coordinator, account_number))
        all_sensors.append(CurrentMonthVolumeSensor(coordinator, account_number))  # 本月用量
        all_sensors.append(CurrentMonthCostSensor(coordinator, account_number))
        # 近31天数据
        all_sensors.append(RecentMonthlyUsageSensor(coordinator, account_number))  # 近31天累计
        all_sensors.append(RecentMonthlyCostSensor(coordinator, account_number))  # 近31天费用
        # 最近日数据
        all_sensors.append(LastDayUsageSensor(coordinator, account_number))
        all_sensors.append(LastDayUsageTimeSensor(coordinator, account_number))
        all_sensors.append(LastDayUsageCostSensor(coordinator, account_number))  # 最近一日费用（新增）
        # 年度数据和阶梯
        all_sensors.append(YearlyVolumeSensor(coordinator, account_number))
        all_sensors.append(YearlyCostSensor(coordinator, account_number))
        all_sensors.append(LadderStageSensor(coordinator, account_number))
        all_sensors.append(LadderUnitPriceSensor(coordinator, account_number))

    async_add_entities(all_sensors)

    _LOGGER.info(f"Created {len(all_sensors)} sensors for config {config_entry.title}")

    # Schedule first update to run in background
    config_entry.async_create_task(
        hass,
        coordinator.async_config_entry_first_refresh(),
        f"{config_entry.title}_first_update",
    )
