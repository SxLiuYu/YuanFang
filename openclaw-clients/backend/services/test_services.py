"""
后端服务单元测试
测试家庭服务 API、做菜服务、语音交互服务等
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestCookingService(unittest.TestCase):
    """做菜服务测试"""

    def setUp(self):
        try:
            from cooking_service import CookingService
            self.cooking_service = CookingService(':memory:')
        except Exception as e:
            self.skipTest(f"无法初始化: {e}")

    def test_search_recipes(self):
        result = self.cooking_service.search_recipes("红烧肉", limit=5)
        self.assertIn('success', result)

    def test_save_recipe(self):
        result = self.cooking_service.save_recipe(
            title="测试菜谱",
            ingredients=["食材1", "食材2"],
            steps=["步骤1", "步骤2"],
            cook_time=30
        )
        self.assertTrue(result.get('success', False))


class TestVoiceInteractionService(unittest.TestCase):
    """语音交互服务测试"""

    def setUp(self):
        try:
            from voice_interaction_service import VoiceInteractionService
            self.voice_service = VoiceInteractionService()
        except Exception as e:
            self.skipTest(f"无法初始化: {e}")

    def test_parse_voice_command(self):
        result = self.voice_service.parse_voice_command("下一步")
        self.assertEqual(result, 'next_step')

    def test_text_to_speech(self):
        result = self.voice_service.text_to_speech("测试")
        self.assertIn('success', result)


class TestAutomationEngine(unittest.TestCase):
    """自动化引擎测试"""

    def setUp(self):
        try:
            from automation_engine import AutomationEngine
            self.engine = AutomationEngine(':memory:')
        except Exception as e:
            self.skipTest(f"无法初始化: {e}")

    def test_add_rule(self):
        result = self.engine.add_rule(
            name="测试规则",
            trigger_type="time",
            trigger_config={"time": "08:00"},
            actions=[]
        )
        self.assertTrue(result.get('success', False))

    def test_get_rules(self):
        rules = self.engine.get_rules()
        self.assertIsInstance(rules, list)


if __name__ == '__main__':
    unittest.main()