"""Sensor platform for MySchoolQuest integration."""

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, ICON
from .coordinator import MySchoolQuestDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_day_data(menu_data: dict, target_date: str) -> dict | None:
    """Look up menu data for a specific date."""
    return menu_data.get(target_date) if menu_data else None


def _extract_items_for_plan(day_data: dict, plan_keyword: str) -> dict:
    """Extract menu items organized by category for a given plan keyword.

    Matches plan names case-insensitively (e.g. "Hot Breakfast", "Lunch").
    Returns a dict like:
        {
            "Main Entree": ["item1", "item2"],
            "Fruit": ["apples"],
            ...
        }
    """
    result: dict[str, list[str]] = {}
    if not day_data:
        return result

    periods = day_data.get("periods", {})
    for plan_name, plan_data in periods.items():
        if plan_keyword.lower() not in plan_name.lower():
            continue
        for cat_name, cat_data in plan_data.get("categories", {}).items():
            result[cat_name] = cat_data.get("item_names", [])
    return result


def _all_categories(day_data: dict) -> dict:
    """Get all categories from all meal periods (fallback when no keyword match)."""
    result: dict[str, list[str]] = {}
    for plan_data in day_data.get("periods", {}).values():
        for cat_name, cat_data in plan_data.get("categories", {}).items():
            result[cat_name] = cat_data.get("item_names", [])
    return result


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the MySchoolQuest sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        MySchoolQuestMenuWeekSensor(coordinator),
        MySchoolQuestDayMealSensor(
            coordinator,
            name="Today's Breakfast Menu",
            unique_id="myschoolquest_today_breakfast",
            day_offset=0,
            meal_keyword="breakfast",
        ),
        MySchoolQuestDayMealSensor(
            coordinator,
            name="Today's Lunch Menu",
            unique_id="myschoolquest_today_lunch",
            day_offset=0,
            meal_keyword="lunch",
        ),
        MySchoolQuestDayMealSensor(
            coordinator,
            name="Tomorrow's Breakfast Menu",
            unique_id="myschoolquest_tomorrow_breakfast",
            day_offset=1,
            meal_keyword="breakfast",
        ),
        MySchoolQuestDayMealSensor(
            coordinator,
            name="Tomorrow's Lunch Menu",
            unique_id="myschoolquest_tomorrow_lunch",
            day_offset=1,
            meal_keyword="lunch",
        ),
    ]

    async_add_entities(entities)


class MySchoolQuestMenuWeekSensor(SensorEntity):
    """Representation of the main school menu week sensor."""

    def __init__(self, coordinator: MySchoolQuestDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._attr_name = "School Menu Week"
        self._attr_unique_id = "myschoolquest_menu_week"
        self._attr_icon = ICON
        self._attr_native_value = 0

    @property
    def native_value(self) -> StateType:
        """Return the number of days with menu data."""
        menu_data = self.coordinator.data.get("menu_data", {})
        return len(menu_data)

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return a summary of the weekly menu data (not the full raw data)."""
        menu_data = self.coordinator.data.get("menu_data", {})
        if not menu_data:
            return {}

        # Build a lightweight summary per day (no raw item details, just names)
        daily_summary = {}
        for date_str, day_data in menu_data.items():
            day_summary: dict[str, list[str]] = {}
            for plan_name, plan_data in day_data.get("periods", {}).items():
                for cat_name, cat_data in plan_data.get("categories", {}).items():
                    day_summary[cat_name] = cat_data.get("item_names", [])
            daily_summary[date_str] = day_summary

        return {
            "data": daily_summary,
            "dates": sorted(menu_data.keys()),
            "day_count": len(menu_data),
        }

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()


class MySchoolQuestDayMealSensor(SensorEntity):
    """Sensor for a specific day's meal period (breakfast or lunch).

    Attributes exposed for easy template iteration:
        items:          ["Peach Yogurt Parfait", "Cheerios", ...]
        categories:     {"Main Entree": ["item1", "item2"], "Fruit": ["apples"], ...}
        category_names: ["Main Entree", "Fruit", ...]
        item_count:     12
        available:      true
        date:           "2026-04-27"
    """

    def __init__(
        self,
        coordinator: MySchoolQuestDataUpdateCoordinator,
        *,
        name: str,
        unique_id: str,
        day_offset: int,
        meal_keyword: str,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._day_offset = day_offset
        self._meal_keyword = meal_keyword
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:silverware-fork-knife"
        self._attr_native_value = ""

    @property
    def _target_date(self) -> str:
        """Compute target date dynamically so it rolls over each day."""
        return (date.today() + timedelta(days=self._day_offset)).isoformat()

    def _get_categories(self, day_data: dict) -> dict:
        """Get categories for this meal period, falling back to all periods."""
        categories = _extract_items_for_plan(day_data, self._meal_keyword)
        if not categories:
            categories = _all_categories(day_data)
        return categories

    @property
    def native_value(self) -> StateType:
        """Return a summary count of items."""
        menu_data = self.coordinator.data.get("menu_data", {})
        day_data = _get_day_data(menu_data, self._target_date)
        if not day_data:
            return "No data"

        categories = self._get_categories(day_data)
        total_items = sum(len(items) for items in categories.values())
        return f"{total_items} items" if total_items else "No data"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return meal items organized by category as lists."""
        menu_data = self.coordinator.data.get("menu_data", {})
        day_data = _get_day_data(menu_data, self._target_date)

        if not day_data:
            return {
                "available": False,
                "date": self._target_date,
                "categories": {},
                "category_names": [],
                "items": [],
                "item_count": 0,
            }

        categories = self._get_categories(day_data)
        all_items = []
        for cat_items in categories.values():
            all_items.extend(cat_items)

        return {
            "available": len(categories) > 0,
            "date": self._target_date,
            "categories": categories,
            "category_names": list(categories.keys()),
            "items": all_items,
            "item_count": len(all_items),
        }

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()
