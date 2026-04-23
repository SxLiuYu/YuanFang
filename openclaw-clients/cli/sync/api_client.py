"""API客户端模块"""

import requests
from typing import Dict, Any, Optional
import json


class OpenClawClient:
    """OpenClaw API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8082"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
        
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, json=data, timeout=10)
            else:
                return {'success': False, 'error': f'不支持的HTTP方法: {method}'}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
        
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': '无法连接到服务器，请确保后端服务已启动'}
        except requests.exceptions.Timeout:
            return {'success': False, 'error': '请求超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET请求"""
        return self._request('GET', endpoint, params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """POST请求"""
        return self._request('POST', endpoint, data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """PUT请求"""
        return self._request('PUT', endpoint, data)
    
    def delete(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """DELETE请求"""
        return self._request('DELETE', endpoint, data)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = self.get('/health')
            return {'success': True, **response}
        except:
            return {'success': False}