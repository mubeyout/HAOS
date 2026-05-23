"""Data models for Gas API responses."""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


class CSGAPIError(Exception):
    """API异常类"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


@dataclass
class GasAccount:
    """燃气账户信息"""
    account_id: str
    user_code: str
    customer_name: str
    address: str
    remote_meter_balance: float
    meter_type: str
    mdm_code: str
    reading_last_time: str
    remote_meter_last_communication_time: str
    user_code_id: Optional[str] = None  # 用于缴费记录等需要认证的接口


@dataclass
class GasMeterData:
    """表计数据"""
    reading_last_time: str
    remote_meter_last_communication_time: str


@dataclass
class GasUsageRecord:
    """用气记录"""
    date: str
    volume: float
    cost: float


@dataclass
class GasPaymentRecord:
    """缴费记录"""
    payment_time: str
    amount: float
    payment_method: Optional[str] = None


@dataclass
class LadderPricing:
    """阶梯价格信息"""
    current_ladder: int
    ladder_1_price: Optional[float] = None
    ladder_1_start: Optional[float] = None
    ladder_1_end: Optional[float] = None
    ladder_2_price: Optional[float] = None
    ladder_2_start: Optional[float] = None
    ladder_2_end: Optional[float] = None
    ladder_3_price: Optional[float] = None
    ladder_3_start: Optional[float] = None
    ladder_3_end: Optional[float] = None


@dataclass
class LadderRateItem:
    """阶梯价格项"""
    rate_name: str
    begin_volume: float
    end_volume: float
    price: float


@dataclass
class MonthlyUsageRecord:
    """月度用气记录"""
    gas_year: str
    gas_volume: float
    gas_fee: float


@dataclass
class PaymentRecordItem:
    """缴费记录项"""
    operation_date: str
    operation_time: str
    pay_amount: float
    pay_org_desc: str
    pay_source_desc: str
    pay_status_desc: str
    pay_item_type: str
