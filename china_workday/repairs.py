"""中国工作日集成修复平台。"""

from __future__ import annotations

from typing import Any, cast

import voluptuous as vol

from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .config_flow import validate_custom_dates
from .const import CONF_REMOVE_HOLIDAYS


class HolidayFixFlow(RepairsFlow):
    """处理节假日配置问题的修复流程。"""

    def __init__(
        self, entry: ConfigEntry, named_holiday: str
    ) -> None:
        """创建修复流程。"""
        self.entry = entry
        self.named_holiday: str = named_holiday
        super().__init__()

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """处理第一步。"""
        return await self.async_step_fix_remove_holiday()

    async def async_step_fix_remove_holiday(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """处理修复移除节假日选项。"""
        errors: dict[str, str] = {}
        if user_input:
            options = dict(self.entry.options)
            new_options = {**options, **user_input}
            try:
                await self.hass.async_add_executor_job(
                    validate_custom_dates, new_options
                )
            except Exception:  # noqa: BLE001
                errors["remove_holidays"] = "remove_holiday_error"
            else:
                self.hass.config_entries.async_update_entry(
                    self.entry, options=new_options
                )
                await self.hass.config_entries.async_reload(self.entry.entry_id)
                return self.async_create_entry(data={})

        remove_holidays = self.entry.options.get(CONF_REMOVE_HOLIDAYS, [])
        removed_named_holiday = [
            value for value in remove_holidays if value != self.named_holiday
        ]
        new_schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Optional(CONF_REMOVE_HOLIDAYS, default=[]): SelectSelector(
                        SelectSelectorConfig(
                            options=[],
                            multiple=True,
                            custom_value=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            {CONF_REMOVE_HOLIDAYS: removed_named_holiday},
        )
        return self.async_show_form(
            step_id="fix_remove_holiday",
            data_schema=new_schema,
            description_placeholders={
                CONF_REMOVE_HOLIDAYS: self.named_holiday,
                "title": self.entry.title,
            },
            errors=errors,
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, Any] | None,
) -> RepairsFlow:
    """创建修复流程。"""
    entry = None
    if data and (entry_id := data.get("entry_id")):
        entry_id = cast(str, entry_id)
        entry = hass.config_entries.async_get_entry(entry_id)

    if data and (holiday := data.get("named_holiday")) and entry:
        # 配置中的命名节假日错误
        return HolidayFixFlow(entry, holiday)

    # 其他情况使用默认确认修复流程
    return ConfirmRepairFlow()
