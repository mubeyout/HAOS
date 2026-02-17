"""Config flow for Kunming Water integration."""
import logging
from typing import Any

import voluptuous as vol
import aiohttp
import hashlib
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_USER_CODE,
    CONF_MOBILE,
    CONF_PASSWORD,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USER_CODE): vol.All(
        vol.Coerce(str),
        vol.Length(min=6, max=20),
    ),
    vol.Required(CONF_MOBILE): vol.All(
        vol.Coerce(str),
        vol.Length(min=11, max=11),
    ),
})

STEP_SMS_DATA_SCHEMA = vol.Schema({
    vol.Required("sms_code"): vol.All(
        vol.Coerce(str),
        vol.Length(min=6, max=6),
    ),
})


class KunmingWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kunming Water."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._user_code: str | None = None
        self._mobile: str | None = None
        self._session: aiohttp.ClientSession | None = None
        self._cookies: str | None = None  # 保存登录后的 cookies
        self._user_info: dict[str, Any] | None = None  # 保存用户信息

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - collect credentials."""
        errors = {}

        if user_input is not None:
            # Validate input
            errors = await self._validate_input(user_input)

            if not errors:
                # Store credentials
                self._user_code = user_input[CONF_USER_CODE]
                self._mobile = user_input[CONF_MOBILE]

                # Send SMS verification code
                result = await self._send_sms_code()

                if result.get("code") == 1:
                    # SMS sent successfully, move to SMS code step
                    return await self.async_step_sms()

                # If SMS failed, show error
                errors["base"] = result.get("message", "发送验证码失败，请重试")

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_sms(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle SMS verification code step."""
        errors = {}

        if user_input is not None:
            sms_code = user_input.get("sms_code", "").strip()

            if not sms_code:
                errors["sms_code"] = "请输入验证码"
            elif len(sms_code) != 6:
                errors["sms_code"] = "验证码应为6位数字"
            else:
                # Verify SMS code
                result = await self._verify_sms_code(sms_code)

                if result.get("success"):
                    # Check if already configured
                    await self.async_set_unique_id(self._user_code)
                    self._abort_if_unique_id_configured()

                    # Convert cookies to string for storage
                    cookies_str = self._cookies or ""

                    # Prepare user info data
                    user_info = self._user_info or {}

                    # Create entry with cookies and user info
                    entry = self.async_create_entry(
                        title=f"昆明水务 {self._user_code}",
                        data={
                            CONF_USER_CODE: self._user_code,
                            CONF_MOBILE: self._mobile,
                            "cookies": cookies_str,
                            # 保存用户基本信息供传感器显示
                            "user_name": user_info.get("userName"),
                            "address": user_info.get("address"),
                            "caliber": user_info.get("caliber"),
                            "cycle": user_info.get("cycle"),
                            # 保存账单列表
                            "bill_list": user_info.get("bill_list", []),
                        },
                    )

                    # Clean up session
                    if self._session:
                        await self._session.close()
                        self._session = None

                    return entry
                else:
                    errors["sms_code"] = result.get("message", "验证码错误")

        # Show description with the mobile number
        return self.async_show_form(
            step_id="sms",
            data_schema=STEP_SMS_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "mobile": f"{self._mobile[:3]}****{self._mobile[-4:]}"
            },
        )

    async def _send_sms_code(self) -> dict:
        """Send SMS verification code."""
        url = "https://km96106.cn/other/common/getValiCode.do"

        # Prepare parameters
        import json
        para = {"phone": self._mobile, "captcha": ""}
        para_json = json.dumps(para)
        para_hex = para_json.encode('utf-8').hex()

        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            async with self._session.post(url, data={"ticket": para_hex}, headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            }, timeout=15) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    _LOGGER.info(f"SMS code sent: {result}")
                    return result
                return {"code": -1, "message": f"HTTP {resp.status}"}

        except Exception as e:
            _LOGGER.error(f"Failed to send SMS: {e}")
            return {"code": -1, "message": str(e)}

    async def _verify_sms_code(self, sms_code: str) -> dict:
        """Verify SMS code and login."""
        # Use a default password for API (required by the API even for SMS login)
        default_password = "123456"
        password_md5 = hashlib.md5(default_password.encode('utf-8')).hexdigest()

        url = "https://km96106.cn/browserClient/index/login.action"

        form_data = {
            "txtUserName": self._mobile,
            "txtPassword": password_md5,
            "loginCheckType": "valiCode",
            "vercode": sms_code,
            "account.username": self._mobile,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://km96106.cn/browserClient/index/index.action",
        }

        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            # 登录
            login_resp = await self._session.post(
                url,
                data=form_data,
                headers=headers,
                timeout=15,
                allow_redirects=True
            )

            if login_resp.status != 200:
                return {"success": False, "message": f"登录失败，HTTP状态码: {login_resp.status}"}

            login_text = await login_resp.text()
            if '"flag":true' not in login_text and 'flag==true' not in login_text:
                import re
                error_match = re.search(r'"msg"[:\s]+"([^"]+)"', login_text)
                error_msg = error_match.group(1) if error_match else "验证码错误或已过期"
                return {"success": False, "message": error_msg}

            _LOGGER.info(f"SMS login successful, session cookies: {self._session.cookie_jar}")

            # 访问账户主页以设置 session
            home_url = "https://km96106.cn/browserClient/account/accountHome.action"
            await self._session.get(home_url, headers=headers, timeout=15)

            # 获取 ticket（从账户主页 HTML）
            ticket = None
            try:
                async with self._session.get(home_url, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        import re
                        ticket_pattern = r"localStorage\.ticket\s*=\s*['\"]([^'\"]+)['\"]"
                        matches = re.findall(ticket_pattern, html)
                        if matches:
                            ticket = matches[0]
                            _LOGGER.info(f"Found ticket: {ticket[:20]}...")
            except Exception as e:
                _LOGGER.warning(f"Failed to get ticket: {e}")

            # 使用新发现的 API 验证登录并获取用水数据
            bill_chart_url = "https://km96106.cn/browserClient/billChart/loadData.action"
            bill_chart_data = {"ticket": ticket, "userCode": self._user_code} if ticket else {"userCode": self._user_code}

            bill_resp = await self._session.post(
                bill_chart_url,
                data=bill_chart_data,
                headers={**headers, "X-Requested-With": "XMLHttpRequest"},
                timeout=15
            )

            if bill_resp.status == 200:
                import json
                bill_result = await bill_resp.json()

                if bill_result.get("success"):
                    water_info = bill_result.get("waterInfo", {})
                    bill_list = bill_result.get("billList", [])

                    _LOGGER.info(f"Login verified, water user: {water_info.get('waterUser')}, bills: {len(bill_list)}")

                    # 保存用户信息
                    self._user_info = {
                        "userName": water_info.get("waterUser"),
                        "address": water_info.get("waterAddress"),
                        "userCode": water_info.get("waterNo", self._user_code),
                        "caliber": water_info.get("caliber"),
                        "cycle": water_info.get("cycle"),
                    }

                    # 保存账单数据
                    if bill_list:
                        self._user_info["bill_list"] = bill_list
                        self._user_info["latest_bill"] = bill_list[0]

                else:
                    error_msg = bill_result.get("msg", "无法获取用水数据")
                    _LOGGER.warning(f"Bill chart API returned: {error_msg}")
                    # 继续处理，但记录警告
            else:
                _LOGGER.warning(f"Bill chart API returned status {bill_resp.status}")

            # 保存 cookies
            import json
            cookies_list = []
            for cookie in self._session.cookie_jar:
                cookies_list.append({
                    "key": cookie.key,
                    "value": cookie.value,
                    "domain": cookie["domain"] if "domain" in cookie else None,
                    "path": cookie["path"] if "path" in cookie else None,
                })
            self._cookies = json.dumps(cookies_list)

            # 保存 ticket（如果获取到）
            if ticket:
                if self._user_info is None:
                    self._user_info = {}
                self._user_info["ticket"] = ticket

            _LOGGER.info(f"Saved {len(cookies_list)} cookies" + (f" and ticket" if ticket else ""))

            return {"success": True}

        except Exception as e:
            _LOGGER.error(f"Failed to verify SMS: {e}")
            return {"success": False, "message": f"验证失败: {str(e)}"}

    async def _validate_input(self, user_input: dict[str, Any]) -> dict:
        """Validate the user input."""
        errors = {}

        # Validate user_code
        user_code = str(user_input.get(CONF_USER_CODE, "")).strip()
        if not user_code:
            errors[CONF_USER_CODE] = "户号不能为空"
        elif not user_code.isdigit():
            errors[CONF_USER_CODE] = "户号应为纯数字"

        # Validate mobile
        mobile = str(user_input.get(CONF_MOBILE, "")).strip()
        if not mobile:
            errors[CONF_MOBILE] = "手机号不能为空"
        elif len(mobile) != 11 or not mobile.isdigit():
            errors[CONF_MOBILE] = "请输入正确的11位手机号"

        return errors

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return KunmingWaterOptionsFlow(config_entry)


class KunmingWaterOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Kunming Water."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_USER_CODE,
                    default=self.config_entry.data.get(CONF_USER_CODE, ""),
                ): str,
                vol.Optional(
                    CONF_MOBILE,
                    default=self.config_entry.data.get(CONF_MOBILE, ""),
                ): str,
            }),
        )
