# MicroPython (XBee) subsystem overview

This directory contains the firmware that runs on the XBee module. It controls
humidifier hardware (pump, fan, valves, aux LED) and exposes a JSON command API
over Zigbee for Home Assistant (HA) to query state and issue control commands.

## Entry points and boot flow
- `flash/main.py` is the MicroPython entry point. It first tries to import the
  bundled code (`bundle`) and soft-resets after bundling. If bundling fails it
  falls back to the normal app import.
- `flash/__init__.py` performs runtime setup: instantiates sensors/switches,
  humidifiers, the duty-cycle controller, and the Zigbee command handler.
  It also enables the watchdog in non-debug mode and feeds it from the main loop.

## Architecture
- **Event loop**: `flash/lib/mainloop.py` provides a cooperative task scheduler.
  Tasks run from callbacks; exceptions are logged but do not crash the loop.
- **Core model**: `flash/lib/core.py` defines `Sensor` and `Switch` classes with
  subscription callbacks, plus a `Commands` base class that reads Zigbee frames
  and dispatches JSON commands.
- **Hardware abstraction**:
  - `flash/lib/xbeepin.py` wraps XBee GPIO/ADC/PWM as `Sensor` subclasses.
  - `flash/tosr0x.py` implements a serial protocol for the TOSR0X relay board.
  - `flash/tosr.py` exposes TOSR relays/temperature as `Sensor` objects.
- **Application logic**:
  - `flash/humidifier.py` implements humidifier behavior per zone (state,
    target humidity, away mode, stall detection, hysteresis).
  - `flash/dutycycle.py` runs a slow PWM-like duty cycle for the pump/valves,
    with safety timeouts and a pressure drop sequence.
  - `flash/commands.py` defines the remote command surface (pump, fan, target_hum,
    etc.) and a subscription mechanism for push updates.
- **Logging**: `flash/lib/logging.py` sends JSON log records to the coordinator.

## Zigbee command protocol
- Payloads are JSON objects like `{ "cmd": "pump", "args": true }`.
- Responses are JSON with a `*_resp` key and a monotonically increasing `nonce`.
- `cmd_bind` subscribes a coordinator EUI64 to update pushes for key sensors
  (pump, pump_temp, pressure_in, valves, available/zone state).
- `cmd_uptime` returns strartup time as UNIX timestamp (as positive integer), or 
  seconds since startup (as a negative value). Negative values are used to
  signal "device reset", because the module does not have RTC, after which HA
  sets the UNIX timestamp using its clock.

## Runtime behavior details
- The main loop schedules:
  - command receive polling every 500 ms,
  - uptime telemetry every 30 seconds,
  - sensor polling (periodic `Sensor` updates for ADC/GPIO/TOSR devices),
  - duty-cycle and humidifier control tasks on demand.
- Watchdog: enabled in non-debug mode with 30s timeout and fed every 1s.
- `config.debug` is true when TOSR0X is not detected, which switches to
  simulation-mode sensors and prints debug state.

## Bundling / deployment
- `flash/bundle.py` compiles `.py` to `.mpy` and bundles them into a single
  module (`bundle.mpy`) for faster load and smaller footprint.
- The bundle stage toggles API mode and triggers a soft reset to restart.

## Integration surface (HA expects)
- Commands used by HA include: `pump`, `fan`, `aux_led`, `pump_temp`,
  `pressure_in`, `pump_speed`, `valve`, `pump_block`, `sav_hum`, `available`,
  `zone`, `hum`, `cur_hum`, `target_hum`, `mode`, `reset_cause`, `unique_id`.

## Files to start reading
- `flash/__init__.py` (runtime setup)
- `flash/lib/core.py` (commands + base Sensor/Switch)
- `flash/commands.py` (remote API)
- `flash/humidifier.py` and `flash/dutycycle.py` (control logic)
