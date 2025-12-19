#!/usr/bin/env python3
"""
Simple TCP telemetry simulator sending JSON lines to clients.
Use it to test the Streamlit frontend without hardware.

Example:
python simulator.py --host 127.0.0.1 --port 9999
"""
import argparse
import json
import socket
import threading
import time
import random

def handle_client(conn, addr):
    print("Client connected:", addr)
    try:
        while True:
            t = int(time.time() * 1000)
            az = int(90 + 20 * random.uniform(-1, 1) * random.choice([1,0.5,0.2]))
            el = int(45 + 10 * random.uniform(-1, 1))
            pwm_az = az
            pwm_el = el
            ia = round(0.08 + random.random() * 0.05, 3)
            ib = round(0.07 + random.random() * 0.05, 3)
            v = round(12.0 + random.uniform(-0.2, 0.2), 2)
            payload = {"t": t, "az": az, "el": el, "pwm_az": pwm_az, "pwm_el": pwm_el, "ia": ia, "ib": ib, "v": v}
            line = json.dumps(payload) + "\n"
            conn.sendall(line.encode("utf-8"))
            time.sleep(0.5)
    except (BrokenPipeError, ConnectionResetError):
        print("Client disconnected:", addr)
    finally:
        conn.close()

def run_server(host, port):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    print(f"Simulator listening on {host}:{port}")
    try:
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    finally:
        srv.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    args = parser.parse_args()
    run_server(args.host, args.port)
