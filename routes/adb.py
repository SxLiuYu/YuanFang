"""
ADB 远程控制路由
实现对 Android 手机的远程控制，支持：
- 执行 adb 命令
- 截图
- 点击/滑动操作
- 安装 APK
- 获取设备信息
"""
import os
import logging
import subprocess
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, current_app

logger = logging.getLogger(__name__)
adb_bp = Blueprint('adb', __name__, url_prefix='/api/adb')


def run_adb_command(cmd_args):
    """运行 adb 命令，返回 (output, error, returncode)"""
    try:
        result = subprocess.run(
            ["adb"] + cmd_args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1


@adb_bp.route('/devices', methods=['GET'])
def list_devices():
    """列出所有连接的 ADB 设备"""
    stdout, stderr, code = run_adb_command(["devices"])
    lines = stdout.strip().split('\n')
    devices = []
    for line in lines[1:]:
        line = line.strip()
        if line:
            parts = line.split()
            if len(parts) >= 2:
                devices.append({"serial": parts[0], "status": parts[1]})
    
    return jsonify({
        "success": code == 0,
        "devices": devices,
        "raw_output": stdout,
        "error": stderr
    })


@adb_bp.route('/command', methods=['POST'])
def execute_command():
    """执行自定义 adb 命令"""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"success": False, "error": "Missing command"}), 400
    
    cmd = data['command']
    if isinstance(cmd, str):
        cmd = cmd.split()
    
    stdout, stderr, code = run_adb_command(cmd)
    return jsonify({
        "success": code == 0,
        "returncode": code,
        "stdout": stdout,
        "stderr": stderr
    })


@adb_bp.route('/screenshot', methods=['GET'])
def screenshot():
    """截取屏幕并返回图片"""
    # 截图到手机上
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    phone_path = f"/sdcard/screenshot_{timestamp}.png"
    local_path = f"/tmp/adb_screenshot_{timestamp}.png"
    
    # 截图
    out1, err1, code1 = run_adb_command(["shell", "screencap", "-p", phone_path])
    if code1 != 0:
        return jsonify({"success": False, "error": f"Screenshot failed: {err1}"}), 500
    
    # pull 到本地
    out2, err2, code2 = run_adb_command(["pull", phone_path, local_path])
    if code2 != 0:
        return jsonify({"success": False, "error": f"Pull failed: {err2}"}), 500
    
    # 清理手机
    run_adb_command(["shell", "rm", phone_path])
    
    # 读取并返回图片
    if os.path.exists(local_path):
        with open(local_path, 'rb') as f:
            img_data = f.read()
        os.unlink(local_path)
        return Response(img_data, content_type="image/png")
    else:
        return jsonify({"success": False, "error": "Screenshot file not found"}), 500


@adb_bp.route('/tap', methods=['POST'])
def tap():
    """点击屏幕"""
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    
    if x is None or y is None:
        return jsonify({"success": False, "error": "Missing x or y"}), 400
    
    stdout, stderr, code = run_adb_command(["shell", "input", "tap", str(x), str(y)])
    return jsonify({
        "success": code == 0,
        "stdout": stdout,
        "stderr": stderr
    })


@adb_bp.route('/swipe', methods=['POST'])
def swipe():
    """滑动屏幕"""
    data = request.get_json()
    x1 = data.get('x1')
    y1 = data.get('y1')
    x2 = data.get('x2')
    y2 = data.get('y2')
    duration = data.get('duration', 500)  # 毫秒
    
    if None in [x1, y1, x2, y2]:
        return jsonify({"success": False, "error": "Missing x1/y1/x2/y2"}), 400
    
    stdout, stderr, code = run_adb_command([
        "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)
    ])
    return jsonify({
        "success": code == 0,
        "stdout": stdout,
        "stderr": stderr
    })


@adb_bp.route('/back', methods=['POST'])
def back():
    """返回键"""
    stdout, stderr, code = run_adb_command(["shell", "input", "keyevent", "4"])
    return jsonify({
        "success": code == 0,
        "stdout": stdout,
        "stderr": stderr
    })


@adb_bp.route('/home', methods=['POST'])
def home():
    """主页键"""
    stdout, stderr, code = run_adb_command(["shell", "input", "keyevent", "3"])
    return jsonify({
        "success": code == 0,
        "stdout": stdout,
        "stderr": stderr
    })


@adb_bp.route('/getprop', methods=['GET'])
def getprop():
    """获取设备属性"""
    stdout, stderr, code = run_adb_command(["shell", "getprop"])
    props = {}
    for line in stdout.split('\n'):
        line = line.strip()
        if line.startswith('[') and ']:' in line:
            try:
                key = line.split('[')[1].split(']')[0]
                value = line.split(']:')[1].strip()
                props[key] = value
            except:
                pass
    
    return jsonify({
        "success": code == 0,
        "properties": props,
        "raw": stdout
    })


@adb_bp.route('/install', methods=['POST'])
def install():
    """安装 APK"""
    data = request.get_json()
    local_apk = data.get('path')
    if not local_apk or not os.path.exists(local_apk):
        return jsonify({"success": False, "error": "APK file not found"}), 400
    
    stdout, stderr, code = run_adb_command(["install", "-r", local_apk])
    return jsonify({
        "success": code == 0,
        "stdout": stdout,
        "stderr": stderr
    })


def init_adb_routes():
    """初始化路由回调（留空）"""
    pass
