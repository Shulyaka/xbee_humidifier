# Home Assistant integration overview

This directory contains the Home Assistant custom component that talks to the
XBee MicroPython firmware over ZHA (Zigbee). It exposes the humidifier zones,
valves, pump/fan controls, and diagnostics as HA entities.

## Entry points
- `custom_components/xbee_humidifier/__init__.py`: sets up the integration,
  creates the API client + coordinator, and forwards config entries to platforms.
- `custom_components/xbee_humidifier/manifest.json`: integration metadata and
  dependency list.

## Architecture
- **Transport / API client**: `coordinator.py` implements
  `XBeeHumidifierApiClient` using ZHA WebSocket service
  `zha.issue_zigbee_cluster_command`.
  - Cluster: `0x11`, endpoint: `0xE8`, command: `0x0000`.
  - Payloads are JSON `{"cmd": "...", "args": ...}`.
  - Responses are JSON with `*_resp` keys and a `nonce` value.
  - One in-flight command per command name (`_awaiting` keyed by `command`).
  - Per-command `asyncio.Lock` to serialize identical commands.
  - ZHA event listener filters `receive_data` by device IEEE and dispatches
    responses or push updates to subscribers.

- **Coordinator**: `XBeeHumidifierDataUpdateCoordinator` runs periodic polling
  (`update_interval=10 min`) and manages "device reset" handling via uptime.
  - Calls `bind` on each refresh to subscribe to device-side pushes.
  - Polls core state: uptime, reset_cause, pump/fan/aux, sensors, valves,
    pump_block, and per-humidifier state.
  - If uptime <= 0 (device reset), it triggers reset callbacks and then pushes a
    computed uptime value back to the device (`uptime` command).

- **Entities**:
  - `humidifier.py`: 3 humidifier entities (zones). Restores previous HA state on
    device reboot and pushes state back to the device (mode, target humidity,
    current humidity, on/off).
  - `switch.py`: pump, fan, aux LED, pump_block. `pump_block` uses `RestoreEntity`
    and re-applies last state on device reset.
  - `valve.py`: 4 valve entities (the 4th is the pressure drop valve).
  - `number.py`: pump speed control (0..1023).
  - `sensor.py`: pump temperature, pressure_in conversion, and uptime with a
    reset_cause attribute.
  - `entity.py`: shared device metadata and SW/HW version info.

## Config / options flow
- `config_flow.py`:
  - User enters the XBee IEEE address.
  - The flow queries the device (`unique_id`, `target_hum`, `sav_hum`) to seed
    defaults for the 3 zones.
  - Options flow allows setting per-zone sensor entity, target/away humidity,
    and min/max humidity constraints.

## Push vs. poll behavior
- Devices push state updates after `bind` (e.g., pump, valve, availability).
- Entities register with `XBeeHumidifierApiClient.add_subscriber` for live
  updates and also rely on coordinator data during refreshes.

## Reset handling
- The device reports uptime; negative uptime is treated as "device rebooted".
- Coordinator triggers `device_reset` callbacks to re-apply HA state to the
  device and schedules a refresh.
- `sensor.py` maps numeric reset causes to strings for the uptime sensor.

## Key files to read first
- `custom_components/xbee_humidifier/coordinator.py`
- `custom_components/xbee_humidifier/humidifier.py`
- `custom_components/xbee_humidifier/switch.py`
- `custom_components/xbee_humidifier/sensor.py`

## Gotchas / constraints
- Only one request per command can be in-flight at a time; callers must avoid
  sending duplicate commands concurrently.
- The response matching is keyed by `command`, not `nonce`, so overlapping
  commands of the same type will conflict. The above constraint is implemented
  to avoid this. 
- `bind` is called on every refresh to ensure push updates remain active.
