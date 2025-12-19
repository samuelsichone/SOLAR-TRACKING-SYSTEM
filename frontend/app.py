"""
Streamlit dashboard for servo telemetry.
Supports two sources:
 - Serial (pyserial): reads JSON lines from a COM/tty port
 - TCP: connects to a host:port and reads JSON lines (compatible with simulator.py)

Run:
streamlit run frontend/app.py
"""
import streamlit as st
import json
import time
import threading
import queue
from collections import deque

# Optional imports at runtime
try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None
import socket

st.set_page_config(page_title="Solar Tracker Telemetry", layout="wide")

st.title("Dual-Axis Solar Tracker — Telemetry Dashboard")

# Session state containers
if "running" not in st.session_state:
    st.session_state.running = False
if "data" not in st.session_state:
    st.session_state.data = deque(maxlen=500)  # store last N telemetry points

# Source selection UI
col1, col2 = st.columns([1, 2])
with col1:
    source = st.selectbox("Telemetry Source", ["Serial", "TCP", "Upload (file)"])
if source == "Serial":
    port = st.text_input("Serial port (e.g., COM3 or /dev/ttyUSB0)", value="")
    baud = st.number_input("Baudrate", value=115200)
else:
    port = st.text_input("Host (for TCP)", value="127.0.0.1:9999")

start_stop = st.button("Start" if not st.session_state.running else "Stop")

# Background reader thread and queue
if "queue" not in st.session_state:
    st.session_state.queue = queue.Queue()

def serial_reader_loop(port_name, baudrate, q):
    try:
        ser = serial.Serial(port_name, baudrate, timeout=1)
    except Exception as e:
        q.put({"error": f"Serial open error: {e}"})
        return
    try:
        while st.session_state.running:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                q.put(obj)
            except Exception as e:
                # ignore parse failures
                pass
    finally:
        ser.close()

def tcp_reader_loop(host, portnum, q):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, portnum))
    except Exception as e:
        q.put({"error": f"TCP connect error: {e}"})
        return
    f = s.makefile("r")
    try:
        while st.session_state.running:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                obj = json.loads(line)
                q.put(obj)
            except Exception:
                pass
    finally:
        try:
            s.close()
        except:
            pass

# Start/stop handling
if start_stop:
    if not st.session_state.running:
        st.session_state.running = True
        # clear old data
        st.session_state.data.clear()
        # start reader thread
        st.session_state.queue = queue.Queue()
        if source == "Serial":
            if serial is None:
                st.error("pyserial is not installed in this environment. Install via pip install pyserial")
                st.session_state.running = False
            else:
                t = threading.Thread(target=serial_reader_loop, args=(port, baud, st.session_state.queue), daemon=True)
                t.start()
        elif source == "TCP":
            # parse host:port
            try:
                host, portnum = port.split(":")
                portnum = int(portnum)
                t = threading.Thread(target=tcp_reader_loop, args=(host, portnum, st.session_state.queue), daemon=True)
                t.start()
            except Exception as e:
                st.error(f"Invalid host:port — {e}")
                st.session_state.running = False
        else:
            st.session_state.running = False
    else:
        st.session_state.running = False

# Display area
placeholder = st.empty()

# Helper to consume queue and push into session_state.data
def consume_queue():
    q = st.session_state.queue
    while not q.empty():
        try:
            item = q.get_nowait()
        except queue.Empty:
            break
        if isinstance(item, dict) and "error" in item:
            st.error(item["error"])
            st.session_state.running = False
            break
        st.session_state.data.append(item)

# Main UI update
with placeholder.container():
    status_col, metrics_col = st.columns([1, 3])
    with status_col:
        st.write("Status")
        st.write("Running" if st.session_state.running else "Stopped")
        st.write(f"Buffered points: {len(st.session_state.data)}")
        if st.session_state.data:
            last = st.session_state.data[-1]
            st.write("Last timestamp:", last.get("t"))
    with metrics_col:
        # consume incoming data
        consume_queue()

        # Prepare lists for charts
        times = [d.get("t", i) for i, d in enumerate(st.session_state.data)]
        az_list = [d.get("az") for d in st.session_state.data]
        el_list = [d.get("el") for d in st.session_state.data]
        ia_list = [d.get("ia") for d in st.session_state.data]
        ib_list = [d.get("ib") for d in st.session_state.data]
        v_list = [d.get("v") for d in st.session_state.data]

        # Top metrics
        cols = st.columns(4)
        if st.session_state.data:
            last = st.session_state.data[-1]
            cols[0].metric("Azimuth (deg)", last.get("az", "-"))
            cols[1].metric("Elevation (deg)", last.get("el", "-"))
            cols[2].metric("Servo A Current (A)", last.get("ia", "-"))
            cols[3].metric("Supply Voltage (V)", last.get("v", "-"))
        else:
            cols[0].metric("Azimuth (deg)", "-")
            cols[1].metric("Elevation (deg)", "-")
            cols[2].metric("Servo A Current (A)", "-")
            cols[3].metric("Supply Voltage (V)", "-")

        # Charts
        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.subheader("Servo angles")
            import pandas as pd
            df = pd.DataFrame({"Azimuth": az_list, "Elevation": el_list})
            if not df.empty:
                df.index = pd.to_datetime(times, unit="ms")
                st.line_chart(df)
        with chart_cols[1]:
            st.subheader("Electrical metrics")
            df2 = pd.DataFrame({"Ia": ia_list, "Ib": ib_list, "V": v_list})
            if not df2.empty:
                df2.index = pd.to_datetime(times, unit="ms")
                st.line_chart(df2)

# Auto-refresh while running
if st.session_state.running:
    st.experimental_rerun()
