# Repository overview

This repo contains two main parts of the same system:
- MicroPython firmware for an XBee module in `flash/` (device-side control).
- A Home Assistant custom component in `custom_components/xbee_humidifier/`.

Use the scoped docs for each part:
- `flash/AGENTS.md`
- `custom_components/xbee_humidifier/AGENTS.md`

## Top-level layout
- `flash/`: MicroPython firmware, bundling logic, and hardware control code.
- `custom_components/xbee_humidifier/`: Home Assistant integration.
- `tests/`, `tests_ha/`: test suites for firmware/helpers and HA integration.
- `setup.py`, `setup.cfg`: packaging for the Python portions.
- `hacs.json`: HACS metadata.

## Project intent
The firmware implements local control logic for a humidifier (pump, valves, fan)
and exposes a JSON command interface over Zigbee. The HA integration uses ZHA to
send commands, pull periodic state, and subscribe to push updates.

## What to read first
- `flash/AGENTS.md`
- `custom_components/xbee_humidifier/AGENTS.md`
- `README.md` for background and hardware context.
