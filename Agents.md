# Agent Definition - Touchscreen Login UI (tblogin)

## Description
A Python Tkinter GUI application designed to run on the 10" HDMI touch screen. It acts as the local physical terminal interface for TrumpyBear biometric logins, manual servo turret testing, and system arm/disarm status.

## Role & Responsibilities
- **Biometric UI Interface:** Receives facial-recognition recognition payloads from camera/Frigate logs to authenticate and log in users.
- **Ranger Guidance:** Displays instructional guides and metrics when users are in range of the ultrasonic sensor.
- **Calibration Slider Controls:** Renders interactive scroll elements to pan/tilt turrets manually during maintenance and verification.
- **SayoDevice Integration:** Integrates external input triggers from physical keypad inputs via USB.

## Key Files
- [login.py](file:///home/ccoupe/Projects/iot/tblogin/login.py) - Main application UI controller and Tkinter loop.
- [TurretSlider.py](file:///home/ccoupe/Projects/iot/tblogin/TurretSlider.py) - Turret manual targeting controls component.
- [Homie_MQTT.py](file:///home/ccoupe/Projects/iot/tblogin/Homie_MQTT.py) - Local Homie convention MQTT handler.
- [Settings.py](file:///home/ccoupe/Projects/iot/tblogin/Settings.py) - UI setting, fonts, fullscreen toggle, and layout preferences.

## Integration Points
- **Subscribed MQTT Topics:**
  - `homie/test_bear/screen/control/set` (UI render and state command packets from Core Bear)
  - `homie/trumpy_ranger/display/mode/set` / `text/set` (Range tracking status metrics)
  - `homie/turret_front/turret_1/control` (Front servo turret orientation/status)
  - `homie/turret_back/turret_1/control` (Rear servo turret orientation/status)
  - `frig-fc/face_recog` (Biometric facial recognition events from Frigate)
- **Published MQTT Topics:**
  - `homie/test_bear/control/cmd/set` (Disarm or override target system states)
  - `homie/turret_front/turret_1/control/set` (Manual servo movement target commands)
  - `homie/turret_back/turret_1/control/set` (Manual servo movement target commands)

## Context & Memory
- The application was originally documented in Ruby/Shoes, but has been completely re-implemented in Python utilizing standard `tkinter`.
- Can run either fullscreen (typical for Raspberry Pi) or inside windowed desktop environments depending on the `fullscreen` config.
