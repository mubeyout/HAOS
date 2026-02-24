"""HTTP Client for Kunming Water API - Real Data Only."""
import logging
import re
from typing import Any, Optional
import hashlib

import aiohttp

from .const import WATER_LADDER_CONFIG

_LOGGER = logging.getLogger(__name__)


class KunmingWaterClient:
    """昆明水务 HTTP 客户端 - 仅使用真实数据"""

    def __init__(
        self,
        user_code: str,
        mobile: str,
        cookies_str: str = "",
        session: aiohttp.ClientSession = None,
    ):
        """
        初始化客户端

        Args:
            user_code: 户号
            mobile: 手机号（用于认证）
            cookies_str: 保存的 cookies JSON 字符串
            session: 可选的 aiohttp 会话
        """
        self.user_code = user_code
        self.mobile = mobile
        self._session = session or aiohttp.ClientSession()
        self._logged_in = False

        # 恢复 cookies 到 session
        if cookies_str:
            self._restore_cookies(cookies_str)
            self._logged_in = True

    def _restore_cookies(self, cookies_str: str) -> None:
        """将 JSON 格式的 cookies 恢复到 session 的 cookie_jar 中"""
        if not cookies_str:
            return

        try:
            import json
            cookies_list = json.loads(cookies_str)
        except:
            # 如果解析失败，尝试旧的字符串格式
            self._restore_cookies_legacy(cookies_str)
            return

        jar = self._session.cookie_jar
        for cookie_data in cookies_list:
            key = cookie_data.get("key")
            value = cookie_data.get("value")
            domain = cookie_data.get("domain")
            path = cookie_data.get("path", "/")

            if key and value:
                # 使用正确的 cookie 设置方法
                jar.update_cookies({key: value})

        _LOGGER.debug(f"Restored {len(cookies_list)} cookies to session")

    def _restore_cookies_legacy(self, cookies_str: str) -> None:
        """旧的字符串格式 cookie 恢复（向后兼容）"""
        jar = self._session.cookie_jar

        for cookie_pair in cookies_str.split(";"):
            cookie_pair = cookie_pair.strip()
            if "=" in cookie_pair:
                key, value = cookie_pair.split("=", 1)
                key = key.strip()
                value = value.strip()

                # 使用正确的 cookie 设置方法
                jar.update_cookies({key: value})

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://km96106.cn/browserClient/index/index.action",
        }

    async def close(self) -> None:
        """关闭客户端会话"""
        if self._session:
            await self._session.close()

    async def login_with_sms(self, sms_code: str) -> bool:
        """
        使用短信验证码登录

        Args:
            sms_code: 短信验证码

        Returns:
            登录是否成功
        """
        url = "https://km96106.cn/browserClient/index/login.action"

        # 使用默认密码（API 要求）
        default_password = "123456"
        password_md5 = hashlib.md5(default_password.encode('utf-8')).hexdigest()

        form_data = {
            "txtUserName": self.mobile,
            "txtPassword": password_md5,
            "loginCheckType": "valiCode",
            "vercode": sms_code,
            "account.username": self.mobile,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://km96106.cn/browserClient/index/index.action",
            "Origin": "https://km96106.cn",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            async with self._session.post(
                url,
                data=form_data,
                headers=headers,
                timeout=15,
                allow_redirects=True
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    _LOGGER.debug(f"Login response: {text[:200]}")

                    if '"flag":true' in text or 'flag==true' in text:
                        self._logged_in = True
                        _LOGGER.info("SMS login successful")

                        # 登录成功后访问账户主页以建立完整 session
                        await self._session.get(
                            "https://km96106.cn/browserClient/account/accountHome.action",
                            headers={
                                "User-Agent": headers["User-Agent"],
                                "Referer": "https://km96106.cn/browserClient/index/index.action",
                            },
                            timeout=15
                        )
                        return True
                    else:
                        # 尝试提取错误信息
                        import re
                        error_match = re.search(r'"msg"[:\s]+"([^"]+)"', text)
                        error_msg = error_match.group(1) if error_match else text[:100]
                        _LOGGER.error(f"Login failed: {error_msg}")
                        return False
                else:
                    _LOGGER.error(f"Login failed with status {resp.status}: {await resp.text()}")
                    return False

        except Exception as err:
            _LOGGER.error(f"Login error: {err}")
            return False

    async def get_user_info(self) -> Optional[dict]:
        """
        获取用户信息

        Returns:
            用户信息字典，失败返回 None
        """
        if not self._logged_in:
            _LOGGER.warning("Not logged in, cannot get user info")
            return None

        # 尝试获取用户信息
        url = "https://km96106.cn/browserClient/index/getUserInfo.action"

        form_data = {
            "userCode": self.user_code,
        }

        headers = self._get_headers()

        try:
            async with self._session.post(
                url,
                data=form_data,
                headers=headers,
                timeout=15
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("flag"):
                        data = result.get("data", {})
                        return {
                            "userName": data.get("userName"),
                            "address": data.get("address"),
                            "userCode": data.get("userCode", self.user_code),
                            "mobile": self.mobile,
                        }
                    else:
                        _LOGGER.warning(f"Failed to get user info: {result.get('msg')}")
                        return None
                else:
                    _LOGGER.warning(f"User info API returned status {resp.status}")
                    return None

        except Exception as err:
            _LOGGER.error(f"Error getting user info: {err}")
            return None

    async def get_bill_list(self, limit: int = 5) -> Optional[list]:
        """
        获取账单列表

        Args:
            limit: 返回记录数量

        Returns:
            账单列表，失败返回 None
        """
        if not self._logged_in:
            _LOGGER.warning("Not logged in, cannot get bill list")
            return None

        url = "https://km96106.cn/browserClient/recharge/getBillList.action"

        form_data = {
            "userCode": self.user_code,
            "pageSize": limit,
        }

        headers = self._get_headers()

        try:
            async with self._session.post(
                url,
                data=form_data,
                headers=headers,
                timeout=15
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("flag"):
                        return result.get("data", [])
                    else:
                        _LOGGER.warning(f"Failed to get bill list: {result.get('msg')}")
                        return None
                elif resp.status == 404:
                    _LOGGER.warning("Bill list API not found (404)")
                    return None
                else:
                    _LOGGER.warning(f"Bill list API returned status {resp.status}")
                    return None

        except Exception as err:
            _LOGGER.error(f"Error getting bill list: {err}")
            return None

    async def get_usage_list(self, days: int = 30) -> Optional[dict]:
        """
        获取用水量列表

        Args:
            days: 查询天数

        Returns:
            用水量记录字典，失败返回 None
        """
        if not self._logged_in:
            _LOGGER.warning("Not logged in, cannot get usage list")
            return None

        url = "https://km96106.cn/browserClient/recharge/getUsageList.action"

        form_data = {
            "userCode": self.user_code,
            "days": days,
        }

        headers = self._get_headers()

        try:
            async with self._session.post(
                url,
                data=form_data,
                headers=headers,
                timeout=15
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("flag"):
                        data = result.get("data", {})
                        if isinstance(data, list):
                            return {"list": data, "total": sum(item.get("volume", 0) for item in data)}
                        return data
                    else:
                        _LOGGER.warning(f"Failed to get usage list: {result.get('msg')}")
                        return None
                elif resp.status == 404:
                    _LOGGER.warning("Usage list API not found (404)")
                    return None
                else:
                    _LOGGER.warning(f"Usage list API returned status {resp.status}")
                    return None

        except Exception as err:
            _LOGGER.error(f"Error getting usage list: {err}")
            return None

    async def get_ticket(self) -> Optional[str]:
        """
        从账户主页获取 ticket

        Returns:
            ticket 字符串，失败返回 None
        """
        if not self._logged_in:
            _LOGGER.warning("Not logged in, cannot get ticket")
            return None

        url = "https://km96106.cn/browserClient/account/accountHome.action"
        headers = self._get_headers()

        try:
            async with self._session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # 从 HTML 中提取 ticket
                    # 查找 localStorage.ticket = '...' 或类似模式
                    ticket_pattern = r"localStorage\.ticket\s*=\s*['\"]([^'\"]+)['\"]"
                    matches = re.findall(ticket_pattern, html)
                    if matches:
                        ticket = matches[0]
                        _LOGGER.debug(f"Found ticket: {ticket[:20]}...")
                        return ticket
                    else:
                        _LOGGER.warning("Ticket not found in HTML")
                        return None
                else:
                    _LOGGER.warning(f"Account home returned status {resp.status}")
                    return None

        except Exception as err:
            _LOGGER.error(f"Error getting ticket: {err}")
            return None

    async def get_bill_chart_data(self, ticket: str = None) -> Optional[dict]:
        """
        获取账单图表数据（包含用水趋势和账单记录）

        Args:
            ticket: 可选的 ticket，如果不提供则尝试获取

        Returns:
            包含用水户信息、账单列表的字典，失败返回 None
        """
        if not self._logged_in:
            _LOGGER.warning("Not logged in, cannot get bill chart data")
            return None

        # 如果没有提供 ticket，尝试获取
        if not ticket:
            ticket = await self.get_ticket()
            if not ticket:
                _LOGGER.error("Cannot get bill chart data without ticket")
                return None

        url = "https://km96106.cn/browserClient/billChart/loadData.action"

        form_data = {
            "ticket": ticket,
            "userCode": self.user_code,
        }

        headers = {
            **self._get_headers(),
            "Referer": "https://km96106.cn/browserClient/billChart/chartIndex.action",
            "Origin": "https://km96106.cn",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            async with self._session.post(
                url,
                data=form_data,
                headers=headers,
                timeout=15
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("success"):
                        return result
                    else:
                        _LOGGER.warning(f"Failed to get bill chart data: {result.get('msg')}")
                        return None
                else:
                    _LOGGER.warning(f"Bill chart API returned status {resp.status}")
                    return None

        except Exception as err:
            _LOGGER.error(f"Error getting bill chart data: {err}")
            return None

    @staticmethod
    def calculate_ladder_stage(total_usage: float) -> dict:
        """
        根据用水量计算阶梯价格

        Args:
            total_usage: 总用水量（立方米）

        Returns:
            包含阶梯信息的字典
        """
        for tier in WATER_LADDER_CONFIG:
            if total_usage <= tier["max_volume"]:
                return {
                    "stage": tier["stage"],
                    "unit_price": tier["unit_price"],
                    "monthly_usage": total_usage,
                }

        # 默认返回最高阶梯
        return {
            "stage": WATER_LADDER_CONFIG[-1]["stage"],
            "unit_price": WATER_LADDER_CONFIG[-1]["unit_price"],
            "monthly_usage": total_usage,
        }
