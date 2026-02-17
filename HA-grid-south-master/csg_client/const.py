"""Constants for csg_client"""

from enum import Enum

BASE_PATH_WEB = "https://95598.csg.cn/ucs/ma/wt/"
BASE_PATH_APP = "https://95598.csg.cn/ucs/ma/zt/"

# https://95598.csg.cn/js/app.1.6.177.1667607288138.js
PARAM_KEY = "cOdHFNHUNkZrjNaN".encode("utf8")
PARAM_IV = "oMChoRLZnTivcQyR".encode("utf8")
LOGON_CHANNEL_ONLINE_HALL = "3"  # web
LOGON_CHANNEL_HANDHELD_HALL = "4"  # app
RESP_STA_SUCCESS = "00"
RESP_STA_EMPTY_PARAMETER = "01"
RESP_STA_SYSTEM_ERROR = "02"
RESP_STA_NO_LOGIN = "04"
RESP_STA_QR_NOT_SCANNED = "09"
SESSION_KEY_LOGIN_TYPE = "10"


class LoginType(str, Enum):
    """Login type from JS"""

    LOGIN_TYPE_SMS = "11"
    LOGIN_TYPE_PWD_AND_SMS = "1011"
    LOGIN_TYPE_WX_QR = "20"
    LOGIN_TYPE_ALI_QR = "21"
    LOGIN_TYPE_CSG_QR = "30"


class QRCodeType(str, Enum):
    """QR code type used in creation API"""

    QR_CSG = "app"
    QR_WECHAT = "wechat"
    QR_ALIPAY = "alipay"


LOGIN_TYPE_TO_QR_CODE_TYPE = {
    LoginType.LOGIN_TYPE_CSG_QR: QRCodeType.QR_CSG,
    LoginType.LOGIN_TYPE_WX_QR: QRCodeType.QR_WECHAT,
    LoginType.LOGIN_TYPE_ALI_QR: QRCodeType.QR_ALIPAY,
}

AREACODE_FALLBACK = AREACODE_GUANGDONG = "030000"

# South China Power Grid area codes
# Note: 南网的地区编码系统中:
# - areaCode (省份代码): 6位, 如 050000 = 云南省
# - cityCode (城市代码): 6位, 如 050100 = 昆明市
# 但某些 API 可能返回 cityCode 作为 areaCode

AREACODE_MAPPING = {
    # Guangdong Province (03) - 省级代码
    "030000": "广东省",
    # Guangdong cities - 可能作为 areaCode 返回
    "030100": "广州市",
    "030200": "韶关市",
    "030300": "深圳市",
    "030600": "佛山市",
    "031700": "东莞市",
    # 新发现的深圳编码 (错误日志中出现的)
    "090000": "深圳市",  # 深圳特殊编码

    # Guangxi Province (04)
    "040000": "广西壮族自治区",
    "040100": "南宁市",

    # Yunnan Province (05)
    "050000": "云南省",
    "050100": "昆明市",  # 昆明的城市代码，可能被作为 areaCode 返回
    "050200": "曲靖市",
    "050300": "玉溪市",

    # Guizhou Province (06)
    "060000": "贵州省",
    "060100": "贵阳市",

    # Hainan Province (07)
    "070000": "海南省",
    "070100": "海口市",
}

# Reverse mapping for lookup
AREACODE_NAME_TO_CODE = {v: k for k, v in AREACODE_MAPPING.items()}

# City code to province code mapping
# Some APIs return city code as areaCode, need to convert to province code
CITY_CODE_TO_PROVINCE = {
    # Yunnan Province cities
    "050100": "050000",  # 昆明市 → 云南省
    "050200": "050000",  # 曲靖市 → 云南省
    "050300": "050000",  # 玉溪市 → 云南省

    # Guangdong Province cities
    "030100": "030000",  # 广州市 → 广东省
    "030200": "030000",  # 韶关市 → 广东省
    "030300": "030000",  # 深圳市 → 广东省
    "030600": "030000",  # 佛山市 → 广东省
    "031700": "030000",  # 东莞市 → 广东省

    # Guangxi Province cities
    "040100": "040000",  # 南宁市 → 广西

    # Guizhou Province cities
    "060100": "060000",  # 贵阳市 → 贵州

    # Hainan Province cities
    "070100": "070000",  # 海口市 → 海南
}

# https://95598.csg.cn/js/chunk-31aec193.1.6.177.1667607288138.js
CREDENTIAL_PUBKEY = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQD1RJE6GBKJlFQvTU6g0ws9R"
    "+qXFccKl4i1Rf4KVR8Rh3XtlBtvBxEyTxnVT294RVvYz6THzHGQwREnlgdkjZyGBf7tmV2CgwaHF+ttvupuzOmRVQ"
    "/difIJtXKM+SM0aCOqBk0fFaLiHrZlZS4qI2/rBQN8VBoVKfGinVMM+USswwIDAQAB"
)

# the value of these login types are the same as the enum above
# however they're not programmatically linked in the source code
# use them as seperated parameters for now
LOGIN_TYPE_PHONE_CODE = "11"
LOGIN_TYPE_PHONE_PWD_CODE = "1011"
SEND_MSG_TYPE_VERIFICATION_CODE = "1"
VERIFICATION_CODE_TYPE_LOGIN = "1"

# https://95598.csg.cn/js/chunk-49c87982.1.6.177.1667607288138.js
RESP_STA_QR_TIMEOUT = "00010001"

# from packet capture
RESP_STA_LOGIN_WRONG_CREDENTIAL = "00010002"

QR_EXPIRY_SECONDS = 300

# account object serialisation and deserialisation
ATTR_ACCOUNT_NUMBER = "account_number"
ATTR_AREA_CODE = "area_code"
ATTR_ELE_CUSTOMER_ID = "ele_customer_id"
ATTR_METERING_POINT_ID = "metering_point_id"
ATTR_METERING_POINT_NUMBER = "metering_point_number"
ATTR_ADDRESS = "address"
ATTR_USER_NAME = "user_name"
ATTR_AUTH_TOKEN = "auth_token"
ATTR_LOGIN_TYPE = "login_type"

# JSON/Headers used in raw APIs
HEADER_X_AUTH_TOKEN = "x-auth-token"
HEADER_CUST_NUMBER = "custNumber"
JSON_KEY_STA = "sta"
JSON_KEY_MESSAGE = "message"
JSON_KEY_CUST_NUMBER = "custNumber"
JSON_KEY_DATA = "data"
JSON_KEY_LOGON_CHAN = "logonChan"
JSON_KEY_SMS_CODE = "code"
JSON_KEY_CRED_TYPE = "credType"
JSON_KEY_AREA_CODE = "areaCode"
JSON_KEY_PARAM = "param"
JSON_KEY_ACCT_ID = "acctId"
JSON_KEY_ELE_CUST_ID = "eleCustId"
JSON_KEY_METERING_POINT_ID = "meteringPointId"
JSON_KEY_METERING_POINT_NUMBER = "meteringPointNumber"
JSON_KEY_YEAR_MONTH = "yearMonth"

# for wrapper functions
WF_ATTR_LADDER = "ladder"
WF_ATTR_LADDER_START_DATE = "start_date"
WF_ATTR_LADDER_REMAINING_KWH = "remaining_kwh"
WF_ATTR_LADDER_TARIFF = "tariff"

WF_ATTR_DATE = "date"
WF_ATTR_MONTH = "month"
WF_ATTR_CHARGE = "charge"
WF_ATTR_KWH = "kwh"
