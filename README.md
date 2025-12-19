# SOLAR-TRACKING-SYSTEM

Description
-----------
A dual-axis solar tracking system firmware (Arduino) and a Streamlit frontend that displays real-time servo motor metrics. The firmware reads four light sensors (LDRs) to compute elevation and azimuth errors, drives two servos (dual-axis), and streams telemetry over Serial (JSON). The Streamlit app connects to the telemetry stream (Serial or TCP simulator) and visualizes servo positions, PWM, and simulated electrical metrics.

Repository layout
----------------
- firmware/
  - tracker.ino            - Arduino sketch (dual-axis tracker + serial telemetry)
- frontend/
  - app.py                 - Streamlit dashboard reading telemetry (Serial or TCP)
  - simulator.py           - TCP telemetry simulator (useful for testing without hardware)
  - requirements.txt       - Python requirements for the frontend

Features
--------
- Dual-axis control based on 4 LDR sensors (NE, NW, SE, SW arrangement).
- Smooth servo movement with simple proportional control and limits.
- Telemetry output as JSON over Serial:
  {"t": ..., "az": ..., "el": ..., "pwm_az": ..., "pwm_el": ..., "ia": ..., "ib": ..., "v": ...}
- Streamlit dashboard:
  - Realtime numeric metrics and line charts
  - Select Serial port or Simulated TCP source
  - Simple persistent history in session state

Hardware (example)
------------------
- Microcontroller: Arduino Uno / Nano / compatible
- 2x Hobby servos (e.g., SG90/ MG90S)
- 4x LDRs (photoresistors)
- 4x 10k resistors (voltage dividers for LDRs)
- Optional: current sensors (ACS712) and voltage divider for battery measurement
- Power supply: appropriate battery / USB (be careful powering servos directly from Arduino 5V pin — use separate supply with common ground)

Wiring (suggested)
------------------
- LDRs wired as voltage dividers to A0, A1, A2, A3.
  - A0: LDR_NE, A1: LDR_NW, A2: LDR_SE, A3: LDR_SW
- Servo Azimuth -> digital PWM pin 9
- Servo Elevation -> digital PWM pin 10
- Optional current sensors -> analog pins (commented in firmware)

Build & Upload (firmware)
-------------------------
1. Open `firmware/tracker.ino` in Arduino IDE.
2. Configure pins and PID/scale constants if needed.
3. Select board and COM port, then Upload.

Run frontend (Streamlit)
------------------------
1. Create a Python venv (recommended) and activate it.
2. Install requirements:
   pip install -r frontend/requirements.txt
3. If you have the tracker hardware connected via USB, set `Source = Serial` in the app and choose the right port (e.g., COM3 or /dev/ttyUSB0).
   - Baudrate default: 115200
4. If you don't have hardware, start the simulator:
   python frontend/simulator.py --host 127.0.0.1 --port 9999
   Then in the app choose `Source = TCP` and enter host: 127.0.0.1, port: 9999
5. Run Streamlit:
   streamlit run frontend/app.py

Telemetry protocol (JSON per line)
----------------------------------
The firmware prints one JSON object per line. Example:
{"t":1623456789,"az":120,"el":45,"pwm_az":95,"pwm_el":80,"ia":0.12,"ib":0.14,"v":12.1}

Where:
- t: epoch millis (unsigned long)
- az: azimuth servo angle (degrees)
- el: elevation servo angle (degrees)
- pwm_az, pwm_el: last PWM/write values (0-255 or 0-180 depending on implementation)
- ia, ib: simulated/measured currents (A) for each servo
- v: supply voltage (V)

Notes & next steps
------------------
- The firmware uses a simple P-controller. For smoother tracking, tune the gains or add full PID.
- If you add real current/voltage sensors, replace the simulated values in firmware with actual ADC readings and proper scaling.
- Consider adding logging on the Streamlit side and a data export feature (CSV).
- For production use, implement safety checks (stall detection, temperature limits, mechanical end-stops).

License
-------
MIT
