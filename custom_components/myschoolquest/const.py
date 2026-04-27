"""Constants for MySchoolQuest integration."""

from datetime import timedelta

DOMAIN = "myschoolquest"
PLATFORMS = ["sensor"]

DEFAULT_NAME = "MySchoolQuest Menu"

# Configuration constants
CONF_LOCATION_ID = "location_id"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = timedelta(hours=6)  # Update every 6 hours

# API endpoints
API_BASE_URL = "https://api.myschoolquest.com/v1/menus/week"

# Icon
ICON = "mdi:food-apple"
