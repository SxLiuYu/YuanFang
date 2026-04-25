#!/usr/bin/env python3
"""
Termux Sensor Client - Simple version
Pushes sensor data to Flask server every interval
Works without termux-api (uses termux_agent /sensors endpoint)
"""
import os, sys, json, time
import urllib.request
import urllib.error
from datetime import datetime

DEFAULT_SERVER = "http://192.168.1.3:8000"
TERMUX_API = "http://192.168.1.10:8080"
NODE_ID = "termux_vivo_x9s"
INTERVAL = 60  # seconds

def get_sensors():
    """Fetch sensor data from termux_agent"""
    try:
        req = urllib.request.Request(f"{TERMUX_API}/sensors", method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def push_sensors(server_url, node_id, data):
    """Push sensor data to Flask server"""
    try:
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{server_url}/api/sensors/{node_id}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def main():
    print(f"Termux Sensor Client starting")
    print(f"Server: {DEFAULT_SERVER}")
    print(f"Node ID: {NODE_ID}")
    print(f"Interval: {INTERVAL} seconds")
    
    while True:
        try:
            # Get sensor data
            sensors = get_sensors()
            sensors["node_id"] = NODE_ID
            sensors["pushed_at"] = datetime.now().isoformat()
            
            # Push to server
            result = push_sensors(DEFAULT_SERVER, NODE_ID, sensors)
            
            ts = datetime.now().strftime("%H:%M:%S")
            if "error" in result:
                print(f"[{ts}] Push failed: {result['error']}")
            else:
                print(f"[{ts}] Pushed: device={sensors.get('device', {}).get('model', '?')}, battery={sensors.get('battery', {}).get('status', '?')}")
        
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
