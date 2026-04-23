"""
家庭服务后端 API
支持智能家居、家庭账本、任务板、购物清单
"""

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sqlite3
from datetime import datetime, timedelta
import requests
import sys
import os

logger = logging.getLogger(__name__)

DB_PATH = 'family_services.db'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xiaohongshu_search_service import XiaoHongShuSearchService
from tavily_search_service import TavilySearchService
from cooking_service import CookingService
from voice_interaction_service import VoiceInteractionService

xhs_service = XiaoHongShuSearchService()
tavily_service = TavilySearchService()
cooking_service = CookingService(DB_PATH)
voice_service = VoiceInteractionService()

app = Flask(__name__)
CORS(app)

# ========== 数据库初始化 ==========

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 智能家居设备表
    c.execute('''
        CREATE TABLE IF NOT EXISTS smart_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE,
            device_name TEXT,
            device_type TEXT,
            platform TEXT,
            room TEXT,
            is_online BOOLEAN,
            last_seen TIMESTAMP
        )
    ''')
    
    # 场景表
    c.execute('''
        CREATE TABLE IF NOT EXISTS smart_scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scene_name TEXT,
            scene_type TEXT,
            triggers TEXT,
            actions TEXT,
            is_enabled BOOLEAN
        )
    ''')
    
    # 家庭账本表
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            type TEXT,
            category TEXT,
            subcategory TEXT,
            note TEXT,
            recorded_by TEXT,
            recorded_at TIMESTAMP
        )
    ''')
    
    # 预算表
    c.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            amount REAL,
            period TEXT,
            start_date DATE,
            end_date DATE
        )
    ''')
    
    # 任务表
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            task_description TEXT,
            assigned_to TEXT,
            points INTEGER,
            due_date TIMESTAMP,
            repeat_rule TEXT,
            status TEXT,
            created_by TEXT
        )
    ''')
    
    # 积分表
    c.execute('''
        CREATE TABLE IF NOT EXISTS points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_name TEXT,
            points INTEGER,
            reason TEXT,
            recorded_at TIMESTAMP
        )
    ''')
    
    # 菜谱表
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id TEXT UNIQUE,
            title TEXT,
            source TEXT,
            author TEXT,
            ingredients TEXT,
            steps TEXT,
            cook_time INTEGER,
            difficulty TEXT,
            tags TEXT,
            cover_image TEXT,
            xsec_token TEXT,
            favorited BOOLEAN DEFAULT 0,
            created_at TIMESTAMP
        )
    ''')
    
    # 计时器表
    c.execute('''
        CREATE TABLE IF NOT EXISTS timers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timer_name TEXT,
            duration_seconds INTEGER,
            remaining_seconds INTEGER,
            status TEXT,
            recipe_id TEXT,
            step_number INTEGER,
            created_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    # 食材清单表
    c.execute('''
        CREATE TABLE IF NOT EXISTS shopping_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            quantity TEXT,
            unit TEXT,
            category TEXT,
            recipe_id TEXT,
            purchased BOOLEAN DEFAULT 0,
            note TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    # 购物清单项
    c.execute('''
        CREATE TABLE IF NOT EXISTS shopping_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            category TEXT,
            quantity INTEGER,
            unit TEXT,
            estimated_price REAL,
            is_purchased BOOLEAN,
            purchased_at TIMESTAMP,
            added_by TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# ========== 智能家居 API ==========

@app.route('/api/smarthome/devices', methods=['GET'])
def get_devices():
    """获取所有设备"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM smart_devices')
    devices = [dict(zip(['id', 'device_id', 'device_name', 'device_type', 'platform', 'room', 'is_online', 'last_seen'], row)) 
               for row in c.fetchall()]
    conn.close()
    return jsonify({'devices': devices})

@app.route('/api/smarthome/device', methods=['POST'])
def add_device():
    """添加设备"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO smart_devices (device_id, device_name, device_type, platform, room, is_online, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['device_id'], data['device_name'], data['device_type'], 
              data['platform'], data.get('room', ''), True, datetime.now()))
        conn.commit()
        return jsonify({'success': True, 'message': '设备添加成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/smarthome/control', methods=['POST'])
def control_device():
    """控制设备"""
    data = request.json
    device_id = data.get('device_id')
    action = data.get('action')  # on, off, toggle, set_value
    value = data.get('value')
    
    # 根据平台调用不同 API
    platform = detect_platform(device_id)
    
    if platform == 'tmall':
        # 调用天猫精灵 API
        control_tmall_device(device_id, action, value)
    elif platform == 'mihome':
        # 调用米家 API
        control_mihome_device(device_id, action, value)
    elif platform == 'tuya':
        # 调用涂鸦 API
        control_tuya_device(device_id, action, value)
    
    return jsonify({'success': True, 'message': f'设备 {device_id} 已{action}'})

def detect_platform(device_id):
    """根据设备 ID 判断平台"""
    if device_id.startswith('TM_'):
        return 'tmall'
    elif device_id.startswith('MI_'):
        return 'mihome'
    elif device_id.startswith('TY_'):
        return 'tuya'
    return 'unknown'

def control_tmall_device(device_id, action, value):
    """控制天猫精灵设备"""
    import hashlib
    import time
    
    # 天猫精灵 API 配置
    TMALL_API_KEY = 'YOUR_APP_KEY'
    TMALL_API_SECRET = 'YOUR_APP_SECRET'
    TMALL_API_URL = 'https://openapi.tmall.com/router/rest'
    
    # 构建请求参数
    params = {
        'method': 'tmall.genie.ieq.device.control',
        'app_key': TMALL_API_KEY,
        'device_id': device_id.replace('TM_', ''),
        'action': action,
        'timestamp': str(int(time.time())),
        'v': '2.0',
        'format': 'json'
    }
    
    if value is not None:
        params['value'] = str(value)
    
    # 生成签名
    sign_str = ''.join([k + params[k] for k in sorted(params.keys())]) + TMALL_API_SECRET
    params['sign'] = hashlib.md5(sign_str.encode()).hexdigest().upper()
    
    # 发送请求（简化示例）
    # response = requests.post(TMALL_API_URL, data=params)
    # return response.json()
    
    logger.info(f"[天猫精灵] 控制设备 {device_id}: {action}")

def control_mihome_device(device_id, action, value):
    """控制米家设备"""
    # 米家 API 实现
    logger.info(f"[米家] 控制设备 {device_id}: {action}")

def control_tuya_device(device_id, action, value):
    """控制涂鸦设备"""
    # 涂鸦 API 实现
    logger.info(f"[涂鸦] 控制设备 {device_id}: {action}")

@app.route('/api/smarthome/scene', methods=['POST'])
def execute_scene():
    """执行场景"""
    data = request.json
    scene_id = data.get('scene_id')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT actions FROM smart_scenes WHERE id = ?', (scene_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        actions = json.loads(row[0])
        # 执行场景动作
        for action in actions:
            # 调用设备控制 API
            pass
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': '场景不存在'}), 404

# ========== 家庭账本 API ==========

@app.route('/api/finance/transaction', methods=['POST'])
def add_transaction():
    """添加交易记录"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO transactions (amount, type, category, subcategory, note, recorded_by, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['amount'], data['type'], data['category'], 
          data.get('subcategory', ''), data.get('note', ''), 
          data.get('recorded_by', 'user'), datetime.now()))
    
    conn.commit()
    conn.close()
    
    # 检查预算
    if data['type'] == 'expense':
        check_budget(data['category'], data['amount'])
    
    return jsonify({'success': True})

@app.route('/api/finance/stats', methods=['GET'])
def get_finance_stats():
    """获取统计报表"""
    period = request.args.get('period', 'monthly')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 按分类统计
    c.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE type = 'expense'
        AND recorded_at >= date('now', '-1 month')
        GROUP BY category
    ''')
    
    stats = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    
    return jsonify({'stats': stats, 'period': period})

@app.route('/api/finance/budget', methods=['POST'])
def set_budget():
    """设置预算"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO budgets (category, amount, period, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['category'], data['amount'], data['period'],
          data.get('start_date', datetime.now().date()),
          data.get('end_date')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

def check_budget(category, amount):
    """检查预算"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT amount FROM budgets
        WHERE category = ? AND period = 'monthly'
    ''', (category,))
    
    row = c.fetchone()
    if row:
        budget = row[0]
        
        # 计算本月已花费
        c.execute('''
            SELECT SUM(amount) FROM transactions
            WHERE category = ? AND type = 'expense'
            AND recorded_at >= date('now', 'start of month')
        ''', (category,))
        
        spent = c.fetchone()[0] or 0
        
        if spent >= budget * 0.8:
            # 发送预算预警（调用飞书 Webhook）
            send_budget_warning(category, budget, spent)
    
    conn.close()

def send_budget_warning(category, budget, spent):
    """发送预算预警"""
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/8c164cc1-e173-4011-a53c-75153147de7d"
    
    message = {
        "msg_type": "text",
        "content": {
            "text": f"💰 预算预警\n{category} 本月已花费 {spent:.2f} 元，预算 {budget:.2f} 元\n已超过 80%，请注意控制支出！"
        }
    }
    
    requests.post(webhook_url, json=message)

# ========== 家庭任务 API ==========

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    status = request.args.get('status', 'pending')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE status = ?', (status,))
    
    tasks = [dict(zip(['id', 'task_name', 'task_description', 'assigned_to', 'points', 
                       'due_date', 'repeat_rule', 'status', 'created_by'], row)) 
             for row in c.fetchall()]
    
    conn.close()
    return jsonify({'tasks': tasks})

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建任务"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO tasks (task_name, task_description, assigned_to, points, 
                          due_date, repeat_rule, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    ''', (data['task_name'], data.get('description', ''), data['assigned_to'],
          data.get('points', 10), data.get('due_date'), 
          data.get('repeat_rule', ''), data.get('created_by', 'user')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """完成任务"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取任务信息
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    
    if task:
        # 更新任务状态
        c.execute('UPDATE tasks SET status = ? WHERE id = ?', ('completed', task_id))
        
        # 添加积分
        c.execute('''
            INSERT INTO points_log (member_name, points, reason, recorded_at)
            VALUES (?, ?, ?, ?)
        ''', (task[3], task[4], f'完成任务：{task[1]}', datetime.now()))
        
        conn.commit()
        
        # 如果是重复任务，创建下一个
        if task[6]:  # repeat_rule
            create_recurring_task(task)
    
    conn.close()
    return jsonify({'success': True})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """获取积分排行榜"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT member_name, SUM(points) as total_points
        FROM points_log
        GROUP BY member_name
        ORDER BY total_points DESC
    ''')
    
    leaderboard = [{'name': row[0], 'points': row[1]} for row in c.fetchall()]
    conn.close()
    
    return jsonify({'leaderboard': leaderboard})

# ========== 购物清单 API ==========

@app.route('/api/shopping/list', methods=['GET'])
def get_shopping_list():
    """获取购物清单"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM shopping_items WHERE is_purchased = ?', (False,))
    
    items = [dict(zip(['id', 'item_name', 'category', 'quantity', 'unit', 
                       'estimated_price', 'is_purchased', 'purchased_at', 'added_by'], row)) 
             for row in c.fetchall()]
    
    conn.close()
    return jsonify({'items': items})

@app.route('/api/shopping/item', methods=['POST'])
def add_shopping_item():
    """添加购物项"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO shopping_items (item_name, category, quantity, unit, 
                                   estimated_price, is_purchased, added_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['item_name'], data.get('category', '其他'), data.get('quantity', 1),
          data.get('unit', '个'), data.get('estimated_price', 0), False, 
          data.get('added_by', 'user')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/shopping/item/<int:item_id>/purchase', methods=['POST'])
def purchase_item(item_id):
    """标记为已购买"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        UPDATE shopping_items 
        SET is_purchased = ?, purchased_at = ?
        WHERE id = ?
    ''', (True, datetime.now(), item_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/shopping/compare', methods=['GET'])
def compare_prices():
    """价格对比"""
    item_name = request.args.get('item_name')
    
    # 调用电商平台 API 获取价格（简化实现）
    prices = {
        '京东': 100,
        '淘宝': 95,
        '拼多多': 88,
        '盒马': 105
    }
    
    return jsonify({'prices': prices, 'item': item_name})

# ========== 能源管理 API ==========

energy_service = EnergyManagementService()
chart_service = EnergyChartService()
ai_predictor = AIEnergyPredictor()

@app.route('/api/energy/chart/daily-trend', methods=['GET'])
def get_daily_trend_chart():
    """获取每日用电趋势图表数据"""
    date = request.args.get('date')
    data = chart_service.get_daily_trend_data(date)
    return jsonify(data)

@app.route('/api/energy/chart/weekly-trend', methods=['GET'])
def get_weekly_trend_chart():
    """获取每周用电趋势图表数据"""
    end_date = request.args.get('end_date')
    data = chart_service.get_weekly_trend_data(end_date)
    return jsonify(data)

@app.route('/api/energy/chart/monthly-trend', methods=['GET'])
def get_monthly_trend_chart():
    """获取月度用电趋势图表数据"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    data = chart_service.get_monthly_trend_data(year, month)
    return jsonify(data)

@app.route('/api/energy/chart/device-distribution', methods=['GET'])
def get_device_distribution_chart():
    """获取设备用电占比图表数据"""
    date = request.args.get('date')
    data = chart_service.get_device_distribution_data(date)
    return jsonify(data)

@app.route('/api/energy/chart/cost-comparison', methods=['GET'])
def get_cost_comparison_chart():
    """获取电费对比图表数据"""
    months = request.args.get('months', 6, type=int)
    data = chart_service.get_cost_comparison_data(months)
    return jsonify(data)

@app.route('/api/energy/chart/goal-progress', methods=['GET'])
def get_goal_progress_chart():
    """获取节能目标进度图表数据"""
    goal_id = request.args.get('goal_id', type=int)
    data = chart_service.get_saving_goal_progress_data(goal_id)
    return jsonify(data)

@app.route('/api/energy/record', methods=['POST'])
def record_energy():
    """记录设备用电"""
    data = request.json
    
    result = energy_service.record_energy_usage(
        device_id=data.get('device_id'),
        device_name=data.get('device_name'),
        power_watts=float(data.get('power_watts', 100)),
        usage_hours=float(data.get('usage_hours', 1)),
        room=data.get('room'),
        notes=data.get('notes')
    )
    
    return jsonify(result)

@app.route('/api/energy/daily', methods=['GET'])
def get_daily_energy():
    """获取每日用电报告"""
    date = request.args.get('date')
    report = energy_service.get_daily_report(date)
    return jsonify(report)

@app.route('/api/energy/monthly', methods=['GET'])
def get_monthly_energy():
    """获取月度用电报告"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    report = energy_service.get_monthly_report(year, month)
    return jsonify(report)

@app.route('/api/energy/suggestions', methods=['GET'])
def get_energy_suggestions():
    """获取节能建议"""
    suggestions = energy_service.get_energy_saving_suggestions()
    return jsonify({'suggestions': suggestions})

@app.route('/api/energy/goal', methods=['POST'])
def set_energy_goal():
    """设置节能目标"""
    data = request.json
    result = energy_service.set_saving_goal(
        goal_name=data.get('goal_name', '节能目标'),
        target_kwh=float(data.get('target_kwh')),
        period=data.get('period', 'monthly')
    )
    return jsonify(result)

@app.route('/api/energy/goal', methods=['GET'])
def get_energy_goal():
    """获取节能目标进度"""
    goal_id = request.args.get('goal_id', type=int)
    progress = energy_service.get_goal_progress(goal_id)
    return jsonify(progress)

# ========== AI 用电预测 API ==========

@app.route('/api/energy/ai/train', methods=['POST'])
def train_prediction_model():
    """训练 AI 预测模型"""
    data = request.json or {}
    days = data.get('days', 30)
    result = ai_predictor.train_model(days)
    return jsonify(result)

@app.route('/api/energy/ai/predict-daily', methods=['GET'])
def predict_daily_usage():
    """预测未来每日用电"""
    days = request.args.get('days', 7, type=int)
    result = ai_predictor.predict_daily_usage(days)
    return jsonify(result)

@app.route('/api/energy/ai/predict-monthly', methods=['GET'])
def predict_monthly_bill():
    """预测月度电费"""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    result = ai_predictor.predict_monthly_bill(month, year)
    return jsonify(result)

@app.route('/api/energy/ai/anomalies', methods=['GET'])
def detect_anomalies():
    """检测异常用电"""
    days = request.args.get('days', 7, type=int)
    result = ai_predictor.detect_anomalies(days)
    return jsonify(result)

@app.route('/api/energy/ai/suggestions', methods=['GET'])
def get_ai_suggestions():
    """获取 AI 智能节能建议"""
    result = ai_predictor.get_smart_suggestions()
    return jsonify(result)

# ========== 小红书搜索 API ==========

@app.route('/api/xiaohongshu/search', methods=['GET'])
def search_xiaohongshu():
    """
    搜索小红书内容
    
    参数:
        keyword: 搜索关键词（必填）
        limit: 返回结果数量（可选，默认 10）
    
    返回:
        {
            'success': bool,
            'keyword': str,
            'count': int,
            'results': [
                {
                    'id': str,
                    'title': str,
                    'author': {'user_id': str, 'nickname': str, 'avatar': str},
                    'cover_image': str,
                    'stats': {'likes': str, 'collects': str, 'comments': str, 'shares': str},
                    'url': str
                }
            ],
            'error': str (if failed)
        }
    """
    keyword = request.args.get('keyword')
    limit = request.args.get('limit', 10, type=int)
    
    if not keyword:
        return jsonify({
            'success': False,
            'error': '缺少搜索关键词（keyword 参数）'
        }), 400
    
    result = xhs_service.search(keyword, limit=limit)
    return jsonify(result)

@app.route('/api/xiaohongshu/detail', methods=['GET'])
def get_xiaohongshu_detail():
    """
    获取小红书笔记详情
    
    参数:
        feed_id: 笔记 ID（必填）
        xsec_token: 访问令牌（必填）
        load_comments: 是否加载评论（可选，默认 false）
    
    返回:
        笔记详情数据
    """
    feed_id = request.args.get('feed_id')
    xsec_token = request.args.get('xsec_token')
    load_comments = request.args.get('load_comments', 'false').lower() == 'true'
    
    if not feed_id or not xsec_token:
        return jsonify({
            'success': False,
            'error': '缺少必要参数（feed_id 和 xsec_token）'
        }), 400
    
    result = xhs_service.get_feed_detail(feed_id, xsec_token, load_comments=load_comments)
    return jsonify(result)

@app.route('/api/xiaohongshu/status', methods=['GET'])
def check_xiaohongshu_status():
    """
    检查小红书登录状态
    
    返回:
        {
            'logged_in': bool,
            'message': str
        }
    """
    result = xhs_service.check_login_status()
    return jsonify(result)

# ========== Tavily 网络搜索 API ==========

@app.route('/api/search', methods=['GET'])
def tavily_search():
    """
    Tavily 网络搜索（默认搜索服务）
    
    参数:
        q: 搜索关键词（必填）
        max_results: 返回结果数量（可选，默认 5）
        search_depth: 搜索深度 "basic" 或 "advanced"（可选，默认 basic）
        include_answer: 是否包含 AI 答案（可选，默认 true）
    
    返回:
        {
            'success': bool,
            'answer': str,  # AI 生成的答案
            'results': [
                {
                    'title': str,
                    'url': str,
                    'content': str,
                    'score': float
                }
            ]
        }
    """
    query = request.args.get('q') or request.args.get('query')
    max_results = int(request.args.get('max_results', 5))
    search_depth = request.args.get('search_depth', 'basic')
    include_answer = request.args.get('include_answer', 'true').lower() == 'true'
    
    if not query:
        return jsonify({
            'success': False,
            'error': '缺少搜索关键词（参数 q 或 query）'
        }), 400
    
    result = tavily_service.search(
        query=query,
        search_depth=search_depth,
        include_answer=include_answer,
        max_results=max_results
    )
    
    return jsonify(result)

@app.route('/api/search/quick', methods=['GET'])
def tavily_quick_search():
    """
    快速搜索 - 仅返回 AI 生成的答案
    
    参数:
        q: 搜索关键词（必填）
    
    返回:
        { 'answer': str }
    """
    query = request.args.get('q') or request.args.get('query')
    
    if not query:
        return jsonify({
            'answer': '',
            'error': '缺少搜索关键词'
        }), 400
    
    answer = tavily_service.search_quick(query)
    return jsonify({'answer': answer})

@app.route('/api/search/context', methods=['GET'])
def tavily_context_search():
    """
    搜索并返回格式化上下文（用于 AI 对话）
    
    参数:
        q: 搜索关键词（必填）
        max_results: 返回结果数量（可选，默认 5）
    
    返回:
        { 'context': str }
    """
    query = request.args.get('q') or request.args.get('query')
    max_results = int(request.args.get('max_results', 5))
    
    if not query:
        return jsonify({
            'context': '',
            'error': '缺少搜索关键词'
        }), 400
    
    context = tavily_service.search_with_context(query, max_results)
    return jsonify({'context': context})

# ========== 做菜功能 API ==========

@app.route('/api/cooking/search', methods=['GET'])
def search_cooking_recipes():
    """
    搜索菜谱
    
    参数:
        keyword: 搜索关键词（如：红烧肉、西红柿炒蛋）
        limit: 返回数量（可选，默认 10）
    
    返回:
        菜谱搜索结果
    """
    keyword = request.args.get('keyword')
    limit = request.args.get('limit', 10, type=int)
    
    if not keyword:
        return jsonify({'success': False, 'error': '缺少搜索关键词'}), 400
    
    result = cooking_service.search_recipes(keyword, limit=limit)
    return jsonify(result)

@app.route('/api/cooking/recipe/detail', methods=['GET'])
def get_recipe_detail():
    """
    获取菜谱详情（从小红书）
    
    参数:
        feed_id: 笔记 ID
        xsec_token: 访问令牌
    
    返回:
        菜谱详细信息
    """
    feed_id = request.args.get('feed_id')
    xsec_token = request.args.get('xsec_token')
    
    if not feed_id or not xsec_token:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400
    
    result = cooking_service.get_recipe_detail(feed_id, xsec_token)
    return jsonify(result)

@app.route('/api/cooking/recipe/save', methods=['POST'])
def save_recipe():
    """
    保存菜谱到本地
    
    请求体:
        title: 菜名
        ingredients: 食材列表
        steps: 步骤列表
        cook_time: 烹饪时间（分钟，可选）
        difficulty: 难度（easy/medium/hard，可选）
        source: 来源（可选）
        author: 作者（可选）
        cover_image: 封面图（可选）
        recipe_id: 来源 ID（可选）
        xsec_token: 访问令牌（可选）
    
    返回:
        {'success': bool, 'recipe_id': str}
    """
    data = request.json
    
    result = cooking_service.save_recipe(
        title=data.get('title'),
        ingredients=data.get('ingredients', []),
        steps=data.get('steps', []),
        cook_time=data.get('cook_time', 0),
        difficulty=data.get('difficulty', 'medium'),
        source=data.get('source', 'xiaohongshu'),
        author=data.get('author', ''),
        cover_image=data.get('cover_image', ''),
        recipe_id=data.get('recipe_id'),
        xsec_token=data.get('xsec_token', '')
    )
    
    return jsonify(result)

@app.route('/api/cooking/recipes', methods=['GET'])
def get_saved_recipes():
    """
    获取已保存的菜谱
    
    参数:
        limit: 返回数量（可选，默认 20）
    
    返回:
        菜谱列表
    """
    limit = request.args.get('limit', 20, type=int)
    recipes = cooking_service.get_saved_recipes(limit=limit)
    return jsonify({'recipes': recipes})

@app.route('/api/cooking/recipe/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """
    获取单个菜谱详情
    
    返回:
        菜谱详细信息
    """
    recipe = cooking_service.get_recipe(recipe_id)
    if recipe:
        return jsonify({'success': True, 'recipe': recipe})
    return jsonify({'success': False, 'error': '菜谱不存在'}), 404

@app.route('/api/cooking/recipe/<recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """删除菜谱"""
    result = cooking_service.delete_recipe(recipe_id)
    return jsonify(result)

@app.route('/api/cooking/recipe/<recipe_id>/voice', methods=['GET'])
def get_voice_instructions(recipe_id):
    """
    获取语音指导
    
    返回:
        分步语音指导文本
    """
    result = cooking_service.get_voice_instructions(recipe_id)
    return jsonify(result)

# ========== 计时器 API ==========

@app.route('/api/cooking/timer', methods=['POST'])
def create_timer():
    """
    创建计时器
    
    请求体:
        timer_name: 计时器名称（如：煮鸡蛋）
        duration_seconds: 时长（秒）
        recipe_id: 关联菜谱 ID（可选）
        step_number: 关联步骤编号（可选）
    
    返回:
        {'success': bool, 'timer_id': int}
    """
    data = request.json
    
    result = cooking_service.create_timer(
        timer_name=data.get('timer_name'),
        duration_seconds=int(data.get('duration_seconds', 60)),
        recipe_id=data.get('recipe_id'),
        step_number=data.get('step_number')
    )
    
    return jsonify(result)

@app.route('/api/cooking/timers', methods=['GET'])
def get_timers():
    """
    获取计时器列表
    
    参数:
        status: 状态（running/stopped/completed/all，默认 running）
    
    返回:
        计时器列表
    """
    status = request.args.get('status', 'running')
    timers = cooking_service.get_timers(status=status)
    return jsonify({'timers': timers})

@app.route('/api/cooking/timer/<int:timer_id>/stop', methods=['POST'])
def stop_timer(timer_id):
    """停止计时器"""
    result = cooking_service.stop_timer(timer_id)
    return jsonify(result)

@app.route('/api/cooking/timer/<int:timer_id>/complete', methods=['POST'])
def complete_timer(timer_id):
    """完成计时器"""
    result = cooking_service.complete_timer(timer_id)
    return jsonify(result)

# ========== 采购清单 API ==========

@app.route('/api/cooking/shopping-list', methods=['GET'])
def get_shopping_list():
    """
    获取采购清单
    
    参数:
        purchased: 是否只显示已采购的（true/false，默认 false）
    
    返回:
        采购清单列表
    """
    purchased = request.args.get('purchased', 'false').lower() == 'true'
    items = cooking_service.get_shopping_list(purchased=purchased)
    return jsonify({'items': items})

@app.route('/api/cooking/shopping-list', methods=['POST'])
def add_to_shopping_list():
    """
    添加食材到采购清单
    
    请求体:
        item_name: 食材名称
        quantity: 数量（可选，默认 1）
        unit: 单位（可选，默认 个）
        category: 分类（可选，默认 其他）
        recipe_id: 关联菜谱 ID（可选）
        note: 备注（可选）
    
    返回:
        {'success': bool, 'item_id': int}
    """
    data = request.json
    
    result = cooking_service.add_to_shopping_list(
        item_name=data.get('item_name'),
        quantity=data.get('quantity', '1'),
        unit=data.get('unit', '个'),
        category=data.get('category', '其他'),
        recipe_id=data.get('recipe_id'),
        note=data.get('note', '')
    )
    
    return jsonify(result)

@app.route('/api/cooking/recipe/<recipe_id>/ingredients', methods=['POST'])
def add_recipe_ingredients(recipe_id):
    """
    将菜谱的食材添加到采购清单
    
    返回:
        {'success': bool, 'added_count': int}
    """
    result = cooking_service.add_recipe_ingredients(recipe_id)
    return jsonify(result)

@app.route('/api/cooking/shopping-list/<int:item_id>/purchase', methods=['POST'])
def mark_purchased(item_id):
    """标记食材已采购"""
    data = request.json or {}
    purchased = data.get('purchased', True)
    result = cooking_service.mark_purchased(item_id, purchased=purchased)
    return jsonify(result)

@app.route('/api/cooking/shopping-list/<int:item_id>', methods=['DELETE'])
def remove_from_shopping_list(item_id):
    """从采购清单删除"""
    result = cooking_service.remove_from_shopping_list(item_id)
    return jsonify(result)

@app.route('/api/cooking/shopping-list/clear', methods=['POST'])
def clear_purchased_items():
    """清空已采购项"""
    result = cooking_service.clear_purchased_items()
    return jsonify(result)

# ========== 语音交互 API ==========

# 全局会话存储（生产环境应使用 Redis）
cooking_sessions = {}

@app.route('/api/voice/tts', methods=['POST'])
def text_to_speech():
    """
    文本转语音
    
    请求体:
        text: 要转换的文本
        voice: 语音音色（可选，默认中文女声）
        rate: 语速（可选，如：+20%, -10%）
        output_file: 输出文件路径（可选）
    
    返回:
        {'success': bool, 'audio_path': str, 'duration': float}
    """
    data = request.json
    
    result = voice_service.text_to_speech(
        text=data.get('text'),
        output_file=data.get('output_file'),
        voice=data.get('voice'),
        rate=data.get('rate', '+0%')
    )
    
    return jsonify(result)

@app.route('/api/voice/recognize', methods=['POST'])
def recognize_command():
    """
    识别语音指令
    
    请求体:
        text: 语音识别后的文本
    
    返回:
        {
            'recognized': bool,
            'command': str,
            'params': dict,
            'confidence': float
        }
    """
    data = request.json
    text = data.get('text', '')
    
    result = voice_service.recognize_command(text)
    return jsonify(result)

@app.route('/api/voice/cooking/start', methods=['POST'])
def start_cooking_session():
    """
    开始做菜语音会话
    
    请求体:
        recipe_id: 菜谱 ID
    
    返回:
        {
            'success': bool,
            'session_id': str,
            'intro_audio': str (介绍语音路径)
        }
    """
    data = request.json
    recipe_id = data.get('recipe_id')
    
    if not recipe_id:
        return jsonify({'success': False, 'error': '缺少 recipe_id'}), 400
    
    # 获取菜谱
    recipe = cooking_service.get_recipe(recipe_id)
    if not recipe:
        return jsonify({'success': False, 'error': '菜谱不存在'}), 404
    
    # 创建会话
    session = voice_service.create_cooking_session(recipe)
    cooking_sessions[session['session_id']] = session
    
    # 生成介绍语音
    intro = voice_service.generate_cooking_intro(
        recipe['title'],
        recipe.get('cook_time', 0),
        recipe.get('difficulty', 'medium')
    )
    
    return jsonify({
        'success': True,
        'session_id': session['session_id'],
        'recipe_title': recipe['title'],
        'total_steps': session['total_steps'],
        'intro_audio': intro['audio_path'] if intro['success'] else None
    })

@app.route('/api/voice/cooking/<session_id>/next', methods=['POST'])
def cooking_next_step(session_id):
    """
    下一步语音指导
    
    返回:
        {
            'success': bool,
            'step': int,
            'total': int,
            'text': str,
            'audio_path': str
        }
    """
    session = cooking_sessions.get(session_id)
    if not session:
        return jsonify({'success': False, 'error': '会话不存在'}), 404
    
    result = voice_service.get_next_step_audio(session)
    
    if result['success'] and result.get('audio'):
        return jsonify({
            'success': True,
            'step': result['step'],
            'total': result['total'],
            'text': result['text'],
            'audio_path': result['audio']['audio_path']
        })
    
    return jsonify(result)

@app.route('/api/voice/cooking/<session_id>/command', methods=['POST'])
def cooking_voice_command(session_id):
    """
    处理做菜语音指令
    
    请求体:
        text: 语音识别文本
    
    返回:
        处理结果（可能包含音频路径、动作指令等）
    """
    session = cooking_sessions.get(session_id)
    if not session:
        return jsonify({'success': False, 'error': '会话不存在'}), 404
    
    data = request.json
    voice_text = data.get('text', '')
    
    result = voice_service.handle_voice_command(session, voice_text)
    
    # 处理特殊动作
    if result.get('action') == 'create_timer':
        # 创建计时器
        timer_result = cooking_service.create_timer(
            timer_name=result.get('timer_name', '计时器'),
            duration_seconds=result.get('duration', 300)
        )
        result['timer_id'] = timer_result.get('timer_id')
    
    # 添加音频路径
    if result.get('audio') and result['audio']['success']:
        result['audio_path'] = result['audio']['audio_path']
        del result['audio']
    
    return jsonify(result)

@app.route('/api/voice/cooking/<session_id>/status', methods=['GET'])
def cooking_session_status(session_id):
    """
    获取做菜会话状态
    
    返回:
        {
            'session_id': str,
            'recipe_title': str,
            'current_step': int,
            'total_steps': int,
            'progress': float
        }
    """
    session = cooking_sessions.get(session_id)
    if not session:
        return jsonify({'success': False, 'error': '会话不存在'}), 404
    
    return jsonify({
        'session_id': session_id,
        'recipe_title': session['recipe']['title'],
        'current_step': session['current_step'],
        'total_steps': session['total_steps'],
        'progress': session['current_step'] / session['total_steps'] if session['total_steps'] > 0 else 0
    })

@app.route('/api/voice/cooking/<session_id>/end', methods=['POST'])
def end_cooking_session(session_id):
    """结束做菜会话"""
    if session_id in cooking_sessions:
        del cooking_sessions[session_id]
    
    return jsonify({'success': True})

@app.route('/api/voice/timer-alert', methods=['POST'])
def generate_timer_alert():
    """
    生成计时器提醒语音
    
    请求体:
        timer_name: 计时器名称
    
    返回:
        {'success': bool, 'audio_path': str}
    """
    data = request.json
    timer_name = data.get('timer_name', '计时器')
    
    result = voice_service.generate_timer_alert(timer_name)
    return jsonify(result)

# ========== 工具函数 ==========

def create_recurring_task(task):
    """创建重复任务"""
    repeat_rule = task[6]
    
    # 计算下次到期时间
    if 'daily' in repeat_rule:
        due_date = datetime.now() + timedelta(days=1)
    elif 'weekly' in repeat_rule:
        due_date = datetime.now() + timedelta(weeks=1)
    else:
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO tasks (task_name, task_description, assigned_to, points, 
                          due_date, repeat_rule, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    ''', (task[1], task[2], task[3], task[4], due_date, repeat_rule, task[8]))
    
    conn.commit()
    conn.close()

# ========== 主程序 ==========

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8082, debug=True)
