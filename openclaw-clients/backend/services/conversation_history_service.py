import logging
logger = logging.getLogger(__name__)
"""
对话历史管理服务
支持多轮对话上下文、会话管理、历史持久化
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class ConversationHistoryService:
    """对话历史管理服务"""

    # 配置
    MAX_HISTORY_MESSAGES = 20  # 最大历史消息数
    MAX_CONTEXT_TOKENS = 4000  # 最大上下文token数（约）

    def __init__(self, db_path: str = 'conversation_history.db'):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """初始化数据库表"""
        conn = self._get_conn()
        c = conn.cursor()

        # 会话表
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        ''')

        # 消息表
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                token_count INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES conversation_sessions(id)
            )
        ''')

        # 创建索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON conversation_messages(session_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_updated ON conversation_sessions(updated_at)')

        conn.commit()
        conn.close()

    # ========== 会话管理 ==========

    def create_session(self, session_name: str = '新会话') -> Dict[str, Any]:
        """创建新会话"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            now = datetime.now()
            c.execute('''
                INSERT INTO conversation_sessions (session_name, created_at, updated_at, message_count)
                VALUES (?, ?, ?, 0)
            ''', (session_name, now, now))

            session_id = c.lastrowid
            conn.commit()

            return {
                'success': True,
                'session_id': session_id,
                'session_name': session_name
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('''
            SELECT id, session_name, created_at, updated_at, message_count
            FROM conversation_sessions
            ORDER BY updated_at DESC
        ''')

        sessions = []
        for row in c.fetchall():
            sessions.append({
                'session_id': row['id'],
                'session_name': row['session_name'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'message_count': row['message_count']
            })

        conn.close()
        return sessions

    def delete_session(self, session_id: int) -> Dict[str, Any]:
        """删除会话及其消息"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            # 删除消息
            c.execute('DELETE FROM conversation_messages WHERE session_id = ?', (session_id,))

            # 删除会话
            c.execute('DELETE FROM conversation_sessions WHERE id = ?', (session_id,))

            conn.commit()
            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    # ========== 消息管理 ==========

    def add_message(self, session_id: int, role: str, content: str) -> Dict[str, Any]:
        """添加消息"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            # 估算token数
            token_count = self._estimate_tokens(content)

            c.execute('''
                INSERT INTO conversation_messages
                (session_id, role, content, token_count, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, role, content, token_count, datetime.now()))

            message_id = c.lastrowid

            # 更新会话统计
            c.execute('''
                UPDATE conversation_sessions
                SET updated_at = ?, message_count = message_count + 1
                WHERE id = ?
            ''', (datetime.now(), session_id))

            conn.commit()

            return {
                'success': True,
                'message_id': message_id,
                'token_count': token_count
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_conversation_history(self, session_id: int,
                                  max_messages: int = None) -> List[Dict[str, Any]]:
        """获取对话历史（用于API调用）"""
        if max_messages is None:
            max_messages = self.MAX_HISTORY_MESSAGES

        conn = self._get_conn()
        c = conn.cursor()

        c.execute('''
            SELECT role, content, token_count, created_at
            FROM conversation_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (session_id, max_messages))

        messages = []
        for row in c.fetchall():
            messages.append({
                'role': row['role'],
                'content': row['content'],
                'token_count': row['token_count'],
                'created_at': row['created_at']
            })

        conn.close()

        # 反转顺序（从旧到新）
        messages.reverse()
        return messages

    def get_conversation_for_api(self, session_id: int,
                                  system_prompt: str = None) -> List[Dict[str, str]]:
        """获取对话历史（OpenAI API格式）"""
        messages = []

        # 系统提示
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        else:
            messages.append({
                'role': 'system',
                'content': '你是一个智能家庭助手，请理解用户的语音指令并提供相应的帮助。' +
                          '你可以帮助用户控制智能家居、管理家庭任务、记录健康数据、查询天气新闻等。' +
                          '请用简洁友好的方式回复。'
            })

        # 历史消息（带token限制）
        history = self.get_conversation_history_with_token_limit(session_id)
        messages.extend(history)

        return messages

    def get_conversation_history_with_token_limit(self, session_id: int) -> List[Dict[str, str]]:
        """获取对话历史（带token限制）"""
        conn = self._get_conn()
        c = conn.cursor()

        c.execute('''
            SELECT role, content, token_count
            FROM conversation_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))

        messages = []
        total_tokens = 0

        for row in c.fetchall():
            if total_tokens + row['token_count'] <= self.MAX_CONTEXT_TOKENS:
                messages.append({
                    'role': row['role'],
                    'content': row['content']
                })
                total_tokens += row['token_count']
            else:
                break

        conn.close()

        # 反转顺序
        messages.reverse()
        return messages

    def clear_session_history(self, session_id: int) -> Dict[str, Any]:
        """清空会话历史"""
        conn = self._get_conn()
        c = conn.cursor()

        try:
            c.execute('DELETE FROM conversation_messages WHERE session_id = ?', (session_id,))
            c.execute('''
                UPDATE conversation_sessions
                SET message_count = 0, updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), session_id))

            conn.commit()
            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def _estimate_tokens(self, text: str) -> int:
        """估算token数"""
        if not text:
            return 0

        # 粗略估算：中文约1.5字符/token，英文约4字符/token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars

        return int(chinese_chars / 1.5 + other_chars / 4)


# API 端点集成
def register_conversation_api(app, service: ConversationHistoryService):
    """注册对话历史API端点"""

    @app.route('/api/conversation/sessions', methods=['GET'])
    def get_sessions():
        """获取所有会话"""
        sessions = service.get_sessions()
        return {'success': True, 'sessions': sessions}

    @app.route('/api/conversation/sessions', methods=['POST'])
    def create_session():
        """创建新会话"""
        data = request.get_json()
        session_name = data.get('session_name', '新会话')
        result = service.create_session(session_name)
        return result

    @app.route('/api/conversation/sessions/<int:session_id>', methods=['DELETE'])
    def delete_session(session_id):
        """删除会话"""
        result = service.delete_session(session_id)
        return result

    @app.route('/api/conversation/sessions/<int:session_id>/messages', methods=['GET'])
    def get_messages(session_id):
        """获取会话消息"""
        messages = service.get_conversation_history(session_id)
        return {'success': True, 'messages': messages}

    @app.route('/api/conversation/sessions/<int:session_id>/messages', methods=['POST'])
    def add_message(session_id):
        """添加消息"""
        data = request.get_json()
        role = data.get('role')
        content = data.get('content')

        if not role or not content:
            return {'success': False, 'error': '缺少必要参数'}, 400

        result = service.add_message(session_id, role, content)
        return result

    @app.route('/api/conversation/sessions/<int:session_id>/clear', methods=['POST'])
    def clear_history(session_id):
        """清空历史"""
        result = service.clear_session_history(session_id)
        return result


# 测试代码
if __name__ == '__main__':
    service = ConversationHistoryService()

    logger.info("=== 对话历史服务测试 ===\n")

    # 创建会话
    logger.info("1. 创建会话...")
    result = service.create_session("测试会话")
    logger.info(f"   结果: {result}\n")

    if result['success']:
        session_id = result['session_id']

        # 添加消息
        logger.info("2. 添加用户消息...")
        result = service.add_message(session_id, 'user', '你好，今天天气怎么样？')
        logger.info(f"   结果: {result}\n")

        logger.info("3. 添加AI回复...")
        result = service.add_message(session_id, 'assistant', '今天天气晴朗，温度适宜，适合外出活动。')
        logger.info(f"   结果: {result}\n")

        # 获取历史
        logger.info("4. 获取对话历史...")
        messages = service.get_conversation_for_api(session_id)
        for msg in messages:
            logger.info(f"   [{msg['role']}]: {msg['content'][:50]}...\n")

        # 获取会话列表
        logger.info("5. 获取会话列表...")
        sessions = service.get_sessions()
        for s in sessions:
            logger.info(f"   - {s['session_name']} ({s['message_count']}条消息)\n")

    logger.info("✅ 测试完成！")