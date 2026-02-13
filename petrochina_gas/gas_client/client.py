"""HTTP Client for Gas API."""

import logging
import requests
import json
import base64
from typing import Optional, Tuple, Dict, Any

from .const import (
    API_BASE,
    API_USER_AUTH,
    API_CREATE_QR_CODE,
    API_CHECK_QR_STATUS,
    API_GET_USER_DEBT,
    API_GET_CUSTOMER_INFO,
    API_GET_METER_READING,
    API_GET_PAYMENT_RECORDS,
    API_GET_MONTHLY_VOLUME,
    PARAM_CID,
    PARAM_USER_CODE,
    PARAM_TERMINAL_TYPE,
    PARAM_USER_CODE_ID,
    PARAM_PAGE,
    PARAM_PAGE_SIZE,
    PARAM_PAGE_NUMBER,
    PARAM_CODE,
    PARAM_UNION_ID,
    PARAM_LOGIN_ID,
    PARAM_QR_CODE_DATA,
    FIELD_CODE,
    FIELD_DATA,
    FIELD_MESSAGE,
    FIELD_SUCCESS,
    FIELD_SUCCESS_WITH_DATA,
    DATA_ACCOUNT_ID,
    DATA_ADDRESS,
    DATA_CUSTOMER_NAME,
    DATA_REMOTE_METER_BALANCE,
    DATA_METER_TYPE,
    DATA_MDM_CODE,
    DATA_READING_LAST_TIME,
    DATA_REMOTE_METER_LAST_COMMUNICATION_TIME,
    DATA_RATE_ITEM_INFO,
)
from .models import GasAccount, LadderPricing, CSGAPIError

_LOGGER = logging.getLogger(__name__)


class GasHttpClient:
    """昆仑燃气 HTTP 客户端"""

    def __init__(self, user_code: Optional[str] = None, cid: int = 2, terminal_type: int = 7):
        """
        初始化客户端

        Args:
            user_code: 燃气户号（8位数字），可选（用于扫码登录时不需要）
            cid: 地区代码（默认为2，昆明分公司）
            terminal_type: 终端类型（默认为7）
        """
        self.user_code = user_code
        self.cid = cid
        self.terminal_type = terminal_type

        # Session 和 Token 管理
        self._session = requests.Session()
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._open_id: Optional[str] = None
        self._mdm_code: Optional[str] = None

        # 设置默认请求头
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.47(0x18002f2f) NetType/WIFI Language/zh_CN",
            "Content-Type": "application/json;charset=UTF-8",
        })

    def _make_request(self, url: str, method: str = "POST", data: Optional[dict] = None,
                   requires_auth: bool = False) -> requests.Response:
        """发送HTTP请求"""
        full_url = f"{API_BASE}{url}"
        headers = dict(self._session.headers)

        # 如果需要认证且已有token，添加到请求头
        if requires_auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
            _LOGGER.debug("Using Bearer token for authentication")

        _LOGGER.debug(f"Request: {method} {full_url}")
        if data:
            _LOGGER.debug(f"  Data: {json.dumps(data, ensure_ascii=False)}")

        try:
            response = self._session.post(full_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as err:
            _LOGGER.error(f"Request failed: {err}")
            raise
        except requests.Timeout as err:
            _LOGGER.error(f"Request timeout: {err}")
            raise
        except Exception as err:
            _LOGGER.error(f"Unexpected error: {err}")
            raise

    def _parse_response(self, response: requests.Response) -> dict:
        """解析API响应"""
        try:
            data = response.json()
            if data.get(FIELD_SUCCESS) or data.get(FIELD_SUCCESS_WITH_DATA):
                return data.get(FIELD_DATA, {})
            else:
                _LOGGER.warning(f"API returned error: {data.get(FIELD_MESSAGE, data)}")
                return {"error": data.get(FIELD_MESSAGE, "Unknown error")}
        except json.JSONDecodeError as err:
            _LOGGER.error(f"Failed to parse JSON response: {err}")
            return {"error": f"JSON decode error: {err}"}

    def login(self, wechat_code: str, union_id: str) -> bool:
        """
        使用微信授权码登录

        Args:
            wechat_code: 微信授权码
            union_id: 微信OpenID

        Returns:
            登录是否成功
        """
        url = API_USER_AUTH
        data = {
            PARAM_CID: "99999",  # 全国查询
            PARAM_CODE: wechat_code,
            PARAM_UNION_ID: union_id,
        }

        _LOGGER.info(f"Logging in with wechat code: {wechat_code}")

        try:
            response = self._make_request(url, data=data, requires_auth=False)
            content = response.content.decode('utf-8')

            # 响应是 base64 编码的
            if content and not content.strip().startswith('{'):
                decoded_bytes = base64.b64decode(content)
                content = decoded_bytes.decode('utf-8')

            result = json.loads(content)

            if result.get(FIELD_SUCCESS) or result.get(FIELD_SUCCESS_WITH_DATA):
                data = result.get(FIELD_DATA, {})

                # 存储token和用户信息
                self._token = data.get("token")
                self._refresh_token = data.get("refreshToken")
                self._open_id = data.get("openId")
                self._mdm_code = data.get("mdmCode")

                _LOGGER.info(f"Login successful for user: {data.get('mobile', 'unknown')}")
                _LOGGER.debug(f"MDM code: {self._mdm_code}")

                # 更新session默认请求头，添加Authorization
                if self._token:
                    self._session.headers["Authorization"] = f"Bearer {self._token}"

                return True
            else:
                _LOGGER.error(f"Login failed: {result.get(FIELD_MESSAGE, 'Unknown error')}")
                return False

        except Exception as err:
            _LOGGER.error(f"Login error: {err}")
            return False

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self._token is not None

    def get_user_debt(self) -> Optional[GasAccount]:
        """
        查询用户余额（公开API，无需认证）

        Returns:
            包含余额等信息的字典
        """
        url = API_GET_USER_DEBT
        data = {
            PARAM_CID: self.cid,
            PARAM_USER_CODE: self.user_code,
            PARAM_TERMINAL_TYPE: self.terminal_type,
        }

        _LOGGER.info(f"Querying user debt: {self.user_code}")
        response = self._make_request(url, data=data, requires_auth=False)
        result = self._parse_response(response)

        if "error" in result:
            _LOGGER.error(f"Failed to get user debt: {result['error']}")
            return None

        account_data = result
        return GasAccount(
            account_id=account_data.get(DATA_ACCOUNT_ID, ""),
            user_code=account_data.get(PARAM_USER_CODE, self.user_code),
            customer_name=account_data.get(DATA_CUSTOMER_NAME, ""),
            address=account_data.get(DATA_ADDRESS, ""),
            remote_meter_balance=float(account_data.get(DATA_REMOTE_METER_BALANCE, 0)),
            meter_type=account_data.get(DATA_METER_TYPE, ""),
            mdm_code=account_data.get(DATA_MDM_CODE, ""),
            reading_last_time=account_data.get(DATA_READING_LAST_TIME, ""),
            remote_meter_last_communication_time=account_data.get(DATA_REMOTE_METER_LAST_COMMUNICATION_TIME, ""),
        )

    def get_customer_info(self) -> Optional[GasAccount]:
        """
        查询客户详细信息（需要认证）

        Returns:
            GasAccount 对象
        """
        if not self.is_logged_in():
            _LOGGER.error("Not logged in. Please login first.")
            return None

        url = API_GET_CUSTOMER_INFO
        data = {
            PARAM_CID: self.cid,
            PARAM_USER_CODE: self.user_code,
            PARAM_TERMINAL_TYPE: self.terminal_type,
            PARAM_USER_CODE_ID: "",
        }

        _LOGGER.info(f"Querying customer info: {self.user_code}")
        response = self._make_request(url, data=data, requires_auth=True)
        result = self._parse_response(response)

        if "error" in result:
            _LOGGER.error(f"Failed to get customer info: {result['error']}")
            return None

        # get_user_debt 和 get_customer_info 返回的数据结构可能相同
        return self.get_user_debt()

    def get_meter_reading(self, days: int = 30) -> Optional[list]:
        """
        查询表计读数（需要认证）

        Args:
            days: 查询天数（默认30天）

        Returns:
            表计读数列表，每个元素包含日期、读数、用量等
        """
        if not self.is_logged_in():
            _LOGGER.error("Not logged in. Please login first.")
            return None

        # 使用新的URL格式: /api/v1/close/recharge/smartMeterGasDaysRecords/{mdmCode}/{userCode}
        mdm_code = self._mdm_code or "9AH1"
        url = f"/api/v1/close/recharge/smartMeterGasDaysRecords/{mdm_code}/{self.user_code}"
        data = {}

        _LOGGER.info(f"Querying meter reading ({days} days): {self.user_code}")
        response = self._make_request(url, data=data, requires_auth=True)
        result = self._parse_response(response)

        if "error" in result:
            _LOGGER.error(f"Failed to get meter reading: {result['error']}")
            return None

        # 解析返回数据
        account_data = result
        if account_data:
            return [{
                "date": record.get("readingLastTime", ""),
                "reading": float(record.get("remoteMeterBalance", 0)),
                "volume": float(record.get("gasVolume", 0)),
                "cost": float(record.get("gasFee", 0)),
            } for record in account_data.get("smartMeterGasDaysRecords", [])]
        return []

    def get_daily_usage(self, days: int = 30) -> Optional[dict]:
        """
        查询每日用气量统计（需要认证）

        Args:
            days: 查询天数（默认30天）

        Returns:
            包含每日用气量统计的字典
        """
        if not self.is_logged_in():
            _LOGGER.error("Not logged in. Please login first.")
            return None

        mdm_code = self._mdm_code or "9AH1"
        url = f"/api/v1/close/recharge/smartMeterGasDaysRecords/{mdm_code}/{self.user_code}"
        data = {}

        _LOGGER.info(f"Querying daily usage ({days} days): {self.user_code}")
        response = self._make_request(url, data=data, requires_auth=True)
        result = self._parse_response(response)

        if "error" in result:
            _LOGGER.error(f"Failed to get daily usage: {result['error']}")
            return None

        # 解析返回数据并汇总
        daily_volumes = []
        if result:
            records = result.get("smartMeterGasDaysRecords", [])
            for record in records:
                daily_volumes.append({
                    "date": record.get("readingLastTime", "")[:10],
                    "volume": float(record.get("gasVolume", 0)),
                    "cost": float(record.get("gasFee", 0)),
                })

        return {
            "daily_volumes": daily_volumes,
            "total_volume": sum(d["volume"] for d in daily_volumes),
            "total_cost": sum(d["cost"] for d in daily_volumes),
        }

    def get_payment_records(self, page: int = 1, page_size: int = 10, user_code_id: str = "") -> Optional[dict]:
        """
        查询缴费记录（需要认证）

        Args:
            page: 页码（默认1）
            page_size: 每页数量（默认10）
            user_code_id: 用户代码ID（可选）

        Returns:
            缴费记录列表
        """
        if not self.is_logged_in():
            _LOGGER.error("Not logged in. Please login first.")
            return None

        url = API_GET_PAYMENT_RECORDS
        data = {
            PARAM_CID: self.cid,
            PARAM_PAGE_NUMBER: page,
            PARAM_PAGE_SIZE: page_size,
        }
        if user_code_id:
            data[PARAM_USER_CODE_ID] = user_code_id

        _LOGGER.info(f"Querying payment records: {self.user_code}")
        response = self._make_request(url, data=data, requires_auth=True)
        result = self._parse_response(response)

        if "error" in result:
            _LOGGER.error(f"Failed to get payment records: {result['error']}")
            return None

        return result

    def get_monthly_usage(self, page: int = 1, page_size: int = 7) -> Optional[dict]:
        """
        查询月度用气量统计（需要认证）

        Args:
            page: 页码（默认1）
            page_size: 每页数量（默认7）

        Returns:
            月度用气量和阶梯价格信息
        """
        if not self.is_logged_in():
            _LOGGER.error("Not logged in. Please login first.")
            return None

        url = API_GET_MONTHLY_VOLUME
        data = {
            PARAM_CID: self.cid,
            PARAM_USER_CODE: self.user_code,
            PARAM_PAGE: page,
            PARAM_PAGE_SIZE: page_size,
        }

        _LOGGER.info(f"Querying monthly usage: {self.user_code}")
        response = self._make_request(url, data=data, requires_auth=True)

        # 解析 base64 响应
        try:
            content = response.content.decode('utf-8')
            # 检查是否是 base64 编码
            if content and not content.strip().startswith('{'):
                decoded_bytes = base64.b64decode(content)
                content = decoded_bytes.decode('utf-8')
                result = json.loads(content)
            else:
                result = json.loads(content)

            if result.get(FIELD_SUCCESS) or result.get(FIELD_SUCCESS_WITH_DATA):
                return result.get(FIELD_DATA, {})
            else:
                _LOGGER.warning(f"API returned error: {result.get(FIELD_MESSAGE, result)}")
                return {"error": result.get(FIELD_MESSAGE, "Unknown error")}
        except Exception as err:
            _LOGGER.error(f"Failed to parse monthly usage response: {err}")
            return {"error": f"Parse error: {err}"}

    def get_ladder_pricing(self) -> Optional[dict]:
        """
        查询阶梯价格信息（通过月度用量接口获取）

        Returns:
            阶梯价格配置字典，包含各档位价格
        """
        monthly_data = self.get_monthly_usage(page=1, page_size=1)

        if monthly_data and "error" not in monthly_data:
            rate_items = monthly_data.get(DATA_RATE_ITEM_INFO, [])

            # 解析阶梯价格
            result = {
                "current_ladder": 1,  # 需要根据累计用量计算
                "ladder_1": {},
                "ladder_2": {},
                "ladder_3": {},
            }

            for item in rate_items:
                rate_name = item.get("rateName", "")
                if "第一" in rate_name or "1" in rate_name:
                    result["ladder_1"] = {
                        "price": float(item.get("price", 0)),
                        "start": float(item.get("beginVolume", 0)),
                        "end": float(item.get("endVolume", 0)),
                    }
                elif "第二" in rate_name or "2" in rate_name:
                    result["ladder_2"] = {
                        "price": float(item.get("price", 0)),
                        "start": float(item.get("beginVolume", 0)),
                        "end": float(item.get("endVolume", 0)),
                    }
                elif "第三" in rate_name or "3" in rate_name:
                    result["ladder_3"] = {
                        "price": float(item.get("price", 0)),
                        "start": float(item.get("beginVolume", 0)),
                        "end": float(item.get("endVolume", 0)),
                    }

            return result

        return None

    def create_login_qr_code(self) -> tuple[str, str]:
        """
        生成登录二维码

        Returns:
            (login_id, image_link): login_id用于后续查询状态，image_link是二维码图片URL
        """
        import time

        url = f"{API_BASE}{API_CREATE_QR_CODE}"

        payload = {
            PARAM_CID: self.cid,
            PARAM_TERMINAL_TYPE: self.terminal_type,
            "timestamp": int(time.time() * 1000),
        }

        try:
            response = self._make_request(url, data=payload, requires_auth=False)
            data = response.json()

            if data.get(FIELD_SUCCESS) or data.get(FIELD_SUCCESS_WITH_DATA):
                login_id = data.get(FIELD_DATA, {}).get("loginId", "")
                image_url = data.get(FIELD_DATA, {}).get("qrCodeUrl", "")
                _LOGGER.info(f"QR code created: login_id={login_id}")
                return login_id, image_url
            else:
                from . import CSGAPIError
                raise CSGAPIError(data.get(FIELD_MESSAGE, "生成二维码失败"))
        except Exception as err:
            _LOGGER.error(f"Failed to create QR code: {err}")
            raise

    def check_qr_login_status(self, login_id: str) -> Tuple[bool, Optional[str]]:
        """
        查询二维码扫描状态

        Args:
            login_id: 二维码登录ID

        Returns:
            (success, auth_token): success是否成功，auth_token是登录后的token
        """
        url = f"{API_BASE}{API_CHECK_QR_STATUS}"

        payload = {
            PARAM_LOGIN_ID: login_id,
            PARAM_CID: self.cid,
        }

        try:
            response = self._make_request(url, data=payload, requires_auth=False)
            data = response.json()

            logged_in = data.get("logged_in", False)
            if logged_in:
                # 用户已扫码登录，获取token
                token = data.get(FIELD_DATA, {}).get("token", "")
                union_id = data.get(FIELD_DATA, {}).get("unionId", "")
                mdm_code = data.get(FIELD_DATA, {}).get("mdmCode", "")

                # 更新session
                self._token = token
                self._refresh_token = None
                self._open_id = union_id
                self._mdm_code = mdm_code

                # 更新session请求头
                if self._token:
                    self._session.headers["Authorization"] = f"Bearer {self._token}"

                _LOGGER.info(f"QR login successful, token received")
                return True, token
            else:
                return False, None
        except Exception as err:
            _LOGGER.error(f"Failed to check QR status: {err}")
            raise

    def close(self):
        """关闭客户端会话"""
        self._session.close()
        _LOGGER.debug("HTTP client session closed")
