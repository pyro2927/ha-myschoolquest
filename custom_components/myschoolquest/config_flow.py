"""Config flow for MySchoolQuest integration."""

import logging
from collections.abc import Mapping
from typing import Any

import requests
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_RESOURCE, CONF_SCAN_INTERVAL
from homeassistant.core import callback

from .const import (
    API_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MySchoolQuestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MySchoolQuest."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        from datetime import date
        
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate connection by making a test API call
                resource = user_input.get(CONF_RESOURCE, API_BASE_URL)
                location_id = user_input.get("location_id", "")
                
                # Get today's date with timezone offset
                from datetime import datetime
                today = datetime.now().astimezone()
                today_str = today.strftime("%Y-%m-%dT00:00:00.000%z")
                if len(today_str) > 6 and today_str[-5] in ('+', '-') and ':' not in today_str[-6:]:
                    today_str = today_str[:-2] + ':' + today_str[-2:]
                
                if location_id:
                    api_url = f"{API_BASE_URL}?location_id={location_id}&date={today_str}"
                else:
                    # If no location_id, use the full resource URL
                    api_url = resource

                response = await self.hass.async_add_executor_job(
                    lambda: requests.get(api_url, timeout=10)
                )
                response.raise_for_status()

                # Validate the response has expected data
                data = response.json()
                if not isinstance(data, dict):
                    errors["base"] = "invalid_response"
                elif "status" not in data or data.get("status") != "success":
                    errors["base"] = "no_data_found"

            except requests.RequestException as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = "cannot_connect"
            except ValueError as err:
                _LOGGER.error("Invalid JSON response: %s", err)
                errors["base"] = "invalid_json"
            except Exception as err:
                _LOGGER.error("Unexpected error: %s", err)
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title="MySchoolQuest Menu",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RESOURCE, default=API_BASE_URL): str,
                    vol.Optional("location_id", default=""): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL.total_seconds()
                    ): vol.All(vol.Coerce(int), vol.Clamp(min=300, max=86400)),
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> config_entries.FlowResult:
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_data)
