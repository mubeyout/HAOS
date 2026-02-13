# -*- coding: utf-8 -*-
"""Config flow for PetroChina Gas integration."""

import copy
import logging
import time
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import ConfigEntryAuthFailed
from requests import RequestException

from .const import (
    ABORT_ALL_ADDED,
    ABORT_NO_ACCOUNT,
    CONF_ACCOUNTS,
    CONF_ACTION,
    CONF_CID,
    CONF_GENERAL_ERROR,
    CONF_SETTINGS,
    CONF_TERMINAL_TYPE,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATED_AT,
    CONF_USER_CODE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
    ERROR_QR_NOT_SCANNED,
    STEP_ADD_ACCOUNT,
    STEP_INIT,
    STEP_QR_LOGIN,
    STEP_SETTINGS,
    STEP_USER,
    STEP_VALIDATE_SMS_CODE,
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
        """
        Handle the initial step.
        Let user choose the login method.
        """
        self.context["user_data"] = {}
        return self.async_show_menu(
            step_id=STEP_USER,
            menu_options=[
                STEP_QR_LOGIN,
            ],
        )

    async def async_step_qr_login(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Handle QR code login step."""
        client = GasHttpClient(cid=2)

        if user_input is None:
            # create QR code
            try:
                login_id, image_link = await self.hass.async_add_executor_job(
                    client.create_login_qr_code
                )
                self.context["user_data"]["login_id"] = login_id
                self.context["user_data"]["image_link"] = image_link
                return self.async_show_form(
                    step_id=STEP_QR_LOGIN,
                    data_schema=vol.Schema(
                        {vol.Required("refresh_qr_code", default=False): bool}
                    ),
                    description_placeholders={
                        "description": f"<p>使用微信小程序扫码登录昆仑燃气。</p>"
                        f'<p><img src="{image_link}" alt="QR code" style="width: 200px;"/></p>',
                    },
                )
            except CSGAPIError as err:
                _LOGGER.error(f"Failed to create QR code: {err}")
                error_detail = str(err)
                errors = {}
                errors[CONF_GENERAL_ERROR] = error_detail
                return self.async_show_form(
                    step_id=STEP_QR_LOGIN,
                    errors=errors,
                )
            except Exception as err:
                _LOGGER.exception("Unexpected exception when creating QR code")
                error_detail = f"{type(err).__name__}: {err}"
                errors = {}
                errors[CONF_GENERAL_ERROR] = error_detail
                return self.async_show_form(
                    step_id=STEP_QR_LOGIN,
                    errors=errors,
                )

        # user submitted the form
        if user_input.get("refresh_qr_code"):
            return await self.async_step_qr_login()

        return await self.async_step_validate_qr_login()

    async def async_step_validate_qr_login(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Get QR scan status after user has scanned the code"""
        client = GasHttpClient(cid=2)
        login_id = self.context["user_data"]["login_id"]
        image_link = self.context["user_data"]["image_link"]

        try:
            success, auth_token = await self.hass.async_add_executor_job(
                client.check_qr_login_status, login_id
            )
            if success:
                # QR login successful, get user info
                self.context["user_data"]["auth_token"] = auth_token
                return await self.async_step_add_account()
        except Exception as err:
            _LOGGER.exception("Unexpected exception during QR login validation")
            error_detail = f"{type(err).__name__}: {err}"
            errors = {}
            errors[CONF_GENERAL_ERROR] = error_detail
            return self.async_show_form(
                step_id=STEP_QR_LOGIN,
                data_schema=vol.Schema(
                    {vol.Required("refresh_qr_code", default=False): bool}
                ),
                errors=errors,
                description_placeholders={
                    "description": f"<p>使用微信小程序扫码登录昆仑燃气。</p>"
                                    f'<p><img src="{image_link}" alt="QR code" style="width: 200px;"/></p>',
                },
            )

    async def async_step_add_account(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Add a gas account"""
        if user_input is None:
            return self.async_show_form(
                step_id=STEP_ADD_ACCOUNT,
                data_schema=vol.Schema({
                    vol.Required(CONF_USER_CODE): vol.All(
                        str, vol.Length(min=8, max=8), msg="请输入8位燃气户号"
                    ),
                    vol.Optional(CONF_CID, default=2): int,
                    vol.Optional(CONF_TERMINAL_TYPE, default=7): int,
                }),
            )

        user_code = user_input.get(CONF_USER_CODE)
        cid = user_input.get(CONF_CID, 2)
        terminal_type = user_input.get(CONF_TERMINAL_TYPE, 7)

        # Set unique ID
        await self.async_set_unique_id(f"GAS-{user_code}")
        self._abort_if_unique_id_configured()

        return await self._create_or_update_config_entry(
            user_code, cid, terminal_type
        )

    async def _create_or_update_config_entry(
        self, user_code, cid, terminal_type
    ) -> FlowResult:
        """Create or update config entry"""
        data = {
            CONF_USER_CODE: user_code,
            CONF_CID: cid,
            CONF_TERMINAL_TYPE: terminal_type,
            CONF_ACCOUNTS: {
                user_code: {
                    CONF_USER_CODE: user_code,
                    CONF_CID: cid,
                    CONF_TERMINAL_TYPE: terminal_type,
                }
            },
            CONF_SETTINGS: {
                CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            },
            CONF_UPDATED_AT: str(int(time.time() * 1000)),
        }

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
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
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
        """Manage the options."""

        schema = vol.Schema(
            {
                vol.Required(CONF_ACTION, default=STEP_ADD_ACCOUNT): vol.In(
                    {
                        STEP_ADD_ACCOUNT: "添加已绑定的燃气户号",
                        STEP_SETTINGS: "参数设置",
                    }
                ),
            }
        )
        if user_input:
            if user_input[CONF_ACTION] == STEP_ADD_ACCOUNT:
                return await self.async_step_add_account()
            if user_input[CONF_ACTION] == STEP_SETTINGS:
                return await self.async_step_settings()
        return self.async_show_form(step_id=STEP_INIT, data_schema=schema)

    async def async_step_add_account(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Select or add a gas account"""
        # Get all account numbers from current entry
        all_account_numbers = list(self.config_entry.data[CONF_ACCOUNTS].keys())

        if user_input:
            user_code = user_input.get(CONF_USER_CODE)
            cid = user_input.get(CONF_CID, 2)
            terminal_type = user_input.get(CONF_TERMINAL_TYPE, 7)

            if user_code in all_account_numbers:
                return self.async_abort(reason=ABORT_ALL_ADDED)

            # store the account config in main entry
            new_data = self.config_entry.data.copy()
            new_data[CONF_ACCOUNTS][user_code] = {
                CONF_USER_CODE: user_code,
                CONF_CID: cid,
                CONF_TERMINAL_TYPE: terminal_type,
            }
            new_data[CONF_UPDATED_AT] = str(int(time.time() * 1000))
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            _LOGGER.info(
                "Added gas account to %s: %s",
                self.config_entry.data.get(CONF_USER_CODE),
                user_code,
            )
            _LOGGER.info("Reloading entry because of new added account")
            await self.hass.config_entries.async_reload(
                self.config_entry.entry_id
            )
            return self.async_create_entry(
                title="",
                data={},
            )

        return self.async_show_form(
            step_id=STEP_ADD_ACCOUNT,
            data_schema=vol.Schema({
                vol.Required(CONF_USER_CODE): vol.All(
                    str, vol.Length(min=8, max=8), msg="请输入8位燃气户号"
                ),
                vol.Optional(CONF_CID, default=2): int,
                vol.Optional(CONF_TERMINAL_TYPE, default=7): int,
            }),
        )

    async def async_step_settings(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Settings of parameters"""
        update_interval = self.config_entry.data[CONF_SETTINGS][CONF_UPDATE_INTERVAL]
        schema = vol.Schema(
            {
                vol.Required(CONF_UPDATE_INTERVAL, default=update_interval): vol.All(
                    int, vol.Range(min=60), msg="刷新间隔不能低于60秒"
                ),
            }
        )
        if user_input is None:
            return self.async_show_form(step_id=STEP_SETTINGS, data_schema=schema)

        new_data = self.config_entry.data.copy()
        new_data[CONF_SETTINGS][CONF_UPDATE_INTERVAL] = user_input[CONF_UPDATE_INTERVAL]
        new_data[CONF_UPDATED_AT] = str(int(time.time() * 1000))
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
        )
        return self.async_create_entry(
            title="",
            data={},
        )
