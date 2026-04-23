"""
knowledge/dynamic_updater.py
知识库动态更新
- 对话中自动提取事实
- 自动更新层级化记忆
- 支持用户确认更正
- 增量更新向量库
"""

import json
import re
import os
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from memory.hierarchical import get_hierarchical_memory
from memory.vector import VectorMemory
from core.llm_adapter import get_llm


# 提取提示模板
EXTRACTION_PROMPT = """
你是元芳AI助手的知识库自动更新模块，负责从对话中提取有用的事实信息存入永久知识库。

分析下面这段对话，提取出关于用户、偏好、事实信息、日程安排等应该记住的内容。

对话内容:
{dialog}

请按以下要求提取：
1. 只提取明确陈述的事实，不要猜测
2. 对于不确定的信息不要提取
3. 分类整理到不同category：user_profile, user_preference, fact, event, other
4. 输出JSON格式，示例：
{{
  "entries": [
    {{
      "key": "user_name",
      "value": "张三",
      "category": "user_profile",
      "importance": 0.9,
      "confidence": 0.95
    }},
    {{
      "key": "favorite_drink", 
      "value": "冰咖啡不加糖",
      "category": "user_preference",
      "importance": 0.7,
      "confidence": 0.9
    }}
  ]
}}

如果没有需要提取的内容，entries返回空数组。
只输出JSON，不要其他内容。
"""


class KnowledgeDynamicUpdater:
    """知识库动态更新器"""
    
    def __init__(self):
        self.hm = get_hierarchical_memory()
        self.llm = get_llm()
        self._init_pending()
    
    def _init_pending(self):
        """初始化待确认目录"""
        self.pending_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "pending_knowledge.json"
        )
        os.makedirs(os.path.dirname(self.pending_file), exist_ok=True)
        if not os.path.exists(self.pending_file):
            with open(self.pending_file, "w", encoding="utf-8") as f:
                json.dump([], f)
    
    def _load_pending(self) -> List[Dict]:
        """加载待确认知识"""
        try:
            with open(self.pending_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_pending(self, pending: List[Dict]):
        """保存待确认知识"""
        with open(self.pending_file, "w", encoding="utf-8") as f:
            json.dump(pending, f, ensure_ascii=False, indent=2)
    
    def extract_from_dialog(self, user_input: str, ai_response: str) -> List[Dict]:
        """从对话中提取新知识"""
        dialog = f"用户: {user_input}\n元芳: {ai_response}"
        prompt = EXTRACTION_PROMPT.format(dialog=dialog)
        
        try:
            response = self.llm.chat_simple([
                {"role": "user", "content": prompt}
            ], temperature=0.0, max_tokens=1024, model="Pro/deepseek-ai/DeepSeek-V3.1-Terminus")
            
            # 清理JSON
            response = response.strip()
            response = response.replace("```json", "").replace("```", "").strip()
            
            # 尝试解析
            data = json.loads(response)
            entries = data.get("entries", [])
            
            # 过滤掉低置信度
            entries = [e for e in entries if e.get("confidence", 0) >= 0.5]
            
            return entries
        except Exception as e:
            print(f"[KnowledgeUpdater] 提取失败: {e}")
            return []
    
    def auto_update(self, user_input: str, ai_response: str, 
                   require_confirmation: bool = True) -> Tuple[int, List[Dict]]:
        """自动提取并更新知识库
        require_confirmation=True: 高置信度直接保存，中置信度待确认
        返回 (更新数量, 待确认列表)
        """
        entries = self.extract_from_dialog(user_input, ai_response)
        updated = 0
        pending = []
        
        for entry in entries:
            confidence = entry.get("confidence", 0.8)
            importance = entry.get("importance", 0.5)
            key = entry.get("key")
            value = entry.get("value")
            category = entry.get("category", "fact")
            
            if not key:
                continue
            
            if require_confirmation:
                if confidence >= 0.9:
                    # 高置信度直接保存
                    self._save_entry(entry)
                    updated += 1
                elif confidence >= 0.5:
                    # 中等置信度加入待确认
                    entry["extracted_at"] = datetime.now().isoformat()
                    pending.append(entry)
            else:
                # 不需要确认，直接保存
                self._save_entry(entry)
                updated += 1
        
        # 保存待确认
        existing_pending = self._load_pending()
        existing_pending.extend(pending)
        self._save_pending(existing_pending)
        
        return updated, pending
    
    def _save_entry(self, entry: Dict):
        """保存条目到层级记忆"""
        category = entry.get("category", "fact")
        key = entry["key"]
        value = entry["value"]
        importance = entry.get("importance", 0.5)
        
        if category == "user_preference":
            self.hm.store_user_preference(key, value, entry.get("confidence", 0.8))
        else:
            self.hm.store_permanent_fact(key, value, category, importance)
    
    def get_pending_confirmations(self) -> List[Dict]:
        """获取待确认知识列表"""
        return self._load_pending()
    
    def confirm_entry(self, index: int, confirmed: bool, 
                     corrected_value: Any = None) -> bool:
        """确认/更正一条待确认知识"""
        pending = self._load_pending()
        if index < 0 or index >= len(pending):
            return False
        
        entry = pending[index]
        
        if confirmed:
            if corrected_value is not None:
                entry["value"] = corrected_value
            self._save_entry(entry)
            # 移除待确认
            del pending[index]
            self._save_pending(pending)
            return True
        else:
            # 用户拒绝，直接删除
            del pending[index]
            self._save_pending(pending)
            return False
    
    def update_vector_memory(self, vector_memory: VectorMemory):
        """将永久知识增量更新到向量记忆"""
        facts = self.hm.get_all_facts()
        # 全部存入向量记忆用于语义检索
        for fact in facts:
            text = f"{fact['fact_key']}: {fact['fact_value']}"
            vector_memory.store(text, {
                "category": fact["category"],
                "importance": fact["importance"],
                "source": "dynamic_knowledge"
            })
        return len(facts)
    
    def search_knowledge(self, query: str, vector_memory: VectorMemory, 
                        top_k: int = 5) -> List[Dict]:
        """语义搜索知识库"""
        results = vector_memory.search(query, top_k=top_k)
        # 过滤出动态知识
        return [r for r in results if r.get("metadata", {}).get("source") == "dynamic_knowledge"]


# 单例
_updater_instance = None

def get_knowledge_updater() -> KnowledgeDynamicUpdater:
    global _updater_instance
    if _updater_instance is None:
        _updater_instance = KnowledgeDynamicUpdater()
    return _updater_instance


if __name__ == "__main__":
    # 测试
    updater = KnowledgeDynamicUpdater()
    print("✅ KnowledgeDynamicUpdater 初始化成功")
    
    # 测试提取
    test_user = "我叫于金泽，我喜欢喝美式咖啡不加糖，我每周三下午开会。"
    test_ai = "好的于先生，我记下了。"
    
    updated, pending = updater.auto_update(test_user, test_ai)
    print(f"📝 测试提取: 自动保存 {updated} 条，待确认 {len(pending)} 条")
    
    stats = updater.hm.get_stats()
    print(f"📊 当前知识库统计: {stats}")
    
    pending_list = updater.get_pending_confirmations()
    print(f"📋 待确认列表: {len(pending_list)}")
    
    print("✅ 测试完成")
