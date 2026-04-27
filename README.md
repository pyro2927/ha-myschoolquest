# MySchoolQuest Menu Integration for Home Assistant

A complete solution to bring your school's daily menu into Home Assistant. Perfect for parents who want to see what their kids are eating at school.

## Features

- 🍽️ **Automated Menu Updates** - Pulls weekly menu data from MySchoolQuest API every 6 hours (configurable)
- 🥣 **Breakfast & Lunch Parsing** - Automatically categorizes meals into breakfast and lunch with items
- 📅 **Today & Tomorrow Menus** - See what's available now and plan for tomorrow
- 🎨 **Beautiful Dashboard** - Includes a stunning dashboard card with gradient styling (Mushroom theme support)
- ⚡ **Docker Ready** - Test the integration in minutes with Docker

## Quick Start

### Option 1: Docker (Recommended for Testing)

```bash
# Clone this repository
git clone https://github.com/pyro2927/ha-myschoolquest.git
cd ha-myschoolquest

# Create a config directory and start Home Assistant
mkdir -p config
docker-compose up -d
```

Access Home Assistant at http://localhost:8123. After it starts, stop the container with `docker-compose down`, then edit `config/configuration.yaml` to add your school's location ID:

After running for the first time, stop with `docker-compose down`, then edit `config/configuration.yaml` to add your school's location ID:

```yaml
myschoolquest:
  resource: "https://api.myschoolquest.com/v1/menus/week"
  location_id: "YOUR_SCHOOL_LOCATION_ID"
  scan_interval: 21600
```

### Option 2: HACS Installation (Production)

1. Open HACS in Home Assistant
2. Go to **Integrations** → Click the three dots
3. Select **Custom repositories**
4. Add URL: `https://github.com/pyro2927/ha-myschoolquest`
5. Set Category to **Integration**, click **Add**
6. Search for "MySchoolQuest Menu" and click **Download**
7. Restart Home Assistant
8. Go to **Settings** → **Devices & Services** → **+ Add Integration**
9. Find "MySchoolQuest Menu" and click it
10. Enter your API resource URL (default should work)
11. Enter your school's location_id from MySchoolQuest
12. Click **Submit**

### Option 3: Manual Installation

1. Copy `custom_components/myschoolquest` to your Home Assistant's `config/custom_components/` folder
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **+ Add Integration**
4. Find "MySchoolQuest Menu" and click it
5. Enter your API resource URL (default should work)
6. Enter your school's location_id from MySchoolQuest
7. Click **Submit**

## Configuration

```yaml
myschoolquest:
  resource: "https://api.myschoolquest.com/v1/menus/week"
  location_id: "YOUR_SCHOOL_LOCATION_ID"  # Required
  scan_interval: 21600  # Optional, update every 6 hours (default)
```

### Finding Your Location ID

1. Log in to your MySchoolQuest account
2. Navigate to your school's menu page  
3. The location_id is typically in the URL or can be found in API responses

## Sensors Created

- `sensor.school_menu_week` - Main sensor with all menu data
- `sensor.today_s_school_menu` - Today's parsed menu (template sensor)
- `sensor.tomorrow_s_school_menu` - Tomorrow's parsed menu (template sensor)

### Example Sensor Attributes

```json
{
  "breakfast": {
    "Hot Item": ["Pancakes", "Eggs"],
    "Cold Item": ["Cereal", "Milk"]
  },
  "lunch": {
    "Main Course": ["Chicken Nuggets", "Fries"],
    "Side": ["Carrots", "Apple Slices"],
    "Dessert": ["Cookie"]
  }
}
```

## Dashboard Card

A beautiful dashboard card is included in `dashboard_card.yaml`. To use it:

1. Edit your Home Assistant dashboard
2. Add a new card → Manual card type  
3. Copy the YAML from `dashboard_card.yaml`
4. Save and enjoy!

### Recommended HACS Integrations (Optional)

- **[Mushroom Cards](https://github.com/piitaya/ha-mushroom)** - Modern card styling
- **[Card Mod](https://github.com/thomasloven/ha-card_mod)** - Custom CSS support

## Project Structure

```
ha-myschoolquest/
├── custom_components/myschoolquest/
│   ├── __init__.py          # Integration setup, config flow entry point
│   ├── config_flow.py       # UI configuration flow for adding device
│   ├── const.py             # Constants and configuration values
│   ├── coordinator.py       # Data polling logic (6-hour updates)
│   ├── sensor.py            # Sensor entities
│   └── manifest.json        # Integration metadata
├── config/                  # Your Home Assistant configuration (mounted from host)
├── Dockerfile               # Build integration into HA container
├── docker-compose.yml       # Docker Compose file (with live mount setup)
├── hacs.json                # HACS integration configuration
├── configuration.yaml.example  # Example config with comments
├── example_config.yaml      # Full example including templates
├── README.md                # This file
└── setup_instructions.md    # Detailed installation guide
```

## Development

### Testing Locally

```bash
# Run Home Assistant with Docker (config mounted for live edits)
docker-compose up -d

# View logs in real-time
docker-compose logs -f

# Stop the container
docker-compose down

# Make configuration changes while container is stopped, then restart
docker-compose up -d
```

The Docker setup uses bind mounts so you can edit files directly on your host:
- `config/` → `/config` in container (full config directory)
- `custom_components/myschoolquest/` → mounted read-only for the integration

```bash
pytest tests/
```

### Code Style

- Follows Python best practices (PEP 8)
- Uses type hints where possible
- Includes docstrings for new functions

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

If you encounter any issues:

1. Check the Home Assistant logs: `docker-compose logs homeassistant`
2. Verify your location_id is correct
3. [Open an issue on GitHub](https://github.com/pyro2927/ha-myschoolquest/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Home Assistant community for the amazing platform
- MySchoolQuest API for providing menu data

---

Made with ❤️ by a parent who wants to know what their kids are eating at school!
