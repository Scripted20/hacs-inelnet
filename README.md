# InelNET Blinds Control for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/Scripted20/hacs-inelnet.svg)](https://github.com/Scripted20/hacs-inelnet/releases)

Control your InelNET blinds, roller shutters, and awnings directly from Home Assistant.

## Features

- **Full cover control**: Open, close, stop, and set position
- **Position tracking**: Estimated position based on travel time (InelNET is unidirectional)
- **Multiple devices**: Configure up to 32 channels
- **Facade orientation**: Track which blinds face which direction (for solar automations)
- **Floor organization**: Organize blinds by floor level
- **Configurable travel time**: Set individual travel times for accurate positioning
- **Retry mechanism**: Configurable command retries for reliable RF transmission

### New in v2.0.0

- **Virtual Sensors**: Solar exposure per facade, energy savings estimation, daily statistics
- **Connectivity Monitoring**: Binary sensor shows if controller is online/offline
- **Facade & Floor Services**: Control all blinds on a facade or floor with a single service call
- **Automation Blueprints**: Ready-to-use blueprints for common automation scenarios

## Requirements

- InelNET Internet central control unit
- Static IP address configured on the InelNET unit
- Home Assistant 2023.1.0 or newer

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/Scripted20/hacs-inelnet`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "InelNET" and install it
9. Restart Home Assistant
10. Go to Settings → Integrations → Add Integration → Search for "InelNET"

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/inelnet` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to Settings → Integrations → Add Integration → Search for "InelNET"

## Automation Blueprints

Click on a button below to import the blueprint directly into your Home Assistant:

### Solar Protection
Automatically close blinds when the sun is hitting a facade directly.

[![Import Solar Protection](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FScripted20%2Fhacs-inelnet%2Fmain%2Fblueprints%2Fautomation%2Finelnet%2Fsolar_protection.yaml)

### Morning Routine
Open blinds in the morning with different times for weekdays and weekends.

[![Import Morning Routine](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FScripted20%2Fhacs-inelnet%2Fmain%2Fblueprints%2Fautomation%2Finelnet%2Fmorning_routine.yaml)

### Evening Privacy
Close blinds at sunset or at a specific time for privacy.

[![Import Evening Privacy](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FScripted20%2Fhacs-inelnet%2Fmain%2Fblueprints%2Fautomation%2Finelnet%2Fevening_privacy.yaml)

### Weather Protection
Close blinds during extreme heat or high wind conditions.

[![Import Weather Protection](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FScripted20%2Fhacs-inelnet%2Fmain%2Fblueprints%2Fautomation%2Finelnet%2Fweather_protection.yaml)

### Weekly Schedule
Set different open/close times for each day of the week.

[![Import Weekly Schedule](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FScripted20%2Fhacs-inelnet%2Fmain%2Fblueprints%2Fautomation%2Finelnet%2Fweekly_schedule.yaml)

### Away Mode
Simulate presence by randomly moving blinds when you're away.

[![Import Away Mode](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FScripted20%2Fhacs-inelnet%2Fmain%2Fblueprints%2Fautomation%2Finelnet%2Faway_mode.yaml)

## Configuration

The integration is configured through the UI:

1. **Host**: Enter the IP address of your InelNET controller (default: 192.168.1.66)
2. **Number of devices**: How many blinds you want to configure
3. **For each device**:
   - **Channel**: The channel number (1-32)
   - **Name**: Friendly name for the blind
   - **Travel time**: Time in seconds for full open/close (default: 20)
   - **Facade**: Orientation (N, NE, E, SE, S, SV, V, NV)
   - **Floor**: Floor level (parter, etaj, mansarda, demisol)
   - **Shaded**: Whether the blind is shaded (e.g., under a balcony)

### Automation Settings (Options)

After initial setup, go to Settings → Integrations → InelNET → Configure → Automation Settings:

- **Enable virtual sensors**: Toggle solar exposure and statistics sensors
- **Solar threshold**: When to trigger solar protection (%)
- **Weather entity**: Select your weather integration for temperature/wind data
- **Max temperature**: Close blinds above this temperature
- **Max wind speed**: Close blinds above this wind speed

## Virtual Sensors

When enabled, the integration creates these sensors:

| Sensor | Description |
|--------|-------------|
| `sensor.inelnet_solar_exposure_*` | Solar intensity per facade (N, NE, E, SE, S, SV, V, NV) 0-100% |
| `sensor.inelnet_energy_savings_today` | Estimated energy savings in kWh |
| `sensor.inelnet_commands_today` | Number of commands sent today |
| `sensor.inelnet_runtime_today` | Total blind movement time today (minutes) |
| `binary_sensor.inelnet_connected` | Controller online/offline status |

## Services

### `inelnet.send_command`

Send a raw command to any channel.

| Field | Description |
|-------|-------------|
| channel | Channel number (1-32) |
| action | Action code: 160=UP, 176=SHORT UP, 144=STOP, 192=DOWN, 208=SHORT DOWN |

### `inelnet.open_facade`

Open all blinds on a specific facade.

| Field | Description |
|-------|-------------|
| facade | Facade orientation: N, NE, E, SE, S, SV, V, NV |

### `inelnet.close_facade`

Close all blinds on a specific facade.

| Field | Description |
|-------|-------------|
| facade | Facade orientation: N, NE, E, SE, S, SV, V, NV |
| position | (Optional) Target position 0-100, default: 0 (fully closed) |

### `inelnet.open_floor`

Open all blinds on a specific floor.

| Field | Description |
|-------|-------------|
| floor | Floor name: parter, etaj, mansarda, demisol |

### `inelnet.close_floor`

Close all blinds on a specific floor.

| Field | Description |
|-------|-------------|
| floor | Floor name: parter, etaj, mansarda, demisol |
| position | (Optional) Target position 0-100, default: 0 (fully closed) |

## Usage

Once configured, your blinds will appear as cover entities. You can:

- Use the standard cover controls (open, close, stop, set position)
- Include them in automations
- Create scenes
- Control via voice assistants (Alexa, Google Home)

### Example Automation

```yaml
automation:
  - alias: "Close blinds at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: cover.close_cover
        target:
          entity_id: cover.living_room

  - alias: "Close south facade when hot"
    trigger:
      - platform: numeric_state
        entity_id: sensor.inelnet_solar_exposure_s
        above: 70
    condition:
      - condition: numeric_state
        entity_id: weather.home
        attribute: temperature
        above: 25
    action:
      - service: inelnet.close_facade
        data:
          facade: "S"
          position: 20
```

## Dashboard Examples

Ready-to-use Lovelace dashboard configurations are available in the [`examples/`](examples/) folder.

### Quick Actions Card

Add this to any dashboard to control all blinds at once:

```yaml
type: horizontal-stack
cards:
  - type: button
    name: Open All
    icon: mdi:blinds-open
    tap_action:
      action: call-service
      service: cover.open_cover
      target:
        integration: inelnet
  - type: button
    name: Stop
    icon: mdi:stop
    tap_action:
      action: call-service
      service: cover.stop_cover
      target:
        integration: inelnet
  - type: button
    name: Close All
    icon: mdi:blinds
    tap_action:
      action: call-service
      service: cover.close_cover
      target:
        integration: inelnet
```

### Facade Control Buttons

```yaml
type: horizontal-stack
cards:
  - type: button
    name: Close South
    icon: mdi:sun-compass
    tap_action:
      action: call-service
      service: inelnet.close_facade
      data:
        facade: "S"
        position: 20
  - type: button
    name: Open South
    icon: mdi:blinds-open
    tap_action:
      action: call-service
      service: inelnet.open_facade
      data:
        facade: "S"
```

### Solar Exposure Sensor Card

```yaml
type: entities
title: Solar Exposure
entities:
  - entity: sensor.inelnet_solar_exposure_n
    name: North
  - entity: sensor.inelnet_solar_exposure_e
    name: East
  - entity: sensor.inelnet_solar_exposure_s
    name: South
  - entity: sensor.inelnet_solar_exposure_v
    name: West
```

See [`examples/`](examples/) folder for more complete examples including scenes, groups, and automations.

## InelNET Protocol

This integration communicates with the InelNET controller via HTTP POST requests:

```
POST http://{host}/msg.htm
Content-Type: application/x-www-form-urlencoded

send_ch={channel}&send_act={action}
```

**Action codes:**
- `160` - UP (full open)
- `176` - SHORT UP
- `144` - STOP
- `192` - DOWN (full close)
- `208` - SHORT DOWN
- `224` - Programming mode

## Known Limitations

- **No position feedback**: InelNET communication is unidirectional. Position is estimated based on travel time.
- **No status polling**: We cannot query the actual state of blinds.
- **RF reliability**: Commands are sent via RF. The integration sends multiple retries to improve reliability.
- **Blueprints not auto-installed**: HACS doesn't support blueprint distribution. Use the import buttons above.

## Troubleshooting

### Cannot connect to InelNET
- Verify the IP address is correct
- Check that the InelNET unit is powered on
- Ensure your Home Assistant can reach the InelNET network

### Commands not working
- Increase retry count in integration options
- Check RF range between InelNET and blinds
- Verify the channel number matches the blind

### Sensors not appearing
- Go to integration options and ensure "Enable virtual sensors" is checked
- Restart Home Assistant after changing this option

### Blueprints not showing
- Blueprints must be imported manually using the buttons in this README
- HACS does not support automatic blueprint installation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

Developed for the Romanian smart home community using InelNET products.
