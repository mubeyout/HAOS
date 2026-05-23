# -*- coding: utf-8 -*-
"""Config flow for PetroChina Gas integration."""

import copy
import logging
import time
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from requests import RequestException

from .const import (
    CONF_ACCOUNTS,
    CONF_CID,
    CONF_GENERAL_ERROR,
    CONF_SETTINGS,
    CONF_TERMINAL_TYPE,
    CONF_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_MDM_CODE,
    CONF_OPEN_ID,
    CONF_UNION_ID,
    CONF_MOBILE,
    CONF_PASSWORD,
    CONF_COMPANY_ID,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATED_AT,
    CONF_USER_CODE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
    STEP_ADD_ACCOUNT_DIRECT,
    STEP_INIT,
    STEP_SETTINGS,
    STEP_USER,
)
from .gas_client import (
    GasHttpClient,
    CSGAPIError,
)

_LOGGER = logging.getLogger(__name__)


class PetrochinaGasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PetroChina Gas Statistics."""

    VERSION = 1
    _reauth_entry: Optional[config_entries.ConfigEntry] = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PetrochinaGasOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step - show account form directly."""
        # terminal_type 使用默认值
        DEFAULT_TERMINAL_TYPE = 7

        if user_input is None:
            return self.async_show_form(
                step_id=STEP_USER,
                data_schema=vol.Schema({
                    vol.Required(CONF_USER_CODE): vol.All(
                        str, vol.Length(min=8, max=8), msg="请输入8位燃气户号"
                    ),
                    vol.Required(CONF_CID, default=2): int,
                    vol.Required(CONF_MOBILE): str,
                    vol.Required(CONF_PASSWORD): str,
                }),
                description_placeholders={
                    "description": "<p>请输入您的燃气户号和登录凭证。</p>"
                    "<p>系统将使用手机号和密码自动登录，无需手动获取Token。</p>"
                    "<p>地区代码：昆明=2，其他地区请咨询燃气公司。</p>"
                },
            )

        user_code = user_input.get(CONF_USER_CODE)
        cid = user_input.get(CONF_CID, 2)
        terminal_type = DEFAULT_TERMINAL_TYPE

        # 收集认证信息（不再收集 company_id，自动检测）
        auth_settings = {
            CONF_MOBILE: user_input.get(CONF_MOBILE, ""),
            CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
        }

        # 设置唯一ID
        await self.async_set_unique_id(f"GAS-{user_code}")

        return await self._create_or_update_config_entry(
            user_code, cid, terminal_type, auth_settings
        )

    async def _create_or_update_config_entry(
        self, user_code, cid, terminal_type, settings: Optional[dict] = None
    ) -> FlowResult:
        """Create or update config entry"""
        # 获取现有配置（如果有）
        if self._reauth_entry:
            old_config = copy.deepcopy(self._reauth_entry.data)
            existing_accounts = old_config.get(CONF_ACCOUNTS, {})
            existing_settings = old_config.get(CONF_SETTINGS, {})
        else:
            existing_accounts = {}
            existing_settings = {}

        # 构建账户配置，包含认证信息
        account_config = {
            CONF_USER_CODE: user_code,
            CONF_CID: cid,
            CONF_TERMINAL_TYPE: terminal_type,
        }

        # 如果提供了认证信息，添加到账户级别
        if settings:
            for key in [CONF_MOBILE, CONF_PASSWORD]:
                if settings.get(key):
                    account_config[key] = settings[key]

        data = {
            CONF_USER_CODE: user_code,
            CONF_CID: cid,
            CONF_TERMINAL_TYPE: terminal_type,
            CONF_ACCOUNTS: {
                **existing_accounts,
                user_code: account_config,
            },
            CONF_SETTINGS: {
                CONF_UPDATE_INTERVAL: existing_settings.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            },
            CONF_UPDATED_AT: str(int(time.time() * 1000)),
        }

        # Add auth settings if provided (to global settings for backward compatibility)
        if settings:
            data[CONF_SETTINGS].update(settings)

        # handle normal creation and reauth
        if self._reauth_entry:
            # reauth
            old_config = copy.deepcopy(self._reauth_entry.data)
            data[CONF_ACCOUNTS] = old_config.get(CONF_ACCOUNTS, {})
            data[CONF_SETTINGS] = old_config.get(CONF_SETTINGS, {})
            self.hass.config_entries.async_update_entry(self._reauth_entry, data=data)
            await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
            self._reauth_entry = None
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title=f"PetroChina Gas {user_code}",
            data=data,
        )

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_user()


class PetrochinaGasOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for PetroChina Gas Statistics."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Manage options - show menu."""
        if user_input is not None:
            if user_input["action"] == "settings":
                return await self.async_step_settings()
            elif user_input["action"] == "auth":
                return await self.async_step_auth()

        return self.async_show_menu(
            step_id=STEP_INIT,
            menu_options={
                "settings": "更新间隔设置",
                "auth": "认证信息设置",
            },
        )

    async def async_step_settings(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Manage update interval settings."""
        settings = self.config_entry.data.get(CONF_SETTINGS, {})
        current_interval = settings.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

        schema = vol.Schema({
            vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                int, vol.Range(min=60), msg="刷新间隔不能低于60秒"
            ),
        })

        if user_input:
            new_data = self.config_entry.data.copy()
            new_data[CONF_SETTINGS] = new_data.get(CONF_SETTINGS, {})
            new_data[CONF_SETTINGS][CONF_UPDATE_INTERVAL] = user_input[CONF_UPDATE_INTERVAL]
            new_data[CONF_UPDATED_AT] = str(int(time.time() * 1000))
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id=STEP_SETTINGS, data_schema=schema)

    async def async_step_auth(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Manage authentication credentials."""
        settings = self.config_entry.data.get(CONF_SETTINGS, {})

        # 获取当前账户信息
        accounts = self.config_entry.data.get(CONF_ACCOUNTS, {})
        if not accounts:
            return self.async_abort(reason="no_account")

        # 获取第一个账户的认证信息作为默认值
        first_account = list(accounts.values())[0]
        defaults = {
            CONF_MOBILE: settings.get(CONF_MOBILE) or first_account.get(CONF_MOBILE, ""),
            CONF_PASSWORD: settings.get(CONF_PASSWORD) or first_account.get(CONF_PASSWORD, ""),
        }

        if user_input is None:
            schema = vol.Schema({
                vol.Optional(CONF_MOBILE, default=defaults[CONF_MOBILE]): str,
                vol.Optional(CONF_PASSWORD, default=defaults[CONF_PASSWORD]): str,
            })
            return self.async_show_form(
                step_id="auth",
                data_schema=schema,
                description_placeholders={
                    "description": "<p>更新登录凭证。</p>"
                    "<p>系统将使用手机号和密码自动登录，Token过期时会自动重新获取。</p>"
                    "<p>留空保持不变。</p>"
                }
            )

        # 保存认证信息
        new_data = copy.deepcopy(self.config_entry.data)
        new_settings = new_data.get(CONF_SETTINGS, {})

        # 更新全局设置
        for key in [CONF_MOBILE, CONF_PASSWORD]:
            if user_input.get(key):  # 只更新非空值
                new_settings[key] = user_input[key]

        new_data[CONF_SETTINGS] = new_settings
        new_data[CONF_UPDATED_AT] = str(int(time.time() * 1000))

        # 同时更新所有账户的认证信息
        for account_key, account_config in new_data.get(CONF_ACCOUNTS, {}).items():
            for key in [CONF_MOBILE, CONF_PASSWORD]:
                if user_input.get(key):
                    account_config[key] = user_input[key]

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
        )

        return self.async_create_entry(title="", data=user_input)
