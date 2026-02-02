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

  - alias: "Open south-facing blinds in winter morning"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: template
        value_template: "{{ now().month in [11, 12, 1, 2] }}"
    action:
      - service: cover.open_cover
        target:
          entity_id:
            - cover.living_3
            - cover.living_4
```

### Services

#### `inelnet.send_command`

Send a raw command to any channel.

| Field | Description |
|-------|-------------|
| channel | Channel number (1-32) |
| action | Action code: 160=UP, 176=SHORT UP, 144=STOP, 192=DOWN, 208=SHORT DOWN |

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

### Tile Card with Position Slider

For individual blind control with position:

```yaml
type: tile
entity: cover.living_room
features:
  - type: cover-open-close
  - type: cover-position
```

### Auto-Generated Dashboard (requires auto-entities from HACS)

Automatically lists all InelNET blinds:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: All Blinds
  show_header_toggle: false
filter:
  include:
    - integration: inelnet
      domain: cover
sort:
  method: name
```

See [`examples/dashboard-universal.yaml`](examples/dashboard-universal.yaml) for more complete examples.

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

## Troubleshooting

### Cannot connect to InelNET
- Verify the IP address is correct
- Check that the InelNET unit is powered on
- Ensure your Home Assistant can reach the InelNET network

### Commands not working
- Increase retry count in integration options
- Check RF range between InelNET and blinds
- Verify the channel number matches the blind

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

Developed for the Romanian smart home community using InelNET products.
