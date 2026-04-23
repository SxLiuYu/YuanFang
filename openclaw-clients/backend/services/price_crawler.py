import logging
logger = logging.getLogger(__name__)
"""
电商价格爬取服务
支持京东、淘宝、拼多多、盒马等平台价格对比
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, List, Optional
import time

class PriceCrawler:
    """电商价格爬取服务"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 平台 API 端点（简化实现，实际需使用官方 API）
        self.platforms = {
            'jd': 'https://item.jd.com',
            'tb': 'https://item.taobao.com',
            'pdd': 'https://mobile.yangkeduo.com',
            'hema': 'https://www.freshhema.com'
        }
    
    def search_price(self, product_name: str, platforms: List[str] = None) -> Dict[str, Dict]:
        """搜索商品价格"""
        if platforms is None:
            platforms = ['jd', 'tb', 'pdd', 'hema']
        
        prices = {}
        
        for platform in platforms:
            try:
                if platform == 'jd':
                    price_data = self._crawl_jd_price(product_name)
                elif platform == 'tb':
                    price_data = self._crawl_tb_price(product_name)
                elif platform == 'pdd':
                    price_data = self._crawl_pdd_price(product_name)
                elif platform == 'hema':
                    price_data = self._crawl_hema_price(product_name)
                else:
                    continue
                
                if price_data:
                    prices[platform] = price_data
            except Exception as e:
                logger.error(f"{platform} 价格爬取失败：{e}")
        
        return prices
    
    def _crawl_jd_price(self, product_name: str) -> Optional[Dict]:
        """爬取京东价格"""
        try:
            # 使用京东 API（简化实现）
            # 实际应使用京东联盟 API
            search_url = f"https://search.jd.com/Search?keyword={product_name}"
            
            response = requests.get(search_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找第一个商品价格
                price_elem = soup.find('div', class_='p-price')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    
                    return {
                        'platform': 'jd',
                        'platform_name': '京东',
                        'price': price,
                        'url': search_url,
                        'timestamp': time.time()
                    }
        except Exception as e:
            logger.error(f"京东价格爬取失败：{e}")
        
        return None
    
    def _crawl_tb_price(self, product_name: str) -> Optional[Dict]:
        """爬取淘宝价格"""
        try:
            # 使用淘宝 API（简化实现）
            # 实际应使用淘宝联盟 API
            search_url = f"https://s.taobao.com/search?q={product_name}"
            
            response = requests.get(search_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                # 淘宝页面需要 JavaScript 渲染，简化处理
                # 实际应使用 Selenium 或官方 API
                return {
                    'platform': 'tb',
                    'platform_name': '淘宝',
                    'price': 0,  # 需要 JavaScript 渲染
                    'url': search_url,
                    'timestamp': time.time(),
                    'note': '需要 JavaScript 渲染'
                }
        except Exception as e:
            logger.error(f"淘宝价格爬取失败：{e}")
        
        return None
    
    def _crawl_pdd_price(self, product_name: str) -> Optional[Dict]:
        """爬取拼多多价格"""
        try:
            # 拼多多移动端页面
            search_url = f"https://mobile.yangkeduo.com/search_result.html?search_key={product_name}"
            
            response = requests.get(search_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                # 简化实现
                return {
                    'platform': 'pdd',
                    'platform_name': '拼多多',
                    'price': 0,
                    'url': search_url,
                    'timestamp': time.time(),
                    'note': '需要进一步优化'
                }
        except Exception as e:
            logger.error(f"拼多多价格爬取失败：{e}")
        
        return None
    
    def _crawl_hema_price(self, product_name: str) -> Optional[Dict]:
        """爬取盒马价格"""
        try:
            search_url = f"https://www.freshhema.com/search?keywords={product_name}"
            
            response = requests.get(search_url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找价格
                price_elem = soup.find('span', class_='money')
                if price_elem:
                    price = self._extract_price(price_elem.get_text(strip=True))
                    
                    return {
                        'platform': 'hema',
                        'platform_name': '盒马',
                        'price': price,
                        'url': search_url,
                        'timestamp': time.time()
                    }
        except Exception as e:
            logger.error(f"盒马价格爬取失败：{e}")
        
        return None
    
    def _extract_price(self, text: str) -> float:
        """从文本中提取价格"""
        # 匹配价格模式：¥99.99 或 99.99 元
        patterns = [
            r'¥\s*([\d.]+)',
            r'([\d.]+)\s*元',
            r'([\d.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        return 0.0
    
    def compare_prices(self, prices: Dict[str, Dict]) -> Dict:
        """对比价格"""
        if not prices:
            return {'error': '无价格数据'}
        
        # 找出最低价
        min_price = float('inf')
        min_platform = ''
        
        for platform, data in prices.items():
            if data.get('price', 0) > 0 and data['price'] < min_price:
                min_price = data['price']
                min_platform = platform
        
        # 计算价差
        max_price = 0
        for platform, data in prices.items():
            if data.get('price', 0) > max_price:
                max_price = data['price']
        
        price_diff = max_price - min_price if min_price > 0 else 0
        
        return {
            'min_price': min_price,
            'min_platform': prices.get(min_platform, {}).get('platform_name', ''),
            'max_price': max_price,
            'price_diff': price_diff,
            'savings': f'最多省¥{price_diff:.2f}',
            'platforms_count': len(prices)
        }
    
    def get_price_history(self, product_id: str, platform: str, days: int = 30) -> List[Dict]:
        """获取价格历史（简化实现）"""
        # 实际应从数据库查询历史价格
        history = []
        
        for i in range(days):
            history.append({
                'date': f'2026-03-{i+1:02d}',
                'price': 100 + (i % 10) * 5,  # 模拟数据
                'platform': platform
            })
        
        return history
    
    def set_price_alert(self, product_name: str, target_price: float, platforms: List[str] = None):
        """设置降价提醒"""
        # 实际应写入数据库，定时任务检查
        alert = {
            'product_name': product_name,
            'target_price': target_price,
            'platforms': platforms or ['jd', 'tb', 'pdd'],
            'created_at': time.time()
        }
        
        logger.info(f"设置降价提醒：{product_name} 目标价¥{target_price}")
        return alert


# 使用示例
if __name__ == '__main__':
    crawler = PriceCrawler()
    
    # 搜索价格
    prices = crawler.search_price('牛奶')
    
    logger.info("\n价格对比:")
    for platform, data in prices.items():
        logger.info(f"{data['platform_name']}: ¥{data['price']:.2f}")
    
    # 对比价格
    comparison = crawler.compare_prices(prices)
    logger.info(f"\n最低价：{comparison['min_platform']} ¥{comparison['min_price']:.2f}")
    logger.info(f"最多省：¥{comparison['savings']}")
