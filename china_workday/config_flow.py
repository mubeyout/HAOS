"""Adds config flow for Workday integration."""

from __future__ import annotations

from functools import partial
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from homeassistant.util import dt as dt_util

from .const import (
    ALLOWED_DAYS,
    CONF_ADD_HOLIDAYS,
    CONF_EXCLUDES,
    CONF_REMOVE_HOLIDAYS,
    CONF_WORKDAYS,
    DEFAULT_EXCLUDES,
    DEFAULT_NAME,
    DEFAULT_WORKDAYS,
    DOMAIN,
    LOGGER,
    CONF_ENABLE_WEEK_TYPE,
    CONF_IMPORTANT_DATES,
    CONF_WEEK_TYPE_START_DATE,
)


def _is_valid_date_range(check_date: str, error: type[HomeAssistantError]) -> bool:
    """Validate date range."""
    if check_date.find(",") > 0:
        dates = check_date.split(",", maxsplit=1)
        for date in dates:
            if dt_util.parse_date(date) is None:
                raise error("Incorrect date in range")
        return True
    return False


def validate_custom_dates(user_input: dict[str, Any]) -> None:
    """Validate custom dates for add/remove holidays."""
    for add_date in user_input[CONF_ADD_HOLIDAYS]:
        if (
            not _is_valid_date_range(add_date, AddDateRangeError)
            and dt_util.parse_date(add_date) is None
        ):
            raise AddDatesError("Incorrect date")

    for remove_date in user_input[CONF_REMOVE_HOLIDAYS]:
        if (
            not _is_valid_date_range(remove_date, RemoveDateRangeError)
            and dt_util.parse_date(remove_date) is None
        ):
            raise RemoveDatesError("Incorrect date")


DATA_SCHEMA_OPT = vol.Schema(
    {
        vol.Optional(CONF_WORKDAYS, default=DEFAULT_WORKDAYS): SelectSelector(
            SelectSelectorConfig(
                options=ALLOWED_DAYS,
                multiple=True,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key="days",
            )
        ),
        vol.Optional(CONF_EXCLUDES, default=DEFAULT_EXCLUDES): SelectSelector(
            SelectSelectorConfig(
                options=ALLOWED_DAYS,
                multiple=True,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key="days",
            )
        ),
        vol.Optional(CONF_ADD_HOLIDAYS, default=[]): SelectSelector(
            SelectSelectorConfig(
                options=[],
                multiple=True,
                custom_value=True,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(CONF_REMOVE_HOLIDAYS, default=[]): SelectSelector(
            SelectSelectorConfig(
                options=[],
                multiple=True,
                custom_value=True,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(CONF_ENABLE_WEEK_TYPE, default=False): bool,
        vol.Optional(CONF_WEEK_TYPE_START_DATE, default=""): TextSelector(),
        vol.Optional(CONF_IMPORTANT_DATES, default=""): TextSelector(),
    }
)


class WorkdayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Workday integration."""

    VERSION = 1

    data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> WorkdayOptionsFlowHandler:
        """Get the options flow for this handler."""
        return WorkdayOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user initial step."""
        # 跳过名称输入步骤，直接使用默认名称进入选项配置
        self.data = {CONF_NAME: DEFAULT_NAME}
        return await self.async_step_options()

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle remaining flow."""
        errors: dict[str, str] = {}
        if user_input is not None:
            combined_input: dict[str, Any] = {**self.data, **user_input}

            try:
                await self.hass.async_add_executor_job(
                    validate_custom_dates, combined_input
                )
            except AddDatesError:
                errors["add_holidays"] = "add_holiday_error"
            except AddDateRangeError:
                errors["add_holidays"] = "add_holiday_range_error"
            except RemoveDatesError:
                errors["remove_holidays"] = "remove_holiday_error"
            except RemoveDateRangeError:
                errors["remove_holidays"] = "remove_holiday_range_error"

            abort_match = {
                CONF_EXCLUDES: combined_input[CONF_EXCLUDES],
                CONF_WORKDAYS: combined_input[CONF_WORKDAYS],
                CONF_ADD_HOLIDAYS: combined_input[CONF_ADD_HOLIDAYS],
                CONF_REMOVE_HOLIDAYS: combined_input[CONF_REMOVE_HOLIDAYS],
                CONF_ENABLE_WEEK_TYPE: combined_input.get(CONF_ENABLE_WEEK_TYPE, False),
                CONF_WEEK_TYPE_START_DATE: combined_input.get(CONF_WEEK_TYPE_START_DATE, ""),
                CONF_IMPORTANT_DATES: combined_input.get(CONF_IMPORTANT_DATES, ""),
            }
            LOGGER.debug("abort_check in options with %s", combined_input)
            self._async_abort_entries_match(abort_match)

            LOGGER.debug("Errors have occurred %s", errors)
            if not errors:
                LOGGER.debug("No duplicate, no errors, creating entry")
                return self.async_create_entry(
                    title=combined_input[CONF_NAME],
                    data={},
                    options=combined_input,
                )

        new_schema = self.add_suggested_values_to_schema(DATA_SCHEMA_OPT, user_input)
        return self.async_show_form(
            step_id="options",
            data_schema=new_schema,
            errors=errors,
            description_placeholders={
                "name": self.data[CONF_NAME],
            },
        )


class WorkdayOptionsFlowHandler(OptionsFlowWithReload):
    """Handle Workday options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Workday options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            combined_input: dict[str, Any] = {**self.config_entry.options, **user_input}

            try:
                await self.hass.async_add_executor_job(
                    validate_custom_dates, combined_input
                )
            except AddDatesError:
                errors["add_holidays"] = "add_holiday_error"
            except AddDateRangeError:
                errors["add_holidays"] = "add_holiday_range_error"
            except RemoveDatesError:
                errors["remove_holidays"] = "remove_holiday_error"
            except RemoveDateRangeError:
                errors["remove_holidays"] = "remove_holiday_range_error"
            else:
                LOGGER.debug("abort_check in options with %s", combined_input)
                abort_match = {
                    CONF_EXCLUDES: combined_input[CONF_EXCLUDES],
                    CONF_WORKDAYS: combined_input[CONF_WORKDAYS],
                    CONF_ADD_HOLIDAYS: combined_input[CONF_ADD_HOLIDAYS],
                    CONF_REMOVE_HOLIDAYS: combined_input[CONF_REMOVE_HOLIDAYS],
                    CONF_ENABLE_WEEK_TYPE: combined_input.get(CONF_ENABLE_WEEK_TYPE, False),
                    CONF_WEEK_TYPE_START_DATE: combined_input.get(CONF_WEEK_TYPE_START_DATE, ""),
                    CONF_IMPORTANT_DATES: combined_input.get(CONF_IMPORTANT_DATES, ""),
                }
                try:
                    self._async_abort_entries_match(abort_match)
                except AbortFlow as err:
                    errors = {"base": err.reason}
                else:
                    return self.async_create_entry(data=combined_input)

        options = self.config_entry.options
        new_schema = self.add_suggested_values_to_schema(DATA_SCHEMA_OPT, user_input or options)
        LOGGER.debug("Errors have occurred in options %s", errors)
        return self.async_show_form(
            step_id="init",
            data_schema=new_schema,
            errors=errors,
            description_placeholders={
                "name": options[CONF_NAME],
            },
        )


class AddDatesError(HomeAssistantError):
    """Exception for error adding dates."""


class AddDateRangeError(HomeAssistantError):
    """Exception for error adding dates."""


class RemoveDatesError(HomeAssistantError):
    """Exception for error removing dates."""


class RemoveDateRangeError(HomeAssistantError):
    """Exception for error removing dates."""


class CountryNotExist(HomeAssistantError):
    """Exception country does not exist error."""
