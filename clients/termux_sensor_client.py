#!/usr/bin/env python3
"""
Termux 传感器采集客户端 v3
支持 HTTP 轮询 + WebSocket 实时推送两种模式�?

用法:
    # WebSocket 模式（推荐，实时推送）
    python3 termux_sensor_client.py --server ws://192.168.1.11:8000

    # HTTP 轮询模式（兼容旧版）
    python3 termux_sensor_client.py --server http://192.168.1.11:8000 --interval 60

依赖（WebSocket 模式需要）:
    pip install websocket-client
"""

import os
import sys
import json
import time
import socket
import argparse
from datetime import datetime

# ============== 配置 ==============
DEFAULT_SERVER = "ws://192.168.1.11:8000"
TERMUX_API = "http://192.168.1.10:8080"
NODE_ID = "termux_sensor_01"
INTERVAL = 60  # HTTP 轮询间隔（秒�?
WS_INTERVAL = 30  # WebSocket 推送间隔（秒）
HEARTBEAT_INTERVAL = 15  # 心跳间隔（秒�?

# ============== 通过 HTTP API 执行命令 ==============

def exec_on_termux(cmd, timeout=5):
    """通过 termux_agent HTTP API 执行命令"""
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{TERMUX_API}/exec",
            data=json.dumps({"command": cmd}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
            if d.get("rc", -1) == 0:
                return d.get("stdout", "").strip()
            else:
                return None
    except Exception as e:
        print(f"exec error: {e}")
        return None


def get_device_info():
    """获取设备基本信息"""
    model = exec_on_termux("getprop ro.product.model")
    brand = exec_on_termux("getprop ro.product.brand")
    android = exec_on_termux("getprop ro.build.version.release")
    return {
        "model": model or "unknown",
        "brand": brand or "unknown",
        "android": android or "unknown"
    }


def get_battery_info():
    """获取电池信息"""
    paths = [
        "/sys/class/power_supply/battery/capacity",
        "/sys/class/power_supply/battery/status",
        "/sys/class/power_supply/battery/temp",
    ]
    result = {}
    for p in paths:
        val = exec_on_termux(f"cat {p}")
        if val:
            key = p.split("/")[-1]
            result[key] = val
    return result if result else "unavailable"


def get_wifi_info():
    """获取 WiFi 信息"""
    ip_out = exec_on_termux("ip addr show wlan0 2>/dev/null | grep 'inet '")
    mac_out = exec_on_termux("ip addr show wlan0 2>/dev/null | grep ether")
    # 尝试获取 SSID
    ssid = exec_on_termux(
        "dumpsys wifi 2>/dev/null | grep 'SSID:' | head -1 | sed 's/.*SSID: //' | tr -d '\"'"
    )

    ip = ""
    if ip_out:
        parts = ip_out.strip().split()
        if len(parts) >= 2:
            ip = parts[1].split('/')[0]

    mac = ""
    if mac_out:
        parts = mac_out.strip().split()
        if len(parts) >= 2:
            mac = parts[1]

    return {"ip": ip, "mac": mac, "ssid": ssid or "unknown"}


def get_lan_devices():
    """扫描 ARP 表获取局域网在线设备"""
    arp_out = exec_on_termux("cat /proc/net/arp")
    devices = []
    if not arp_out:
        return devices

    for line in arp_out.split('\n'):
        parts = line.split()
        if len(parts) >= 4 and parts[0].count('.') == 3:
            ip = parts[0]
            hw_addr = parts[3]
            if hw_addr != "00:00:00:00:00:00":
                devices.append({"ip": ip, "mac": hw_addr})
    return devices


def get_location():
    """尝试获取位置信息（通过 Termux Location API�?""
    try:
        import urllib.request
        url = f"{TERMUX_API}/location"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode("utf-8"))
            return d
    except Exception:
        return None


def collect_sensor_data():
    """采集所有传感器数据（v3 增强版）"""
    data = {
        "node_id": NODE_ID,
        "timestamp": datetime.now().isoformat(),
        "device": get_device_info(),
        "sensors": {
            "wifi": get_wifi_info(),
            "battery": get_battery_info(),
            "lan_devices": get_lan_devices(),
        }
    }
    return data


# ============== HTTP 模式 ==============

def post_data(server_url, data):
    """POST 数据到主服务（HTTP 模式�?""
    import urllib.request

    url = f"{server_url}/api/sensor"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return True, result
    except Exception as e:
        return False, str(e)


def http_mode(server_url, interval):
    """HTTP 轮询模式"""
    print(f"[HTTP 模式] 轮询间隔 {interval}s")

    while True:
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{ts}] 采集数据...")

        data = collect_sensor_data()
        print(f"  设备: {data['device']['brand']} {data['device']['model']} (Android {data['device']['android']})")
        print(f"  WiFi: {data['sensors']['wifi'].get('ssid', 'unknown')}")
        print(f"  电池: {data['sensors']['battery']}")
        print(f"  LAN设备: {len(data['sensors']['lan_devices'])}�?)

        success, result = post_data(server_url, data)
        if success:
            print(f"  上报成功: {result}")
        else:
            print(f"  上报失败: {result}")

        time.sleep(interval)


# ============== WebSocket 模式 ==============

def ws_mode(server_url, interval):
    """WebSocket 实时推送模�?""
    try:
        import websocket
    except ImportError:
        print("�?WebSocket 模式需要安装依�? pip install websocket-client")
        print("   回退�?HTTP 模式...")
        http_url = server_url.replace("ws://", "http://").replace("wss://", "https://")
        http_mode(http_url, interval)
        return

    # WebSocket 事件
    def on_open(ws):
        print(f"�?已连接到 {server_url}")
        # 发送注册消�?
        register = {
            "type": "register",
            "node_id": NODE_ID,
            "device": get_device_info(),
        }
        ws.send(json.dumps(register))
        print(f"  节点 ID: {NODE_ID}")

    def on_message(ws, message):
        """收到服务端指�?""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "command":
                cmd = data.get("action", "")
                params = data.get("params", {})
                cmd_id = data.get("command_id", "")
                print(f"\n[指令] {cmd_id}: {cmd} {params}")
                handle_command(ws, cmd_id, cmd, params)

            elif msg_type == "snapshot_request":
                """服务端要求立即快�?""
                sensor_data = collect_sensor_data()
                sensor_data["type"] = "sensor_update"
                ws.send(json.dumps(sensor_data))
                print(f"[快照] 响应服务端快照请�?)

            elif msg_type == "pong":
                pass  # 心跳响应

            elif msg_type == "config":
                """服务端下发配置更�?""
                new_interval = data.get("interval")
                if new_interval:
                    nonlocal interval
                    interval = new_interval
                    print(f"[配置] 更新推送间隔为 {interval}s")

        except json.JSONDecodeError:
            pass

    def on_error(ws, error):
        print(f"[错误] {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"\n[断开] 连接关闭 ({close_status_code}), {close_interval}s 后重�?..")
        time.sleep(reconnect_interval)
        reconnect(ws)

    def reconnect(ws):
        """断线重连"""
        attempts = 0
        while attempts < 10:
            attempts += 1
            print(f"[重连] �?{attempts} 次尝�?..")
            try:
                ws.url = server_url
                ws.run_forever()
                return
            except Exception as e:
                print(f"[重连] 失败: {e}")
                time.sleep(min(attempts * 5, 30))
        print("[重连] 超过 10 次，退�?)
        sys.exit(1)

    def handle_command(ws, cmd_id, cmd, params):
        """处理服务端下发的指令"""
        result = {"success": False, "data": None}

        if cmd == "take_photo":
            output = params.get("output", "/data/data/com.termux/files/home/photo.jpg")
            exec_on_termux(f"termux-camera-photo -c 0 {output}")
            result = {"success": True, "data": {"path": output}}

        elif cmd == "get_location":
            loc = get_location()
            result = {"success": loc is not None, "data": loc}

        elif cmd == "vibrate":
            duration = params.get("duration", 500)
            exec_on_termux(f"termux-vibrate -d {duration}")
            result = {"success": True}

        elif cmd == "notify":
            title = params.get("title", "元芳")
            content = params.get("content", "")
            exec_on_termux(f"termux-notification --title '{title}' --content '{content}'")
            result = {"success": True}

        elif cmd == "set_interval":
            nonlocal interval
            interval = params.get("interval", 30)
            result = {"success": True, "data": {"interval": interval}}

        # 回报结果
        ws.send(json.dumps({
            "type": "command_result",
            "command_id": cmd_id,
            "result": result,
        }))

    # 连接参数
    reconnect_interval = 5
    ws = websocket.WebSocketApp(
        server_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # 设置心跳
    ws.run_forever(ping_interval=HEARTBEAT_INTERVAL, ping_timeout=10)


# ============== 主程�?==============

def main():
    parser = argparse.ArgumentParser(description="Termux 传感器采集客户端 v3")
    parser.add_argument("--server", default=DEFAULT_SERVER,
                        help="主服务地址（ws:// �?http://�?)
    parser.add_argument("--interval", type=int, default=INTERVAL,
                        help="推送间�?�?，默�?60")
    parser.add_argument("--node-id", default=NODE_ID,
                        help="节点 ID，默�?termux_sensor_01")
    parser.add_argument("--termux-api", default=TERMUX_API,
                        help="Termux Agent API 地址")
    parser.add_argument("--ws", action="store_true",
                        help="强制使用 WebSocket 模式")
    parser.add_argument("--http", action="store_true",
                        help="强制使用 HTTP 轮询模式")
    args = parser.parse_args()

    global NODE_ID, TERMUX_API
    NODE_ID = args.node_id
    TERMUX_API = args.termux_api

    print("=" * 50)
    print("Termux 传感器采集客户端 v3")
    print(f"节点 ID: {NODE_ID}")
    print(f"主服�? {args.server}")
    print(f"Termux API: {TERMUX_API}")
    print("=" * 50)

    # 自动检测模�?
    if args.http:
        server = args.server.replace("ws://", "http://").replace("wss://", "https://")
        http_mode(server, args.interval)
    elif args.ws or args.server.startswith("ws://") or args.server.startswith("wss://"):
        ws_mode(args.server, args.interval)
    else:
        # 默认�?HTTP
        http_mode(args.server, args.interval)


if __name__ == "__main__":
    main()

