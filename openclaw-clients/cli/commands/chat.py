"""聊天命令模块"""

from typing import Dict, Any, Optional


def send_message(client, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    发送消息给AI
    
    Args:
        client: OpenClaw客户端
        message: 消息内容
        session_id: 会话ID
    
    Returns:
        AI回复
    """
    try:
        data = {
            'message': message,
            'voice_output': False
        }
        
        if session_id:
            data['session_id'] = session_id
        
        response = client.post('/api/v1/agent/chat', data)
        
        if response.get('success'):
            return {
                'success': True,
                'text': response.get('text', ''),
                'session_id': response.get('session_id')
            }
        return {'success': False, 'error': response.get('error', '对话失败')}
    except Exception as e:
        return {'success': False, 'error': str(e)}