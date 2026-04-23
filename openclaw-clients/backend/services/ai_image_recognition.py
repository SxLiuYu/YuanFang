import logging
logger = logging.getLogger(__name__)
"""
AI 图像识别服务
支持拍照记账、发票识别、商品识别等
"""

import requests
import base64
import json
from typing import Dict, List, Optional
import time

class AIImageRecognition:
    """AI 图像识别服务"""
    
    def __init__(self):
        # 通义千问视觉 API
        self.dashscope_api_key = ""
        self.vision_api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    def set_api_key(self, api_key: str):
        """设置 API Key"""
        self.dashscope_api_key = api_key
    
    # ========== 拍照记账 ==========
    
    def recognize_receipt(self, image_path: str) -> Optional[Dict]:
        """识别发票/收据"""
        try:
            # 读取图片并转为 Base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 调用视觉 API
            result = self._call_vision_api(
                image_data,
                "请识别这张发票/收据，提取以下信息：\n1. 总金额\n2. 商家名称\n3. 消费日期\n4. 商品明细\n请以 JSON 格式返回"
            )
            
            if result:
                # 解析结果
                return self._parse_receipt_result(result)
        
        except Exception as e:
            logger.error(f"发票识别失败：{e}")
        
        return None
    
    def recognize_product(self, image_path: str) -> Optional[Dict]:
        """识别商品"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            result = self._call_vision_api(
                image_data,
                "请识别这个商品，告诉我：\n1. 商品名称\n2. 品牌\n3. 类别\n4. 可能的价格范围\n请以 JSON 格式返回"
            )
            
            if result:
                return self._parse_product_result(result)
        
        except Exception as e:
            logger.error(f"商品识别失败：{e}")
        
        return None
    
    def recognize_text(self, image_path: str) -> Optional[str]:
        """OCR 文字识别"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            result = self._call_vision_api(
                image_data,
                "请识别图片中的所有文字内容"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"文字识别失败：{e}")
        
        return None
    
    # ========== 场景识别 ==========
    
    def recognize_scene(self, image_path: str) -> Optional[Dict]:
        """识别场景"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            result = self._call_vision_api(
                image_data,
                "请描述这个场景，包括：\n1. 场景类型（室内/室外/餐厅/商场等）\n2. 主要物体\n3. 可能的活动\n请以 JSON 格式返回"
            )
            
            if result:
                return {
                    'description': result,
                    'tags': self._extract_tags(result)
                }
        
        except Exception as e:
            logger.error(f"场景识别失败：{e}")
        
        return None
    
    # ========== 智能分析 ==========
    
    def analyze_shopping_cart(self, image_path: str) -> Optional[Dict]:
        """分析购物车商品"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            result = self._call_vision_api(
                image_data,
                "请分析购物车中的所有商品，列出：\n1. 每个商品的名称\n2. 估计数量\n3. 估计单价\n4. 估计总价\n请以 JSON 格式返回"
            )
            
            if result:
                return self._parse_cart_result(result)
        
        except Exception as e:
            logger.error(f"购物车分析失败：{e}")
        
        return None
    
    def analyze_refrigerator(self, image_path: str) -> Optional[Dict]:
        """分析冰箱食材"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            result = self._call_vision_api(
                image_data,
                "请识别冰箱里的食材，列出：\n1. 每种食材的名称\n2. 估计数量\n3. 新鲜度评估\n4. 建议食用期限\n请以 JSON 格式返回"
            )
            
            if result:
                return self._parse_ingredients_result(result)
        
        except Exception as e:
            logger.error(f"冰箱分析失败：{e}")
        
        return None
    
    # ========== API 调用 ==========
    
    def _call_vision_api(self, image_base64: str, prompt: str) -> Optional[str]:
        """调用视觉 API"""
        if not self.dashscope_api_key:
            logger.info("未设置 API Key")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.dashscope_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'qwen-vl-plus',
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'image': f'data:image/jpeg;base64,{image_base64}'},
                            {'text': prompt}
                        ]
                    }
                ]
            },
            'parameters': {
                'max_tokens': 1000,
                'temperature': 0.7
            }
        }
        
        try:
            response = requests.post(self.vision_api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('output', {}).get('text', '')
            else:
                logger.error(f"API 调用失败：{response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.info(f"API 调用异常：{e}")
            return None
    
    # ========== 结果解析 ==========
    
    def _parse_receipt_result(self, text: str) -> Dict:
        """解析发票识别结果"""
        # 简化实现，实际应使用 JSON 解析
        return {
            'type': 'receipt',
            'description': text,
            'total_amount': self._extract_amount(text),
            'merchant': self._extract_merchant(text),
            'date': self._extract_date(text)
        }
    
    def _parse_product_result(self, text: str) -> Dict:
        """解析商品识别结果"""
        return {
            'type': 'product',
            'description': text,
            'name': self._extract_product_name(text),
            'category': self._extract_category(text),
            'price_range': self._extract_price_range(text)
        }
    
    def _parse_cart_result(self, text: str) -> Dict:
        """解析购物车结果"""
        return {
            'type': 'shopping_cart',
            'description': text,
            'items': self._extract_items(text),
            'total': self._extract_amount(text)
        }
    
    def _parse_ingredients_result(self, text: str) -> Dict:
        """解析食材结果"""
        return {
            'type': 'ingredients',
            'description': text,
            'items': self._extract_items(text),
            'suggestions': self._generate_suggestions(text)
        }
    
    # ========== 工具方法 ==========
    
    def _extract_amount(self, text: str) -> float:
        """提取金额"""
        import re
        pattern = r'[\d.]+元|[\d.]+块|¥[\d.]+'
        match = re.search(pattern, text)
        if match:
            return float(re.search(r'[\d.]+', match.group()).group())
        return 0.0
    
    def _extract_merchant(self, text: str) -> str:
        """提取商家名称"""
        # 简化实现
        return "未知商家"
    
    def _extract_date(self, text: str) -> str:
        """提取日期"""
        import re
        pattern = r'\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}'
        match = re.search(pattern, text)
        if match:
            return match.group()
        return time.strftime('%Y-%m-%d')
    
    def _extract_product_name(self, text: str) -> str:
        """提取商品名"""
        # 简化实现
        return "未知商品"
    
    def _extract_category(self, text: str) -> str:
        """提取类别"""
        # 简化实现
        return "其他"
    
    def _extract_price_range(self, text: str) -> str:
        """提取价格范围"""
        # 简化实现
        return "未知"
    
    def _extract_items(self, text: str) -> List[Dict]:
        """提取商品列表"""
        # 简化实现
        return []
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        # 简化实现
        return []
    
    def _generate_suggestions(self, text: str) -> List[str]:
        """生成建议"""
        # 简化实现
        return ["建议尽快食用"]


# 使用示例
if __name__ == '__main__':
    ai = AIImageRecognition()
    ai.set_api_key('sk-xxxxx')
    
    # 识别发票
    result = ai.recognize_receipt('receipt.jpg')
    if result:
        logger.info(f"发票识别成功：{result}")
    
    # 识别商品
    result = ai.recognize_product('product.jpg')
    if result:
        logger.info(f"商品识别成功：{result}")
    
    # OCR 识别
    text = ai.recognize_text('text.jpg')
    if text:
        logger.info(f"文字识别：{text}")
    
    # 分析购物车
    result = ai.analyze_shopping_cart('cart.jpg')
    if result:
        logger.info(f"购物车分析：{result}")
    
    # 分析冰箱
    result = ai.analyze_refrigerator('fridge.jpg')
    if result:
        logger.info(f"冰箱分析：{result}")
