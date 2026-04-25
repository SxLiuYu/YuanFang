#!/usr/bin/env python3
"""
Termux Agent - Lightweight HTTP API for Termux
Works without termux-api (uses getprop, proc files)
"""
import os, sys, json, time, signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import subprocess

HOST, PORT = "0.0.0.0", 8080

def exec_cmd(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip()[:2000], "stderr": r.stderr.strip()[:500], "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}

def get_device_info():
    """Get device info via getprop"""
    brand = exec_cmd("getprop ro.product.brand")
    model = exec_cmd("getprop ro.product.model")
    android = exec_cmd("getprop ro.build.version.release")
    return {
        "brand": brand.get("stdout", "unknown"),
        "model": model.get("stdout", "unknown"),
        "android": android.get("stdout", "unknown"),
    }

def get_battery_simple():
    """Try to read battery from /sys or use termux-battery-status with short timeout"""
    # Try termux-battery-status with short timeout
    r = exec_cmd("termux-battery-status", timeout=3)
    if r["rc"] == 0 and r["stdout"]:
        try:
            return json.loads(r["stdout"])
        except:
            pass
    return {"status": "unavailable", "note": "termux-api timeout"}

class H(BaseHTTPRequestHandler):
    def log_message(self, f, *args): pass

    def send_json(self, d, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/health":
            info = get_device_info()
            self.send_json({"status": "ok", "node": "termux", "ip": "192.168.1.10", "device": info})
        elif p == "/device":
            self.send_json({"success": True, "data": get_device_info()})
        elif p == "/battery":
            self.send_json({"success": True, "data": get_battery_simple()})
        elif p == "/wifi":
            # Try termux-wifi-connectioninfo but don't wait long
            r = exec_cmd("termux-wifi-connectioninfo", timeout=3)
            self.send_json({"success": True, "data": {"stdout": r.get("stdout", ""), "available": r["rc"] == 0}})
        elif p == "/location":
            r = exec_cmd("termux-location -r last", timeout=5)
            self.send_json({"success": True, "data": r})
        elif p == "/sensors":
            # Combined sensor data
            self.send_json({
                "device": get_device_info(),
                "battery": get_battery_simple(),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(content_length) or "{}")
        except:
            d = {}
        p = urlparse(self.path).path
        if p == "/exec":
            cmd = d.get("command", "")
            timeout = int(d.get("timeout", 5))
            self.send_json(exec_cmd(cmd, timeout=timeout))
        else:
            self.send_json({"error": "not found"}, 404)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    print(f"Termux Agent starting on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), H).serve_forever()
