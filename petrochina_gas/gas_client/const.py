"""Constants for Gas API Client."""

# API Endpoints (根据抓包数据修正)
API_USER_AUTH = "/api/v1/open/wechat/userAuthorization"
API_CREATE_QR_CODE = "/api/v1/open/wechat/createQRCode"
API_CHECK_QR_STATUS = "/api/v1/open/wechat/checkQRCodeStatus"
API_GET_USER_DEBT = "/api/v1/open/recharge/getUserDebtByUserCode"
API_GET_USER_DEBT_AUTH = "/api/v1/close/recharge/getUserDebt"  # 需要认证的版本，返回 userCodeList
API_GET_CUSTOMER_INFO = "/api/v1/close/user/getUserCode"
API_GET_METER_READING = "/api/v1/close/recharge/smartMeterGasDaysRecords"
API_GET_PAYMENT_RECORDS = "/api/v1/close/recharge/getPaymentRecordList"
API_GET_MONTHLY_VOLUME = "/api/v1/close/recharge/getMonthlyTotalGasVolume"
# Token refresh - userAuthorization endpoint (may accept refreshToken)
API_REFRESH_TOKEN = "/api/v1/open/wechat/userAuthorization"
# Password login endpoints (web version)
API_PASSWORD_LOGIN = "/api/v1/open/user/passwordLogin"
API_GET_COMPANIES = "/api/v1/open/company/list"
API_GET_RSA_PUBLIC_KEY = "/api/v1/open/encrypt/getRSA"

# Request Parameters (根据抓包数据修正)
PARAM_CID = "cid"
PARAM_USER_CODE = "userCode"
PARAM_TERMINAL_TYPE = "terminalType"
PARAM_USER_CODE_ID = "userCodeId"
PARAM_PAGE = "page"
PARAM_PAGE_SIZE = "pageSize"
PARAM_PAGE_NUMBER = "pageNumber"
PARAM_CODE = "code"
PARAM_UNION_ID = "unionId"
PARAM_LOGIN_ID = "loginId"
PARAM_QR_CODE_DATA = "qrCodeData"
PARAM_LENGTH_TIME_YQQS = "lengthTimeYqqs"
PARAM_TIMESTAMP = "timestamp"

# Fixed values from HAR analysis
DEFAULT_CID_NATIONWIDE = "99999"  # 全国查询

# Response Fields
FIELD_CODE = "code"
FIELD_DATA = "data"
FIELD_MESSAGE = "message"
FIELD_SUCCESS = "success"
FIELD_SUCCESS_WITH_DATA = "successWithData"

# API Base URL
API_BASE = "https://bol.grs.petrochina.com.cn"

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
