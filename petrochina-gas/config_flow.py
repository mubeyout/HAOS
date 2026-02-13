"""Config flow for PetroChina Gas integration."""

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_USER_CODE,
    CONF_CID,
    CONF_TERMINAL_TYPE,
    CONF_ACCOUNTS,
    CONF_SETTINGS,
)
from .gas_client import GasHttpClient, CSGAPIError

_LOGGER = logging.getLogger(__name__)

# Step identifiers
STEP_USER = "user"
STEP_QR_LOGIN = "qr_login"
STEP_ACCOUNT = "account"
STEP_CONFIRM = "confirm"


class PetrochinaGasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """昆仑燃气配置流程"""

    VERSION = 1

    def __init__(self) -> None:
        """初始化配置流程"""
        self._qr_login_id: str | None = None
        self._qr_image_url: str | None = None
        self._wechat_code: str | None = None
        self._union_id: str | None = None
        self._user_code: str | None = None
        self._cid: int = 2
        self._terminal_type: int = 7
        self._auth_token: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """第一步：选择登录方式"""
        if user_input is None:
            return self.async_show_menu(
                step_id=STEP_USER,
                menu_options=[
                    STEP_QR_LOGIN,
                    "manual_login",
                    "skip_login",
                ],
            )

        choice = user_input.get("login_method")

        if choice == STEP_QR_LOGIN:
            return await self.async_step_qr_login()
        elif choice == "manual_login":
            # 手动输入授权码
            return await self.async_step_manual_login()
        elif choice == "skip_login":
            # 跳过登录
            _LOGGER.info("User skipped login, proceeding with public API only")
            self._auth_token = None
            return await self.async_step_account()
        else:
            # 不应该到这里
            return self.async_show_menu(step_id=STEP_USER)

    async def async_step_qr_login(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """二维码登录步骤"""
        client = GasHttpClient(cid=self._cid)

        if user_input is None:
            # 初次显示，生成二维码
            try:
                login_id, image_url = await self.hass.async_add_executor_job(
                    client.create_login_qr_code
                )

                self._qr_login_id = login_id
                self._qr_image_url = image_url

                return self.async_show_form(
                    step_id=STEP_QR_LOGIN,
                    data_schema=vol.Schema({
                        vol.Required("refresh_qr", default=False): bool
                    }),
                    description_placeholders={
                        "description": (
                            f"<p>请使用微信扫描下方二维码登录昆仑燃气小程序。</p>"
                            f'<p><img src="{image_url}" style="width:250px;height:250px;margin:20px auto;"/></p>'
                            f"<p>扫描后点击<strong>刷新状态</strong>，或等待10秒后自动检查。</p>"
                        )
                    },
                )
            except CSGAPIError as err:
                _LOGGER.error(f"Failed to create QR code: {err}")
                return self.async_show_form(
                    step_id=STEP_QR_LOGIN,
                    errors={"base": str(err)},
                )

        # 用户点击下一步，检查扫码状态
        if user_input.get("refresh_qr"):
            return await self.async_step_qr_login()

        # 检查登录状态
        login_id = self._qr_login_id
        success, auth_token = await self.hass.async_add_executor_job(
            client.check_qr_login_status, login_id
        )

        if success:
            # 登录成功
            self._auth_token = auth_token
            _LOGGER.info("QR login successful, proceeding to account setup")
            return await self.async_step_account()
        else:
            # 未扫码，返回重新显示二维码
            return self.async_show_form(
                step_id=STEP_QR_LOGIN,
                errors={"base": "qr_not_scanned"},
                description_placeholders={
                    "description": (
                        f"<p>二维码未扫描，请重试。</p>"
                        f'<p><img src="{self._qr_image_url}" style="width:250px;height:250px;margin:20px auto;"/></p>'
                        f"<p>扫描后点击<strong>刷新状态</strong>。</p>"
                    )
                },
            )

    async def async_step_manual_login(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """手动输入微信授权码"""
        errors = {}

        if user_input is None:
            return self.async_show_form(
                step_id="manual_login",
                data_schema=vol.Schema({
                    vol.Required("wechat_code", default=""): str,
                }),
                description_placeholders={
                    "description": "<p>请输入从昆仑燃气小程序获取的微信授权码（8位）</p>"
                },
            )

        wechat_code = user_input.get("wechat_code", "").strip()

        if not wechat_code:
            errors["base"] = "wechat_code_required"
        elif len(wechat_code) < 8:
            errors["base"] = "wechat_code_invalid"
        else:
            self._wechat_code = wechat_code
            # union_id 使用默认值
            self._union_id = "oYyWJ5oc-9czhTnS2-iWAvow0TB8"
            _LOGGER.info(f"WeChat code received: {wechat_code[:10]}***")
            return await self.async_step_account()

        return self.async_show_form(
            step_id="manual_login",
            data_schema=vol.Schema({
                vol.Required("wechat_code", default=""): str,
            }),
            errors=errors,
        )

    async def async_step_account(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """第二步：配置燃气账户"""
        errors = {}

        if user_input is not None:
            return self.async_show_form(
                step_id=STEP_ACCOUNT,
                data_schema=vol.Schema({
                    vol.Required(CONF_USER_CODE): str,
                    vol.Optional(CONF_CID, default=2): vol.Coerce(int),
                    vol.Optional(CONF_TERMINAL_TYPE, default=7): vol.Coerce(int),
                }),
            )

        user_code = user_input.get(CONF_USER_CODE, "").strip()
        cid = user_input.get(CONF_CID, 2)

        if not user_code:
            errors[CONF_USER_CODE] = "user_code_required"
        elif not user_code.isdigit() or len(user_code) != 8:
            errors[CONF_USER_CODE] = "user_code_invalid"
        else:
            self._user_code = user_code
            self._cid = cid
            self._terminal_type = user_input.get(CONF_TERMINAL_TYPE, 7)
            return await self.async_step_confirm()

        return self.async_show_form(
            step_id=STEP_ACCOUNT,
            data_schema=vol.Schema({
                vol.Required(CONF_USER_CODE): str,
                vol.Optional(CONF_CID, default=2): vol.Coerce(int),
                vol.Optional(CONF_TERMINAL_TYPE, default=7): vol.Coerce(int),
            }),
            errors=errors,
        )

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """第三步：确认配置"""
        if user_input is None:
            features = self._get_features_description()
            return self.async_show_form(
                step_id=STEP_CONFIRM,
                description_placeholders={
                    "description": f"请确认以下配置信息：\n\n户号：{self._user_code}\n地区代码：{self._cid}\n微信登录：{'是' if self._auth_token or self._wechat_code else '否'}\n\n{features}"
                },
                data_schema=vol.Schema({
                    vol.Required("confirm", default=False): bool,
                }),
            )

        if user_input.get("confirm"):
            return await self.async_create_entry()

    def _get_features_description(self) -> str:
        """获取功能说明"""
        if self._auth_token or self._wechat_code:
            return """已登录功能：
✓ 余额查询
✓ 客户信息
✓ 表计读数
✓ 用气统计
✓ 缴费记录
✓ 阶梯价格"""
        else:
            return """基础功能（未登录）：
✓ 余额查询
✓ 客户信息

注意：登录后可获得完整功能，包括用气统计、缴费记录、阶梯价格。"""

    async def async_create_entry(self) -> FlowResult:
        """创建配置条目"""
        # 准备数据
        data = {
            CONF_USER_CODE: self._user_code,
            CONF_CID: self._cid,
            CONF_TERMINAL_TYPE: self._terminal_type,
        }

        # 如果有授权信息
        if self._auth_token:
            data["wechat_code"] = self._wechat_code or ""
            data["union_id"] = self._union_id or ""

        # 账户列表（初始为空，后续通过options添加）
        data[CONF_ACCOUNTS] = {
            self._user_code: {
                CONF_USER_CODE: self._user_code,
                CONF_CID: self._cid,
                CONF_TERMINAL_TYPE: self._terminal_type,
            }
        }

        _LOGGER.info(f"Creating entry for user: {self._user_code}")

        return self.async_create_entry(
            title=f"昆仑燃气 {self._user_code}",
            data=data,
        )
