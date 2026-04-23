import logging
logger = logging.getLogger(__name__)
"""
语音交互服务 - TTS 语音播报 + 语音指令识别
用于做菜场景的语音指导和语音控制
"""

import os
import subprocess
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class VoiceInteractionService:
    """语音交互服务"""
    
    def __init__(self):
        # TTS 配置
        self.tts_engine = 'edge-tts'  # 可选：edge-tts, pyttsx3, system
        self.voice_zh = 'zh-CN-XiaoxiaoNeural'  # 中文女声
        self.voice_zh_male = 'zh-CN-YunxiNeural'  # 中文男声
        self.output_dir = '/tmp/tts_output'
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 语音指令关键词
        self.voice_commands = {
            'next_step': ['下一步', '继续', '下一个', '往下'],
            'prev_step': ['上一步', '返回', '上一个', '往前'],
            'repeat_step': ['重复', '再说一遍', '再来一次'],
            'start_timer': ['开始计时', '计时', '设个闹钟'],
            'stop_timer': ['停止计时', '取消计时', '停'],
            'show_list': ['购物清单', '采购清单', '要买什么'],
            'add_item': ['添加到清单', '加到购物单', '记一下'],
            'cooking_mode': ['做菜模式', '开始做菜', '做饭'],
            'exit': ['退出', '结束', '不做了']
        }
    
    # ========== TTS 语音合成 ==========
    
    def text_to_speech(self, text: str, output_file: str = None, 
                       voice: str = None, rate: str = '+0%') -> Dict[str, Any]:
        """
        文本转语音（使用 edge-tts）
        
        Args:
            text: 要转换的文本
            output_file: 输出文件路径（可选，默认自动生成）
            voice: 语音音色（可选，默认中文女声）
            rate: 语速（可选，如：+20%, -10%）
        
        Returns:
            {'success': bool, 'audio_path': str, 'duration': float}
        """
        if not voice:
            voice = self.voice_zh
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            output_file = os.path.join(self.output_dir, f'tts_{timestamp}.mp3')
        
        try:
            # 使用 edge-tts 生成语音
            command = [
                'edge-tts',
                '--voice', voice,
                '--text', text,
                '--rate', rate,
                '--write-media', output_file
            ]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                # 获取音频时长（使用 ffprobe 或估算）
                duration = self._get_audio_duration(output_file)
                
                return {
                    'success': True,
                    'audio_path': output_file,
                    'duration': duration,
                    'text': text
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr.strip() or 'TTS 生成失败'
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'TTS 生成超时'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': '未找到 edge-tts，请先安装：pip install edge-tts'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        try:
            # 使用 ffprobe
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=5
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        
        # 估算：约 15 字/秒
        return 2.0  # 默认 2 秒
    
    def generate_step_audio(self, step_text: str, step_number: int) -> Dict[str, Any]:
        """
        生成步骤语音
        
        Args:
            step_text: 步骤文本
            step_number: 步骤编号
        
        Returns:
            TTS 结果
        """
        full_text = f"第{step_number}步：{step_text}"
        return self.text_to_speech(full_text)
    
    def generate_cooking_intro(self, recipe_title: str, cook_time: int, 
                                difficulty: str) -> Dict[str, Any]:
        """
        生成菜谱介绍语音
        
        Args:
            recipe_title: 菜名
            cook_time: 烹饪时间
            difficulty: 难度
        
        Returns:
            TTS 结果
        """
        difficulty_map = {
            'easy': '简单',
            'medium': '中等',
            'hard': '困难'
        }
        
        text = f"今天我们来做的菜是：{recipe_title}。"
        text += f"预计需要{cook_time}分钟，难度{difficulty_map.get(difficulty, '中等')}。"
        text += "准备好了吗？我们开始吧！"
        
        return self.text_to_speech(text, voice=self.voice_zh_male)
    
    def generate_timer_alert(self, timer_name: str) -> Dict[str, Any]:
        """
        生成计时器提醒语音
        
        Args:
            timer_name: 计时器名称
        
        Returns:
            TTS 结果
        """
        text = f"叮！{timer_name}时间到了！"
        return self.text_to_speech(text, rate='+10%')
    
    def generate_confirmation(self, action: str) -> Dict[str, Any]:
        """
        生成确认语音
        
        Args:
            action: 确认的动作
        
        Returns:
            TTS 结果
        """
        text = f"好的，{action}"
        return self.text_to_speech(text)
    
    # ========== 语音指令识别 ==========
    
    def recognize_command(self, text: str) -> Dict[str, Any]:
        """
        识别语音指令文本
        
        Args:
            text: 语音识别后的文本
        
        Returns:
            {
                'recognized': bool,
                'command': str,
                'confidence': float,
                'params': dict
            }
        """
        text = text.lower().strip()
        
        # 匹配指令
        for cmd_type, keywords in self.voice_commands.items():
            for keyword in keywords:
                if keyword in text:
                    # 提取参数
                    params = self._extract_params(cmd_type, text)
                    
                    return {
                        'recognized': True,
                        'command': cmd_type,
                        'confidence': 0.9,
                        'params': params,
                        'original_text': text
                    }
        
        return {
            'recognized': False,
            'command': None,
            'confidence': 0.0,
            'original_text': text
        }
    
    def parse_voice_command(self, text: str) -> str:
        """
        解析语音指令（简化版，返回指令类型）
        
        Args:
            text: 语音识别文本
        
        Returns:
            指令类型字符串
        """
        result = self.recognize_command(text)
        return result.get('command', 'unknown')
    
    def _extract_params(self, cmd_type: str, text: str) -> Dict[str, Any]:
        """提取指令参数"""
        params = {}
        
        if cmd_type == 'start_timer':
            # 提取时间（如：计时 5 分钟）
            import re
            match = re.search(r'(\d+)\s*(分钟 | 秒)', text)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                params['duration'] = value * 60 if '分钟' in unit else value
                params['timer_name'] = text.replace(match.group(0), '').strip() or '计时器'
        
        elif cmd_type == 'add_item':
            # 提取食材（如：添加到清单 鸡蛋 5 个）
            import re
            match = re.search(r'(\S+)\s*(\d+)\s*(个 | 斤 | 克 | 瓶 | 袋)', text)
            if match:
                params['item_name'] = match.group(1)
                params['quantity'] = match.group(2)
                params['unit'] = match.group(3)
            else:
                # 简单提取
                parts = text.split('到清单')
                if len(parts) > 1:
                    params['item_name'] = parts[1].strip()
        
        elif cmd_type in ['next_step', 'prev_step', 'repeat_step']:
            # 提取步骤编号（如：第 3 步）
            import re
            match = re.search(r'第 (\d+)\s*步', text)
            if match:
                params['step_number'] = int(match.group(1))
        
        return params
    
    # ========== 语音交互流程 ==========
    
    def create_cooking_session(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建做菜语音会话
        
        Args:
            recipe: 菜谱数据
        
        Returns:
            会话数据
        """
        session = {
            'session_id': f"cooking_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'recipe': recipe,
            'current_step': 0,
            'total_steps': len(recipe.get('steps', [])),
            'timers': [],
            'created_at': datetime.now()
        }
        
        return session
    
    def get_next_step_audio(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取下一步的语音指导
        
        Args:
            session: 做菜会话
        
        Returns:
            语音数据
        """
        steps = session['recipe'].get('steps', [])
        current = session['current_step']
        
        if current >= len(steps):
            return {
                'success': False,
                'message': '已经是最后一步了',
                'audio': None
            }
        
        # 生成语音
        step_text = steps[current]
        audio_result = self.generate_step_audio(step_text, current + 1)
        
        if audio_result['success']:
            session['current_step'] += 1
        
        return {
            'success': True,
            'step': current + 1,
            'total': len(steps),
            'text': f"第{current + 1}步：{step_text}",
            'audio': audio_result
        }
    
    def handle_voice_command(self, session: Dict[str, Any], 
                             voice_text: str) -> Dict[str, Any]:
        """
        处理语音指令
        
        Args:
            session: 做菜会话
            voice_text: 语音识别文本
        
        Returns:
            处理结果
        """
        # 识别指令
        cmd_result = self.recognize_command(voice_text)
        
        if not cmd_result['recognized']:
            return {
                'success': False,
                'message': '没听清楚，请再说一遍',
                'audio': self.text_to_speech('没听清楚，请再说一遍')
            }
        
        command = cmd_result['command']
        params = cmd_result['params']
        
        # 处理不同指令
        if command == 'next_step':
            return self.get_next_step_audio(session)
        
        elif command == 'prev_step':
            if session['current_step'] > 0:
                session['current_step'] -= 1
                return self.get_step_audio(session, session['current_step'])
            else:
                return {
                    'success': False,
                    'message': '已经是第一步了',
                    'audio': self.text_to_speech('已经是第一步了')
                }
        
        elif command == 'repeat_step':
            # 重复当前步骤
            if session['current_step'] > 0:
                return self.get_step_audio(session, session['current_step'] - 1)
        
        elif command == 'start_timer':
            duration = params.get('duration', 300)  # 默认 5 分钟
            timer_name = params.get('timer_name', '计时器')
            return {
                'success': True,
                'action': 'create_timer',
                'timer_name': timer_name,
                'duration': duration,
                'audio': self.text_to_speech(f'好的，开始{timer_name}计时')
            }
        
        elif command == 'stop_timer':
            return {
                'success': True,
                'action': 'stop_timer',
                'audio': self.text_to_speech('计时已停止')
            }
        
        elif command == 'show_list':
            return {
                'success': True,
                'action': 'show_shopping_list',
                'audio': self.text_to_speech('正在显示购物清单')
            }
        
        elif command == 'exit':
            return {
                'success': True,
                'action': 'exit_cooking',
                'audio': self.text_to_speech('好的，做菜模式已结束')
            }
        
        return {
            'success': False,
            'message': '暂不支持该指令',
            'audio': None
        }
    
    def get_step_audio(self, session: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """获取指定步骤的语音"""
        steps = session['recipe'].get('steps', [])
        
        if step_index < 0 or step_index >= len(steps):
            return {'success': False, 'error': '步骤不存在'}
        
        return self.generate_step_audio(steps[step_index], step_index + 1)


# 快速测试
if __name__ == '__main__':
    service = VoiceInteractionService()
    
    logger.info("=== 语音交互服务测试 ===\n")
    
    # 检查 edge-tts
    logger.info("1. 检查 edge-tts...")
    result = subprocess.run(['which', 'edge-tts'], capture_output=True, text=True)
    if result.returncode == 0:
        logger.info(f"   ✅ edge-tts 已安装：{result.stdout.strip()}")
    else:
        logger.info(f"   ❌ edge-tts 未安装")
        logger.info(f"   安装命令：pip install edge-tts\n")
    
    # 测试 TTS
    logger.info("2. 测试 TTS 生成...")
    result = service.text_to_speech("你好，这是语音测试")
    if result['success']:
        logger.info(f"   ✅ 生成成功：{result['audio_path']}")
        logger.info(f"   时长：{result['duration']}秒\n")
    else:
        logger.error(f"   ❌ 生成失败：{result['error']}\n")
    
    # 测试语音指令识别
    logger.info("3. 测试语音指令识别...")
    test_commands = [
        "下一步",
        "上一步",
        "计时 5 分钟",
        "停止计时",
        "添加到清单 鸡蛋 5 个",
        "退出"
    ]
    
    for cmd in test_commands:
        result = service.recognize_command(cmd)
        if result['recognized']:
            logger.info(f"   ✅ '{cmd}' -> {result['command']} (参数：{result['params']})")
        else:
            logger.info(f"   ❌ '{cmd}' -> 未识别\n")
    
    # 测试做菜会话
    logger.info("\n4. 测试做菜会话...")
    recipe = {
        'title': '西红柿炒蛋',
        'steps': [
            '鸡蛋打散，加少许盐',
            '西红柿洗净切块',
            '热锅凉油，倒入蛋液',
            '加入西红柿翻炒',
            '调味出锅'
        ],
        'cook_time': 10,
        'difficulty': 'easy'
    }
    
    session = service.create_cooking_session(recipe)
    logger.info(f"   会话创建：{session['session_id']}")
    logger.info(f"   菜谱：{session['recipe']['title']}")
    logger.info(f"   步骤数：{session['total_steps']}\n")
    
    # 获取第一步语音
    logger.info("5. 获取第一步语音指导...")
    result = service.get_next_step_audio(session)
    if result['success']:
        logger.info(f"   步骤：{result['step']}/{result['total']}")
        logger.info(f"   文本：{result['text']}")
        if result['audio'] and result['audio']['success']:
            logger.info(f"   音频：{result['audio']['audio_path']}")
    
    logger.info("\n✅ 测试完成！")
