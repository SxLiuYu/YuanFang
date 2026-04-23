#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync.api_client import OpenClawClient
from commands import sync, chat
from collectors import LocationCollector, HealthCollector, NotificationCollector

def test_all():
    """运行所有测试"""
    print("=" * 60)
    print("OpenClaw CLI 测试")
    print("=" * 60)
    
    client = OpenClawClient("http://localhost:8082")
    
    # 1. 测试API连接
    print("\n1. 测试API连接...")
    result = client.health_check()
    if result.get('success'):
        print("   [OK] 后端服务运行正常")
    else:
        print("   [FAIL] 无法连接到后端服务")
        return
    
    # 2. 测试数据采集器
    print("\n2. 测试数据采集器...")
    
    # 位置采集
    loc_collector = LocationCollector()
    loc_collector.set_place('home')
    loc = loc_collector.get_current_location()
    print(f"   [OK] 位置采集: {loc['place_type']}, ({loc['latitude']:.4f}, {loc['longitude']:.4f})")
    
    # 健康采集
    health_collector = HealthCollector()
    health = health_collector.get_today_health()
    print(f"   [OK] 健康采集: {health['steps']} 步, 睡眠 {health['sleep_hours']} 小时")
    
    # 通知采集
    notif_collector = NotificationCollector()
    payment = notif_collector.simulate_payment_notification(50, "美团外卖")
    print(f"   [OK] 支付识别: {payment['payment_info']['amount']} 元, 商户: {payment['payment_info']['merchant']}")
    
    # 3. 测试同步命令
    print("\n3. 测试同步命令...")
    
    # 同步健康数据
    result = sync.sync_health(client, steps=5000, sleep=7.5)
    print(f"   {'[OK]' if result.get('success') else '[FAIL]'} 健康数据同步: {result.get('success', False)}")
    
    # 同步支付数据
    result = sync.sync_payment(client, amount=50, merchant="美团外卖")
    print(f"   {'[OK]' if result.get('success') else '[FAIL]'} 支付数据同步: {result.get('success', False)}")
    if result.get('success'):
        print(f"       自动分类: {result.get('category')}")
    
    # 同步日程
    result = sync.sync_calendar(client, title="团队会议", date="2025-03-20", time="10:00")
    print(f"   {'[OK]' if result.get('success') else '[FAIL]'} 日程数据同步: {result.get('success', False)}")
    
    # 4. 测试AI对话
    print("\n4. 测试AI对话...")
    result = chat.send_message(client, "你好")
    if result.get('success'):
        print(f"   [OK] AI回复: {result.get('text', '')[:50]}...")
    else:
        print(f"   [FAIL] AI对话失败: {result.get('error')}")
    
    # 5. 测试报告
    print("\n5. 测试报告生成...")
    from commands import report
    rpt = report.generate(client, 'daily')
    print(f"   [OK] 报告生成完成")
    print(f"       健康数据: 步数 {rpt.get('health', {}).get('total_steps', 0)}")
    print(f"       财务数据: 支出 {rpt.get('finance', {}).get('total_expense', 0)} 元")
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)

if __name__ == '__main__':
    test_all()