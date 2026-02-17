"""Sensors for Kunming Water integration.

包含以下传感器类型：
1. 用户名 (user_name) - 配置时获取
2. 地址 (address) - 配置时获取
3. 账户编号 (user_code) - 配置时获取
4. 最新账单用水量 (latest_usage) - 从账单列表获取
5. 两月用水量 (two_month_usage) - 从账单列表获取（同 latest_usage）
6. 月平均用水量 (monthly_avg_usage) - 计算得出（两月用水量 / 2）
7. 最新账单金额 (latest_bill_amount) - 根据用水量计算（总费用）
8. 自来水费 (bill_water_fee) - 根据用水量计算 (3.20元/m³)
9. 污水费 (bill_sewage_fee) - 根据用水量计算 (1.00元/m³)
10. 垃圾费 (bill_garbage_fee) - 固定金额 (20.00元)
11. 水表口径 (caliber) - 配置时获取
12. 抄表周期 (cycle) - 配置时获取

注意：
- 采用方案 A（改进版）：使用 billChart API 获取账单数据
- 需要 ticket 参数，从账户主页 HTML 中获取
- 账单数据在配置时获取并保存
- 费用计算基于实际账单明细：
  * 自来水费单价: 3.20元/m³
  * 污水费单价: 1.00元/m³
  * 垃圾费: 20.00元/期（固定）
  * 总费用 = 用水量 × (3.20 + 1.00) + 20.00
- 如需更新数据，请重新配置集成
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    CONF_USER_CODE,
    ATTR_USER_NAME,
    ATTR_ADDRESS,
)

_LOGGER = logging.getLogger(__name__)


# ============================================
# Base Sensor Class
# ============================================

class WaterBaseSensor(CoordinatorEntity, SensorEntity):
    """昆明水务传感器基类"""

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
            name=f"WaterAccount-{self._account_number}",
            manufacturer="Kunming Water",
            model="Virtual Water Meter",
        )

    @property
    def should_poll(self) -> bool:
        """默认不轮询"""
        return False

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

class WaterUserCodeSensor(WaterBaseSensor):
    """账户编号传感器"""
    _attr_icon = "mdi:numeric"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "user_code")


class WaterUserNameSensor(WaterBaseSensor):
    """用户名传感器"""
    _attr_icon = "mdi:account-circle"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, ATTR_USER_NAME)


class WaterAddressSensor(WaterBaseSensor):
    """地址传感器"""
    _attr_icon = "mdi:map-marker"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, ATTR_ADDRESS)


class WaterTwoMonthUsageSensor(WaterBaseSensor):
    """两月总用水量传感器"""
    _attr_icon = "mdi:water"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "two_month_usage")
        self._attr_native_unit_of_measurement = "m³"


class WaterMonthlyAvgUsageSensor(WaterBaseSensor):
    """月平均用水量传感器"""
    _attr_icon = "mdi:calendar-month"
    _attr_device_class = SensorDeviceClass.WATER

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "monthly_avg_usage")
        self._attr_native_unit_of_measurement = "m³"


class WaterLatestUsageSensor(WaterBaseSensor):
    """最新账单用水量传感器"""
    _attr_icon = "mdi:water-pump"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "latest_usage")
        self._attr_native_unit_of_measurement = "m³"


class WaterCaliberSensor(WaterBaseSensor):
    """水表口径传感器"""
    _attr_icon = "mdi:gauge"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "caliber")


class WaterCycleSensor(WaterBaseSensor):
    """抄表周期传感器"""
    _attr_icon = "mdi:calendar-refresh"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "cycle")


class WaterLatestBillAmountSensor(WaterBaseSensor):
    """最新账单金额传感器（估算）"""
    _attr_icon = "mdi:currency-cny"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "latest_bill_amount")
        self._attr_native_unit_of_measurement = "CNY"


class WaterBillWaterFeeSensor(WaterBaseSensor):
    """自来水费传感器（估算）"""
    _attr_icon = "mdi:water"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "bill_water_fee")
        self._attr_native_unit_of_measurement = "CNY"


class WaterBillSewageFeeSensor(WaterBaseSensor):
    """污水费传感器（估算）"""
    _attr_icon = "mdi:water-waves"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "bill_sewage_fee")
        self._attr_native_unit_of_measurement = "CNY"


class WaterBillGarbageFeeSensor(WaterBaseSensor):
    """垃圾费传感器（固定）"""
    _attr_icon = "mdi:trash-can"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "bill_garbage_fee")
        self._attr_native_unit_of_measurement = "CNY"


class WaterBillDateSensor(WaterBaseSensor):
    """最新账单日期传感器"""
    _attr_icon = "mdi:calendar"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        account_number: str,
    ) -> None:
        super().__init__(coordinator, account_number, "bill_date")


# ============================================
# Setup Entry
# ============================================

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry."""

    user_code = config_entry.data.get(CONF_USER_CODE)
    if not user_code:
        _LOGGER.info("No user_code in config, exit entry setup")
        return

    # 创建协调器
    coordinator = WaterCoordinator(hass, config_entry)

    # 创建所有传感器
    all_sensors = []
    account_number = user_code

    all_sensors.append(WaterUserCodeSensor(coordinator, account_number))
    all_sensors.append(WaterUserNameSensor(coordinator, account_number))
    all_sensors.append(WaterAddressSensor(coordinator, account_number))
    all_sensors.append(WaterCaliberSensor(coordinator, account_number))
    all_sensors.append(WaterCycleSensor(coordinator, account_number))
    all_sensors.append(WaterLatestUsageSensor(coordinator, account_number))
    all_sensors.append(WaterLatestBillAmountSensor(coordinator, account_number))
    all_sensors.append(WaterBillDateSensor(coordinator, account_number))
    # 费用明细传感器
    all_sensors.append(WaterBillWaterFeeSensor(coordinator, account_number))
    all_sensors.append(WaterBillSewageFeeSensor(coordinator, account_number))
    all_sensors.append(WaterBillGarbageFeeSensor(coordinator, account_number))
    all_sensors.append(WaterTwoMonthUsageSensor(coordinator, account_number))
    all_sensors.append(WaterMonthlyAvgUsageSensor(coordinator, account_number))

    async_add_entities(all_sensors)

    _LOGGER.info(f"Created {len(all_sensors)} sensors for config {config_entry.title}")

    # 首次更新
    await coordinator.async_config_entry_first_refresh()


# ============================================
# Coordinator
# ============================================

class WaterCoordinator(DataUpdateCoordinator):
    """昆明水务数据协调器 - 方案 A：使用配置时获取的静态数据"""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """初始化协调器"""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # 不自动更新 - 数据仅在配置时获取一次
            update_interval=None,
        )
        self._config_entry = config_entry
        self._config = config_entry.data
        self.data = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """返回配置时保存的静态数据 - 包括账单列表"""
        _LOGGER.info("Using static data from configuration (including bill list)")

        user_code = self._config.get(CONF_USER_CODE)

        # 从配置中获取账单列表
        bill_list = self._config.get("bill_list", [])

        # 计算最新用水量和费用明细
        latest_usage = None
        latest_bill_amount = None
        bill_water_fee = None      # 自来水费
        bill_sewage_fee = None     # 污水费
        bill_garbage_fee = None    # 垃圾费（固定）
        two_month_usage = None     # 两月用水量
        monthly_avg_usage = None   # 月平均用水量
        bill_date = None           # 账单日期

        if bill_list:
            try:
                latest_usage = int(bill_list[0].get("amount", 0))
                bill_no = bill_list[0].get("billNo", "")

                # 从账单号解析日期 (格式: YYYYMM)
                if bill_no and len(bill_no) >= 6:
                    try:
                        year = int(bill_no[:4])
                        month = int(bill_no[4:6])
                        # 抄表通常是每月10日
                        bill_date = date(year, month, 10)
                    except (ValueError, IndexError):
                        pass

                if latest_usage > 0:
                    # 根据实际账单明细的费用公式计算
                    # 自来水费单价: 3.20元/m³
                    # 污水费单价: 1.00元/m³
                    # 垃圾费: 20.00元（固定）
                    WATER_RATE = 3.20      # 自来水费单价 (元/m³)
                    SEWAGE_RATE = 1.00     # 污水费单价 (元/m³)
                    GARBAGE_FEE = 20.00    # 垃圾费 (元/期，固定)

                    bill_water_fee = round(latest_usage * WATER_RATE, 2)
                    bill_sewage_fee = round(latest_usage * SEWAGE_RATE, 2)
                    bill_garbage_fee = GARBAGE_FEE
                    latest_bill_amount = round(bill_water_fee + bill_sewage_fee + bill_garbage_fee, 2)

                    # 计算可推导的数据
                    two_month_usage = latest_usage  # 两月用水量 = 账单用水量
                    monthly_avg_usage = round(latest_usage / 2, 2)  # 月平均 = 两月 / 2
            except (ValueError, IndexError):
                pass

        # 使用配置时保存的用户信息
        account_data = {
            # 从配置中获取的静态数据
            ATTR_USER_NAME: self._config.get("user_name"),
            ATTR_ADDRESS: self._config.get("address"),
            "user_code": user_code,
            "caliber": self._config.get("caliber"),
            "cycle": self._config.get("cycle"),

            # 账单数据
            "latest_usage": latest_usage,
            "latest_bill_amount": latest_bill_amount,  # 估算的账单金额
            "bill_date": bill_date,                    # 账单日期 (从账单号解析)
            "bill_water_fee": bill_water_fee,          # 自来水费
            "bill_sewage_fee": bill_sewage_fee,        # 污水费
            "bill_garbage_fee": bill_garbage_fee,      # 垃圾费
            "bill_list": bill_list,

            # 可计算的数据
            "two_month_usage": two_month_usage,        # 两月用水量 = 账单用水量
            "monthly_avg_usage": monthly_avg_usage,    # 月平均用水量 = 两月 / 2
        }

        self.data[user_code] = account_data
        _LOGGER.info(
            f"Static data loaded for {user_code} - "
            f"latest_usage: {latest_usage} m³, "
            f"bill_date: {bill_date}, "
            f"two_month_usage: {two_month_usage} m³, "
            f"monthly_avg_usage: {monthly_avg_usage} m³, "
            f"latest_bill_amount: {latest_bill_amount} CNY "
            f"(water: {bill_water_fee}, sewage: {bill_sewage_fee}, garbage: {bill_garbage_fee}), "
            f"bills: {len(bill_list)}"
        )

        # 记录信息
        _LOGGER.info(
            "昆明水务数据从配置时获取。"
            "如需更新数据，请重新配置集成。"
        )

        return self.data
