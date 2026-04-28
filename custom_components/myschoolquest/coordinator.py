"""Data coordinator for MySchoolQuest integration."""

import logging
from datetime import datetime, timedelta

import requests
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class MySchoolQuestDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching MySchoolQuest data."""

    def __init__(self, hass: HomeAssistant, resource: str, location_id: str) -> None:
        """Initialize the coordinator."""
        self.resource = resource
        self.location_id = location_id.strip().rstrip(".").strip()
        super().__init__(
            hass,
            _LOGGER,
            name="MySchoolQuest Data",
            update_interval=timedelta(hours=6),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the API."""
        try:
            # Use today's date with local timezone offset
            today = datetime.now().astimezone()
            today_str = today.strftime("%Y-%m-%dT00:00:00.000%z")
            # Insert colon in timezone offset: -0500 -> -05:00
            if len(today_str) > 6 and today_str[-5] in ('+', '-') and ':' not in today_str[-6:]:
                today_str = today_str[:-2] + ':' + today_str[-2:]
            
            # Also get tomorrow's date for fetching future menu data
            tomorrow = today + timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%Y-%m-%dT00:00:00.000%z")
            if len(tomorrow_str) > 6 and tomorrow_str[-5] in ('+', '-') and ':' not in tomorrow_str[-6:]:
                tomorrow_str = tomorrow_str[:-2] + ':' + tomorrow_str[-2:]

            # Build the API URL with location_id - fetch both today and tomorrow
            # The API should return a week of data, but we ensure we get today and tomorrow
            if self.location_id:
                api_url = f"{API_BASE_URL}?location_id={self.location_id}&date={today_str}"
                api_url_tomorrow = f"{API_BASE_URL}?location_id={self.location_id}&date={tomorrow_str}"
            else:
                api_url = self.resource
                api_url_tomorrow = None

            _LOGGER.debug("Fetching menu data from: %s", api_url)

            response = await self.hass.async_add_executor_job(
                lambda: requests.get(api_url, timeout=30)
            )
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise UpdateFailed(f"API returned error: {data.get('msg', 'unknown error')}")

            # Fetch tomorrow's menu separately if needed (for early morning)
            tomorrow_data = None
            if api_url_tomorrow:
                try:
                    _LOGGER.debug("Fetching tomorrow's menu from: %s", api_url_tomorrow)
                    response_tomorrow = await self.hass.async_add_executor_job(
                        lambda: requests.get(api_url_tomorrow, timeout=30)
                    )
                    if response_tomorrow.status_code == 200:
                        tomorrow_data = response_tomorrow.json()
                except Exception as err:
                    _LOGGER.warning("Could not fetch tomorrow's menu: %s", err)

            # The API returns a 'menus' field which is a list of lists
            # Each inner list contains menu entries for that day
            menu_data = {}

            def process_menu_response(response_data):
                """Process a single API response and add to menu_data."""
                if not response_data or response_data.get("status") != "success":
                    return
                
                menus = response_data.get("menus", [])

                if isinstance(menus, list):
                    for menu_list in menus:
                        # Skip empty days
                        if not isinstance(menu_list, list) or not menu_list:
                            continue

                        # Process ALL entries in each day's menu list
                        # (API returns multiple entries per day: breakfast, lunch, etc.)
                        for menu_entry in menu_list:
                            if not isinstance(menu_entry, dict):
                                continue

                            date_str = menu_entry.get("date")
                            if not date_str:
                                continue

                            # Initialize day data if first entry for this date
                            if date_str not in menu_data:
                                menu_data[date_str] = {
                                    "date": date_str,
                                    "periods": {},
                                }

                            # Collect all meals for this day, organized by plan name
                            # Each "plan" (e.g. "Hot Breakfast", "Lunch") is a meal period
                            periods = menu_data[date_str]["periods"]

                            meals_list = menu_entry.get("meals", [])
                            if isinstance(meals_list, list):
                                for meal in meals_list:
                                    if not isinstance(meal, dict):
                                        continue

                                    plan = meal.get("plan", "Unknown")
                                    categories = meal.get("categories", [])

                                    # If this plan hasn't been seen yet, initialize it
                                    if plan not in periods:
                                        periods[plan] = {
                                            "categories": {},
                                        }

                                    # Merge categories under this plan
                                    for category in categories:
                                        if not isinstance(category, dict):
                                            continue

                                        cat_name = category.get("name", "Unknown")
                                        items_list = category.get("items", [])

                                        # Build the items list with full item details
                                        items = []
                                        for item in items_list:
                                            if isinstance(item, dict):
                                                item_data = {
                                                    "name": item.get("name", ""),
                                                    "description": item.get("description", ""),
                                                    "serving_size": item.get("serving_size", ""),
                                                    "allergens": item.get("allergens", []),
                                                    "nutrients": item.get("nutrients", []),
                                                }
                                                items.append(item_data)

                                        if cat_name not in periods[plan]["categories"]:
                                            periods[plan]["categories"][cat_name] = {
                                                "name": cat_name,
                                                "items": items,
                                                "item_names": [it["name"] for it in items],
                                            }
                                        else:
                                            # Merge items if category already exists
                                            existing_items = periods[plan]["categories"][cat_name]["items"]
                                            existing_names = {it["name"] for it in existing_items}
                                            for item_data in items:
                                                if item_data["name"] not in existing_names:
                                                    existing_items.append(item_data)
                                                    periods[plan]["categories"][cat_name]["item_names"].append(item_data["name"])

            # Process today's response
            process_menu_response(data)
            
            # Process tomorrow's response if available
            if tomorrow_data:
                process_menu_response(tomorrow_data)

            return {"menu_data": menu_data}
        except requests.RequestException as err:
            _LOGGER.error("Error fetching MySchoolQuest data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except (KeyError, TypeError) as err:
            _LOGGER.error("Invalid response from MySchoolQuest API: %s", err)
            raise UpdateFailed(f"Invalid API response: {err}") from err
        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error fetching MySchoolQuest data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
