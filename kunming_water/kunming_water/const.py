"""Constants for Kunming Water integration."""
from datetime import timedelta

# ============================================================
# Domain and integration info
# ============================================================
DOMAIN = "kunming_water"

# Config flow
CONF_USER_CODE = "user_code"
CONF_MOBILE = "mobile"
CONF_PASSWORD = "password"

# ============================================================
# API Endpoints
# ============================================================
API_BASE = "https://km96106.cn"  # 昆明水务 API 基础地址

# Authentication
API_AUTH_CODE = "/api/v1/open/sms/sendAuthCode"  # 短信验证码登录
API_AUTH_LOGIN = "/api/v1/open/user/passwordLogin"   # 手机密码登录
API_CHECK_AUTH_CODE = "/api/v1/open/sms/checkAuthCode"  # 查询验证码状态

# Data retrieval
API_GET_USER_INFO = "/api/v1/close/user/getUserInfo"     # 获取用户信息
API_GET_BALANCE = "/api/v1/close/recharge/getUserBalance"  # 获取余额
API_GET_BILL_LIST = "/api/v1/close/recharge/getBillList"     # 获取账单列表
API_GET_USAGE_LIST = "/api/v1/close/recharge/getUsageList"  # 获取用量列表
API_GET_USAGE_DETAIL = "/api/v1/close/recharge/getUsageDetail"  # 获取用量详情

# ============================================================
# State attributes
# ============================================================
ATTR_USER_NAME = "user_name"
ATTR_ADDRESS = "address"
ATTR_ACCOUNT_BALANCE = "account_balance"
ATTR_LAST_BILL_DATE = "last_bill_date"
ATTR_LAST_PAYMENT_DATE = "last_payment_date"
ATTR_LAST_PAYMENT_AMOUNT = "last_payment_amount"
ATTR_BILL_AMOUNT = "bill_amount"
ATTR_BILL_STATUS = "bill_status"
ATTR_BILL_PERIOD = "bill_period"
ATTR_MONTHLY_USAGE_TOTAL = "monthly_usage_total"  # 本月累计用水量（API返回）
ATTR_UNIT_PRICE = "unit_price"  # 当前水价单价
ATTR_LADDER_STAGE = "ladder_stage"  # 当前阶梯

# ============================================================
# Sensor suffixes
# ============================================================
SUFFIX_BALANCE = "balance"
SUFFIX_LAST_PAYMENT = "last_payment"
SUFFIX_MONTHLY_USAGE = "monthly_usage"
SUFFIX_DAILY_USAGE = "daily_usage"
SUFFIX_UNIT_PRICE = "unit_price"  # 单价传感器
SUFFIX_LADDER_STAGE = "ladder_stage"  # 阶梯传感器

# ============================================================
# Water Price Ladder Configuration (昆明市民用水价格）
# ============================================================
# 第一阶梯：生活用水 0-12.5 m³/月，单价 4.20 元/m³
# 第二阶梯：生活用水 12.5-17.5 m³/月，单价 5.80 元/m³
# 第三阶梯：生活用水 17.5 m³以上/月，单价 10.60 元/m³
WATER_LADDER_CONFIG = [
    {"max_volume": 12.5, "unit_price": 4.20, "stage": 1},
    {"max_volume": 17.5, "unit_price": 5.80, "stage": 2},
    {"max_volume": float("inf"), "unit_price": 10.60, "stage": 3},
]

# ============================================================
# Defaults
# ============================================================
DEFAULT_UPDATE_INTERVAL = timedelta(hours=1).seconds
SCAN_INTERVAL = timedelta(seconds=30).seconds  # For config flow
