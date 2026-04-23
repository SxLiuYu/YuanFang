#!/usr/bin/env python3
"""
小红书搜索功能测试脚本
"""

import requests
import json

BASE_URL = 'http://localhost:8082'

def test_search():
    """测试搜索功能"""
    print("=== 测试小红书搜索 ===\n")
    
    # 测试搜索
    print("1. 搜索「美食推荐」...")
    response = requests.get(f'{BASE_URL}/api/xiaohongshu/search', params={
        'keyword': '美食推荐',
        'limit': 3
    })
    
    result = response.json()
    print(f"   状态：{'成功' if result.get('success') else '失败'}")
    print(f"   结果数：{result.get('count', 0)}\n")
    
    if result.get('success'):
        for i, item in enumerate(result['results'], 1):
            print(f"   [{i}] {item['title']}")
            print(f"       作者：{item['author']['nickname']}")
            print(f"       点赞：{item['stats']['likes']} | 收藏：{item['stats']['collects']}")
            print(f"       链接：{item['url']}\n")
    else:
        print(f"   错误：{result.get('error')}\n")
    
    # 测试搜索「家居装修」
    print("2. 搜索「家居装修」...")
    response = requests.get(f'{BASE_URL}/api/xiaohongshu/search', params={
        'keyword': '家居装修',
        'limit': 2
    })
    
    result = response.json()
    print(f"   状态：{'成功' if result.get('success') else '失败'}")
    print(f"   结果数：{result.get('count', 0)}\n")
    
    if result.get('success'):
        for i, item in enumerate(result['results'], 1):
            print(f"   [{i}] {item['title']}")
            print(f"       作者：{item['author']['nickname']}\n")

def test_status():
    """测试登录状态检查"""
    print("=== 检查小红书登录状态 ===\n")
    
    response = requests.get(f'{BASE_URL}/api/xiaohongshu/status')
    result = response.json()
    
    print(f"   登录状态：{'已登录' if result.get('logged_in') else '未登录'}")
    print(f"   详情：{result.get('message', '无')}\n")

def test_detail():
    """测试笔记详情获取"""
    print("=== 测试笔记详情获取 ===\n")
    
    # 先搜索获取一个笔记
    response = requests.get(f'{BASE_URL}/api/xiaohongshu/search', params={
        'keyword': '美食',
        'limit': 1
    })
    
    result = response.json()
    if result.get('success') and result.get('count', 0) > 0:
        feed = result['results'][0]
        feed_id = feed['id']
        xsec_token = feed['xsec_token']
        
        print(f"   测试笔记：{feed['title']}")
        print(f"   ID: {feed_id}\n")
        
        # 获取详情
        print("   获取笔记详情...")
        response = requests.get(f'{BASE_URL}/api/xiaohongshu/detail', params={
            'feed_id': feed_id,
            'xsec_token': xsec_token
        })
        
        detail = response.json()
        if detail.get('success'):
            print(f"   详情获取成功")
            # 可以打印更多详情信息
        else:
            print(f"   详情获取失败：{detail.get('error')}")
    else:
        print("   无法获取测试笔记（搜索失败）")

if __name__ == '__main__':
    try:
        # 测试登录状态
        test_status()
        
        # 测试搜索
        test_search()
        
        # 测试详情获取
        test_detail()
        
        print("\n✅ 测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到家庭助手 API（http://localhost:8082）")
        print("   请先启动服务：python3 family_services_api.py")
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
