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
9. 上次缴费金额与时间 (last_payment)
10. 今日用气量与金额 (daily_volume, daily_cost)
11. 上月用气量与金额 (monthly_volume, monthly_cost)
12. 近10天/30天用量 (recent_usage)
13. 去年用气量与金额 (yearly_usage)
14. 今年用气量与金额 (yearly_volume, yearly_cost)
15. 阶梯价格与范围 (ladder_stage, ladder_price, current_ladder)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
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
    SUFFIX_BAL,
    SUFFIX_ADDRESS,
    SUFFIX_LADDER_STAGE,
    SUFFIX_DAILY_VOLUME,
    SUFFIX_DAILY_COST,
    SUFFIX_MONTHLY_VOLUME,
    SUFFIX_MONTHLY_COST,
    SUFFIX_YEARLY_VOLUME,
    SUFFIX_YEARLY_COST,
    SUFFIX_LAST_PAYMENT,
    SUFFIX_OWE_AMOUNT,
    SUFFIX_METER_READING,
    SUFFIX_LAST_COMMUNICATION,
    ATTR_KEY_LAST_UPDATE,
    ATTR_KEY_CUSTOMER_NAME,
    ATTR_KEY_ADDRESS,
    ATTR_KEY_ACCOUNT_ID,
    ATTR_KEY_METER_TYPE,
    ATTR_KEY_LADDER_1,
    ATTR_KEY_LADDER_2,
    ATTR_KEY_LADDER_3,
    ATTR_KEY_CURRENT_LADDER,
)
from .gas_client import GasHttpClient

_LOGGER = logging.getLogger(__name__)


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
        account_data = self.coordinator.data.get(self._account_number)

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
        self._attr_unit_of_measurement = "CNY"


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


class GasLastPaymentSensor(GasBaseSensor):
    """上次缴费金额与时间传感器"""
    _attr_icon = "mdi:receipt"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_LAST_PAYMENT)


class GasDailyVolumeSensor(GasBaseSensor):
    """今日用气量传感器"""
    _attr_icon = "mdi:fire"
    _attr_device_class = SensorDeviceClass.GAS

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_DAILY_VOLUME)


class GasDailyCostSensor(GasBaseSensor):
    """今日用气费用传感器"""
    _attr_icon = "mdi:cash"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_DAILY_COST)


class GasMonthlyVolumeSensor(GasBaseSensor):
    """上月用气量传感器"""
    _attr_icon = "mdi:calendar-month"
    _attr_device_class = SensorDeviceClass.GAS

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_MONTHLY_VOLUME)


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


class RecentUsageSensor(GasBaseSensor):
    """近10天/30天用量传感器"""
    _attr_icon = "mdi:chart-line"
    _attr_device_class = SensorDeviceClass.GAS

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "recent_usage")


class YearlyVolumeSensor(GasBaseSensor):
    """今年用气量传感器"""
    _attr_icon = "mdi:chart-bar"
    _attr_device_class = SensorDeviceClass.GAS

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_YEARLY_VOLUME)


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


class LadderStageSensor(GasBaseSensor):
    """当前阶梯传感器"""
    _attr_icon = "mdi:stairs"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, SUFFIX_LADDER_STAGE)


class LadderPriceSensor(GasBaseSensor):
    """阶梯价格传感器"""
    _attr_icon = "mdi:tag"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "ladder_price")


class CurrentLadderSensor(GasBaseSensor):
    """当前阶梯与单价传感器"""
    _attr_icon = "mdi:format-list-numbered"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, ATTR_KEY_CURRENT_LADDER)


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

    def _get_or_create_client(self, user_code: str, cid: int, terminal_type: int) -> GasHttpClient:
        """获取或创建HTTP客户端"""
        if user_code not in self._clients:
            self._clients[user_code] = GasHttpClient(
                user_code=user_code,
                cid=cid,
                terminal_type=terminal_type
            )
            self._logged_in[user_code] = False
        return self._clients[user_code]

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
        client = self._get_or_create_client(user_code, cid, terminal_type)
        account_data = {}

        # 1. 尝试登录（如果提供了微信授权码）
        logged_in = await self._async_login_if_needed(user_code, client)

        # 2. 获取基础数据（公开API，无需认证）
        try:
            user_debt = await self.hass.async_add_executor_job(client.get_user_debt)
            if user_debt:
                account_data.update({
                    SUFFIX_BAL: user_debt.remote_meter_balance,
                    "customer_name": user_debt.customer_name,
                    SUFFIX_ADDRESS: user_debt.address,
                    "account_id": user_debt.account_id,
                    SUFFIX_METER_READING: user_debt.reading_last_time,
                    SUFFIX_LAST_COMMUNICATION: user_debt.remote_meter_last_communication_time,
                    "meter_type": user_debt.meter_type,
                    "mdm_code": user_debt.mdm_code,
                    "user_code": user_debt.user_code,
                })
        except Exception as err:
            _LOGGER.error(f"Error getting user debt for {user_code}: {err}")

        # 3. 如果已登录，获取认证后的数据
        if logged_in:
            # 获取缴费记录
            try:
                payment_records = await self.hass.async_add_executor_job(
                    client.get_payment_records,
                    1,  # page
                    10  # page_size
                )

                if payment_records and "recordsInfoList" in payment_records:
                    records = payment_records["recordsInfoList"]
                    if records:
                        last_payment = records[0]
                        account_data.update({
                            SUFFIX_LAST_PAYMENT: f"{last_payment.get('payAmount', 0)}元 ({last_payment.get('operationDate', '')})",
                            SUFFIX_OWE_AMOUNT: float(last_payment.get('oweAmount', 0)),
                        })
                    else:
                        account_data.update({
                            SUFFIX_LAST_PAYMENT: "无缴费记录",
                            SUFFIX_OWE_AMOUNT: 0,
                        })
            except Exception as err:
                _LOGGER.error(f"Error getting payment records for {user_code}: {err}")
                account_data.update({
                    SUFFIX_LAST_PAYMENT: "获取失败",
                    SUFFIX_OWE_AMOUNT: 0,
                })

            # 获取月度用量（包含阶梯价格信息）
            try:
                monthly_data = await self.hass.async_add_executor_job(
                    client.get_monthly_usage,
                    1,  # page
                    7   # page_size (7 months)
                )

                if monthly_data and "error" not in monthly_data:
                    # 解析阶梯价格
                    rate_items = monthly_data.get("rateItemInfo", [])

                    ladder_1 = {"price": 0, "start": 0, "end": 0}
                    ladder_2 = {"price": 0, "start": 0, "end": 0}
                    ladder_3 = {"price": 0, "start": 0, "end": 0}
                    current_ladder = 1

                    for item in rate_items:
                        rate_name = item.get("rateName", "")
                        if "第一" in rate_name or "1" in rate_name or "一档" in rate_name:
                            ladder_1 = {
                                "price": float(item.get("price", 0)),
                                "start": float(item.get("beginVolume", 0)),
                                "end": float(item.get("endVolume", 0)),
                            }
                        elif "第二" in rate_name or "2" in rate_name or "二档" in rate_name:
                            ladder_2 = {
                                "price": float(item.get("price", 0)),
                                "start": float(item.get("beginVolume", 0)),
                                "end": float(item.get("endVolume", 0)),
                            }
                        elif "第三" in rate_name or "3" in rate_name or "三档" in rate_name:
                            ladder_3 = {
                                "price": float(item.get("price", 0)),
                                "start": float(item.get("beginVolume", 0)),
                                "end": float(item.get("endVolume", 0)),
                            }

                    # 解析月度用量记录
                    records = monthly_data.get("recordsInfo", [])
                    if records:
                        # 获取上月数据
                        last_month = records[0]
                        account_data.update({
                            SUFFIX_MONTHLY_VOLUME: float(last_month.get("gasVolume", 0)),
                            SUFFIX_MONTHLY_COST: float(last_month.get("gasFee", 0)),
                        })

                        # 计算今年累计用量
                        current_year = datetime.now().year
                        yearly_volume = sum(
                            float(r.get("gasVolume", 0))
                            for r in records
                            if r.get("gasYear", f"{current_year}").startswith(str(current_year))
                        )
                        yearly_cost = sum(
                            float(r.get("gasFee", 0))
                            for r in records
                            if r.get("gasYear", f"{current_year}").startswith(str(current_year))
                        )

                        account_data.update({
                            SUFFIX_YEARLY_VOLUME: yearly_volume,
                            SUFFIX_YEARLY_COST: yearly_cost,
                        })

                        # 根据累计用量确定当前阶梯
                        total_volume = yearly_volume
                        if total_volume >= ladder_3["start"] and ladder_3["price"] > 0:
                            current_ladder = 3
                        elif total_volume >= ladder_2["start"] and ladder_2["price"] > 0:
                            current_ladder = 2
                        else:
                            current_ladder = 1
                    else:
                        account_data.update({
                            SUFFIX_MONTHLY_VOLUME: 0,
                            SUFFIX_MONTHLY_COST: 0,
                            SUFFIX_YEARLY_VOLUME: 0,
                            SUFFIX_YEARLY_COST: 0,
                        })

                    # 更新阶梯价格数据
                    account_data.update({
                        "ladder_stage": current_ladder,
                        "ladder_price": {
                            "第一阶梯": f"{ladder_1['price']}元/m³ ({ladder_1['start']}-{ladder_1['end']}m³)",
                            "第二阶梯": f"{ladder_2['price']}元/m³ ({ladder_2['start']}-{ladder_2['end']}m³)",
                            "第三阶梯": f"{ladder_3['price']}元/m³ ({ladder_3['start']}m³以上)",
                        },
                        ATTR_KEY_CURRENT_LADDER: f"第{current_ladder}阶梯",
                        ATTR_KEY_LADDER_1: ladder_1,
                        ATTR_KEY_LADDER_2: ladder_2,
                        ATTR_KEY_LADDER_3: ladder_3,
                    })

            except Exception as err:
                _LOGGER.error(f"Error getting monthly usage for {user_code}: {err}")
                account_data.update({
                    SUFFIX_MONTHLY_VOLUME: 0,
                    SUFFIX_MONTHLY_COST: 0,
                    SUFFIX_YEARLY_VOLUME: 0,
                    SUFFIX_YEARLY_COST: 0,
                    "ladder_stage": 1,
                    "ladder_price": {},
                    ATTR_KEY_CURRENT_LADDER: "未知",
                })

            # 获取每日用量（用于今日用量和近期用量）
            try:
                daily_usage = await self.hass.async_add_executor_job(
                    client.get_daily_usage,
                    30  # 30 days
                )

                if daily_usage and "daily_volumes" in daily_usage:
                    daily_volumes = daily_usage["daily_volumes"]
                    if daily_volumes:
                        # 获取今日数据
                        today = datetime.now().strftime("%Y-%m-%d")
                        today_data = next(
                            (d for d in daily_volumes if d["date"].startswith(today)),
                            None
                        )

                        account_data.update({
                            SUFFIX_DAILY_VOLUME: today_data["volume"] if today_data else 0,
                            SUFFIX_DAILY_COST: today_data["cost"] if today_data else 0,
                        })

                        # 计算近10天和30天用量
                        recent_10_days = sum(d["volume"] for d in daily_volumes[:10])
                        recent_30_days = sum(d["volume"] for d in daily_volumes[:30])

                        account_data.update({
                            "recent_usage": {
                                "近10天": f"{recent_10_days}m³",
                                "近30天": f"{recent_30_days}m³",
                                "daily_detail": daily_volumes[:30],
                            }
                        })
                    else:
                        account_data.update({
                            SUFFIX_DAILY_VOLUME: 0,
                            SUFFIX_DAILY_COST: 0,
                            "recent_usage": {},
                        })
            except Exception as err:
                _LOGGER.error(f"Error getting daily usage for {user_code}: {err}")
                account_data.update({
                    SUFFIX_DAILY_VOLUME: 0,
                    SUFFIX_DAILY_COST: 0,
                    "recent_usage": {},
                })

        else:
            # 未登录时，设置默认值
            account_data.update({
                SUFFIX_LAST_PAYMENT: "需要登录查看",
                SUFFIX_OWE_AMOUNT: 0,
                SUFFIX_DAILY_VOLUME: 0,
                SUFFIX_DAILY_COST: 0,
                SUFFIX_MONTHLY_VOLUME: 0,
                SUFFIX_MONTHLY_COST: 0,
                SUFFIX_YEARLY_VOLUME: 0,
                SUFFIX_YEARLY_COST: 0,
                "recent_usage": {},
                "ladder_stage": 1,
                "ladder_price": {},
                ATTR_KEY_CURRENT_LADDER: "需要登录查看",
                ATTR_KEY_LADDER_1: {},
                ATTR_KEY_LADDER_2: {},
                ATTR_KEY_LADDER_3: {},
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
                account_data = await self._async_refresh_account_data(user_code, cid, terminal_type)
                self.data[user_code] = account_data
                _LOGGER.debug(f"Updated data for {user_code}")
            except Exception as err:
                _LOGGER.error(f"Failed to update data for {user_code}: {err}")
                self.data[user_code] = {}

        return self.data


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
        # 创建所有18个传感器
        all_sensors.append(GasBalanceSensor(coordinator, account_number))
        all_sensors.append(GasCustomerInfoSensor(coordinator, account_number))
        all_sensors.append(GasUserCodeSensor(coordinator, account_number))
        all_sensors.append(GasUserNameSensor(coordinator, account_number))
        all_sensors.append(GasAddressSensor(coordinator, account_number))
        all_sensors.append(GasMeterReadingSensor(coordinator, account_number))
        all_sensors.append(GasLastCommunicationSensor(coordinator, account_number))
        all_sensors.append(GasOweAmountSensor(coordinator, account_number))
        all_sensors.append(GasLastPaymentSensor(coordinator, account_number))
        all_sensors.append(GasDailyVolumeSensor(coordinator, account_number))
        all_sensors.append(GasDailyCostSensor(coordinator, account_number))
        all_sensors.append(GasMonthlyVolumeSensor(coordinator, account_number))
        all_sensors.append(GasMonthlyCostSensor(coordinator, account_number))
        all_sensors.append(RecentUsageSensor(coordinator, account_number))
        all_sensors.append(YearlyVolumeSensor(coordinator, account_number))
        all_sensors.append(YearlyCostSensor(coordinator, account_number))
        all_sensors.append(LadderStageSensor(coordinator, account_number))
        all_sensors.append(LadderPriceSensor(coordinator, account_number))
        all_sensors.append(CurrentLadderSensor(coordinator, account_number))

    await async_add_entities(all_sensors)

    _LOGGER.info(f"Created {len(all_sensors)} sensors for config {config_entry.title}")

    # Schedule first update to run in background
    config_entry.async_create_task(
        hass,
        coordinator.async_config_entry_first_refresh(),
        f"{config_entry.title}_first_update",
    )
