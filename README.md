# xbee_humidifier
![CI](https://github.com/Shulyaka/xbee_humidifier/actions/workflows/xbee_humidifier.yml/badge.svg?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/Shulyaka/xbee_humidifier/badge.svg?branch=master)](https://coveralls.io/github/Shulyaka/xbee_humidifier?branch=master)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

MicroPython firmware and Home Assistant custom component for my DIY humidifier

## What is this about?
I've built a high pressure humidifier for myself and made it smart using Home Assistant.

The first Proof-of-Concept approach was a centralized solution implementing with low-level control of the device (like start/stop the engine duty cycle or open/close the valve) with higher-level logic implemented on Home Assistant side using automations defined in yaml. That approach had two disadvantages: firstly, the humidifier could find itself on undefined state (possible being indefinitely on) in the event of connection failure from HA of any kind (reboot, wireless interference, software error, etc), and secondly, only one instance of HA could control the humidifier (no redundance possible).

This repo is the second approach implementing local in-device control with high-level commands (such as change target humidity, update measured humidity, etc), allowing several hosts to control the same device, and a custom component for Home Assistant.

### You may find parts of this repo useful for your own MicroPython projects, such as:
1. Main loop implementation with task scheduling. Be careful with the stack size, which is very small on XBees, if you experience unexplained software reboots, then refactor your code scheduling tasks into the main loop instead of calling them directly because that would use the stack
2. Hardware abstraction layer for different kinds of inputs/outputs (virtual, gpio, external relay boards, binary or analog) with low pass filter and trigger callbacks support
3. JSON command interface with the host over ZigBee
4. A remote logger
5. An example of Github-CI pipeline with tests for both micropython and HA custom component

## Setup
Hardware:
1. Reverse osmosis filter
2. High pressure pump (I use SpeedMax)
3. High pressure valves
4. Relay board controlled by XBee (I use TOSR04-T)
5. The XBee3 module with zigbee3 stack capable of running MicroPython
6. A single-board computer capable of hosting Home Assistant with ZigBee stick
7. Zigbee humidity and water leak sensors (I use Aqara)

Software:
1. Home Assistant
2. XCTU (optional, for initial configuration)

![image](https://github.com/Shulyaka/xbee_humidifier/assets/2741408/1bde427c-6b78-420a-9ca6-a9678a8affea)
![image](https://github.com/Shulyaka/xbee_humidifier/assets/2741408/1ffda79b-5865-4031-8e36-aac3dec9fee7)
