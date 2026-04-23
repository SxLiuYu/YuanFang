"""
AI Gateway 服务
统一代理所有 AI API 调用，支持 DashScope、OpenAI 等
"""

from flask import Blueprint, request, jsonify
import requests
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ai_gateway = Blueprint('ai_gateway', __name__, url_prefix='/api/ai')

DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/api/v1'

DEFAULT_MODEL = os.getenv('AI_DEFAULT_MODEL', 'qwen-max')
DEFAULT_SYSTEM_PROMPT = '你是一个智能家庭助手，请理解用户的指令并提供相应的帮助。'


@ai_gateway.route('/chat', methods=['POST'])
def chat():
    """
    统一聊天接口
    请求体: {
        "message": "用户消息",
        "context": [{"role": "user", "content": "..."}],  // 可选
        "model": "qwen-max",  // 可选
        "system_prompt": "..."  // 可选
    }
    """
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', [])
        model = data.get('model', DEFAULT_MODEL)
        system_prompt = data.get('system_prompt', DEFAULT_SYSTEM_PROMPT)
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        messages = [{'role': 'system', 'content': system_prompt}]
        messages.extend(context)
        messages.append({'role': 'user', 'content': message})
        
        response = call_dashscope(messages, model)
        
        if response.get('success'):
            return jsonify({
                'success': True,
                'content': response['content'],
                'model': model
            })
        else:
            return jsonify({
                'success': False,
                'error': response.get('error', 'AI 服务调用失败')
            }), 500
            
    except Exception as e:
        logger.error(f"Chat API 错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gateway.route('/complete', methods=['POST'])
def complete():
    """
    文本补全接口
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        model = data.get('model', DEFAULT_MODEL)
        max_tokens = data.get('max_tokens', 500)
        
        if not prompt:
            return jsonify({'error': '提示词不能为空'}), 400
        
        messages = [
            {'role': 'system', 'content': DEFAULT_SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt}
        ]
        
        response = call_dashscope(messages, model, max_tokens)
        
        if response.get('success'):
            return jsonify({
                'success': True,
                'content': response['content']
            })
        else:
            return jsonify({
                'success': False,
                'error': response.get('error', 'AI 服务调用失败')
            }), 500
            
    except Exception as e:
        logger.error(f"Complete API 错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_gateway.route('/models', methods=['GET'])
def list_models():
    """
    列出可用模型
    """
    return jsonify({
        'models': [
            {'id': 'qwen-max', 'name': '通义千问 Max', 'description': '最强推理能力'},
            {'id': 'qwen-plus', 'name': '通义千问 Plus', 'description': '平衡性能与成本'},
            {'id': 'qwen-turbo', 'name': '通义千问 Turbo', 'description': '快速响应'},
            {'id': 'qwen-long', 'name': '通义千问 Long', 'description': '长文本处理'}
        ]
    })


def call_dashscope(messages, model='qwen-max', max_tokens=500):
    """
    调用 DashScope API
    """
    if not DASHSCOPE_API_KEY:
        logger.error("DASHSCOPE_API_KEY 未配置")
        return {'success': False, 'error': 'API Key 未配置'}
    
    try:
        url = f'{DASHSCOPE_BASE_URL}/services/aigc/text-generation/generation'
        
        headers = {
            'Authorization': f'Bearer {DASHSCOPE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'input': {
                'messages': messages
            },
            'parameters': {
                'temperature': 0.7,
                'top_p': 0.8,
                'max_tokens': max_tokens
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()
        
        if response.ok and data.get('output'):
            choices = data['output'].get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', '')
                return {'success': True, 'content': content}
        
        error_msg = data.get('message', data.get('code', '未知错误'))
        logger.error(f"DashScope API 错误: {error_msg}")
        return {'success': False, 'error': error_msg}
        
    except requests.Timeout:
        return {'success': False, 'error': '请求超时'}
    except Exception as e:
        logger.error(f"DashScope 调用异常: {e}")
        return {'success': False, 'error': str(e)}


def register_ai_gateway(app):
    """
    注册 AI Gateway 到 Flask 应用
    """
    app.register_blueprint(ai_gateway)
    logger.info("AI Gateway 已注册")