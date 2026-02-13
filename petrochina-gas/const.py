"""Constants for PetroChina Gas Statistics integration."""
from datetime import timedelta

# ============================================================
# Domain and integration info
# ============================================================
DOMAIN = "petrochina_gas"

# Config flow
# main account (user code)
CONF_USER_CODE = "user_code"
CONF_CID = "cid"
CONF_TERMINAL_TYPE = "terminal_type"

# electricity accounts -> gas accounts
CONF_ACCOUNTS = "accounts"
CONF_SETTINGS = "settings"
CONF_UPDATED_AT = "updated_at"
CONF_ACTION = "action"

# Abort states
ABORT_NO_ACCOUNT = "no_account"
ABORT_ALL_ADDED = "all_added"

# Errors
CONF_GENERAL_ERROR = "base"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_UNKNOWN = "unknown"

# UI
LOGIN_TYPE_WX_QR_APP_NAME = {
    "wx_qr": "微信小程序",
}

# ============================================================
# API Endpoints
# ============================================================
API_BASE = "https://bol.grs.petrochina.com.cn"

# Open API (no authentication required)
API_OPEN_USER_AUTH = f"{API_BASE}/api/v1/open/weixin/userAuthorization"
API_OPEN_GET_USER_DEBT = f"{API_BASE}/api/v1/open/recharge/getUserDebtByUserCode"

# Close API (authentication may be required)
API_CLOSE_GET_USER_CODE = f"{API_BASE}/api/v1/close/user/getUserCode"
API_CLOSE_GET_USER_DEBT = f"{API_BASE}/api/v1/close/recharge/getUserDebt"
API_GET_METER_READING = "/api/v1/close/recharge/smartMeterGasDaysRecords"
API_GET_PAYMENT_RECORDS = "/api/v1/close/recharge/getPaymentRecordList"
API_GET_MONTHLY_VOLUME = "/api/v1/close/recharge/getMonthlyTotalGasVolume"

# Request Parameters
PARAM_CID = "cid"
PARAM_USER_CODE = "userCode"
PARAM_TERMINAL_TYPE = "terminalType"
PARAM_USER_CODE_ID = "userCodeId"
PARAM_PAGE = "page"
PARAM_PAGE_SIZE = "pageSize"
PARAM_PAGE_NUMBER = "pageNumber"
PARAM_CODE = "code"
PARAM_UNION_ID = "unionId"

# Response Fields
FIELD_CODE = "code"
FIELD_DATA = "data"
FIELD_MESSAGE = "message"
FIELD_SUCCESS = "success"
FIELD_SUCCESS_WITH_DATA = "successWithData"

# Data Fields
DATA_ACCOUNT_ID = "accountId"
DATA_ADDRESS = "address"
DATA_CUSTOMER_NAME = "customerName"
DATA_REMOTE_METER_BALANCE = "remoteMeterBalance"
DATA_METER_TYPE = "meterType"
DATA_MDM_CODE = "mdmCode"
DATA_READING_LAST_TIME = "readingLastTime"
DATA_REMOTE_METER_LAST_COMMUNICATION_TIME = "remoteMeterLastCommunicationTime"

# Ladder Pricing
DATA_LADDER_1_PRICE = "ladder_1_price"
DATA_LADDER_1_START = "ladder_1_start"
DATA_LADDER_1_END = "ladder_1_end"

DATA_LADDER_2_PRICE = "ladder_2_price"
DATA_LADDER_2_START = "ladder_2_start"
DATA_LADDER_2_END = "ladder_2_end"

DATA_LADDER_3_PRICE = "ladder_3_price"
DATA_LADDER_3_START = "ladder_3_start"
DATA_LADDER_3_END = "ladder_3_end"

DATA_CURRENT_LADDER = "current_ladder"
DATA_RATE_ITEM_INFO = "rateItemInfo"
DATA_RECORDS_INFO = "recordsInfo"

# Payment History
DATA_LAST_PAYMENT_AMOUNT = "lastPaymentAmount"
DATA_LAST_PAYMENT_TIME = "lastPaymentTime"
DATA_OWE_AMOUNT = "oweAmount"
DATA_PAYMENT_RECORDS_LIST = "recordsInfoList"

# Usage Statistics
DATA_DAILY_VOLUME = "gasVolume"
DATA_DAILY_COST = "gasFee"
DATA_MONTHLY_VOLUME = "monthlyVolume"
DATA_MONTHLY_COST = "monthlyCost"
DATA_TOTAL_GAS_VOLUME = "totalGasVolume"

# ============================================================
# Sensor Suffixes
# ============================================================
# Balance and arrears
SUFFIX_BAL = "balance"
SUFFIX_ARREARS = "arrears"

# Meter readings
SUFFIX_METER_READING = "meter_reading"
SUFFIX_LAST_COMMUNICATION = "last_communication"

# Usage statistics
SUFFIX_DAILY_VOLUME = "daily_volume"
SUFFIX_DAILY_COST = "daily_cost"
SUFFIX_MONTHLY_VOLUME = "monthly_volume"
SUFFIX_MONTHLY_COST = "monthly_cost"
SUFFIX_YEARLY_VOLUME = "yearly_volume"
SUFFIX_YEARLY_COST = "yearly_cost"

# Ladder pricing
SUFFIX_LADDER_STAGE = "ladder_stage"
SUFFIX_LADDER_PRICE = "ladder_price"
SUFFIX_LADDER_REMAINING = "ladder_remaining"

# Customer info
SUFFIX_CUSTOMER_NAME = "customer_name"
SUFFIX_ADDRESS = "address"

# Payment info
SUFFIX_LAST_PAYMENT = "last_payment"
SUFFIX_OWE_AMOUNT = "owe_amount"

# ============================================================
# Sensor Attributes Keys
# ============================================================
# Customer information
ATTR_KEY_CUSTOMER_NAME = "customer_name"
ATTR_KEY_ADDRESS = "address"
ATTR_KEY_ACCOUNT_ID = "account_id"

# Meter information
ATTR_KEY_METER_TYPE = "meter_type"

# Ladder pricing
ATTR_KEY_LADDER_1 = "ladder_1"
ATTR_KEY_LADDER_2 = "ladder_2"
ATTR_KEY_LADDER_3 = "ladder_3"
ATTR_KEY_CURRENT_LADDER = "current_ladder"

# Update timestamps
ATTR_KEY_LAST_UPDATE = "last_update"
ATTR_KEY_LAST_READING = "last_reading"
ATTR_KEY_LAST_COMMUNICATION = "last_communication"

# ============================================================
# Defaults
# ============================================================
# Update interval (how often to poll for updates)
DEFAULT_UPDATE_INTERVAL = timedelta(hours=1).seconds

# Request timeout (each request timeout in seconds)
SETTING_UPDATE_TIMEOUT = 60

# ============================================================
# State Update Reasons
# ============================================================
STATE_UPDATE_UNCHANGED = "unchanged"
