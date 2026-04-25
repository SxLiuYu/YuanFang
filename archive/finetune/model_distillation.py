#!/usr/bin/env python3
"""
模型蒸馏系统
- 大模型"老师"生成高质量回答
- 小模型"学生"学习
- 持续积累经验，小模型越来越好
"""

import json
import os
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DistillationExample:
    """蒸馏样本"""
    query: str
    teacher_response: str  # 大模型回答
    student_response: Optional[str] = None  # 小模型回答
    reasoning_trace: Optional[str] = None  # 大模型思考过程
    timestamp: float = 0.0
    quality_score: float = 0.0  # 质量评分


class ModelDistillationSystem:
    """模型蒸馏系统"""
    
    def __init__(
        self,
        teacher_model,  # 大模型
        student_model,  # 小模型
        storage_path: str = "~/.yuanfang/distillation"
    ):
        self.teacher = teacher_model
        self.student = student_model
        self.storage_path = Path(storage_path).expanduser()
        self.examples_path = self.storage_path / "examples.jsonl"
        
        # 初始化目录
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 加载已有样本
        self.examples: List[DistillationExample] = []
        self._load_examples()
        
        print(f"🧠 模型蒸馏系统初始化")
        print(f"   老师模型: {getattr(teacher_model, 'model', 'unknown')}")
        print(f"   学生模型: {getattr(student_model, 'model', 'unknown')}")
        print(f"   已有样本: {len(self.examples)}")
    
    def query(
        self, 
        query: str, 
        use_teacher: bool = True,
        save_example: bool = True
    ) -> Dict[str, Any]:
        """
        查询 - 优先用大模型，同时让小模型学习
        
        Args:
            query: 用户问题
            use_teacher: 是否用老师模型
            save_example: 是否保存样本
        
        Returns:
            结果字典
        """
        result = {
            "query": query,
            "timestamp": time.time(),
            "use_teacher": use_teacher
        }
        
        # 1. 老师模型回答（高质量）
        if use_teacher:
            print("👨‍🏫 老师模型思考中...")
            teacher_response = self.teacher.chat(query)
            result["teacher_response"] = teacher_response
            print(f"✅ 老师回答完成 ({len(teacher_response)} chars)")
        
        # 2. 学生模型尝试回答
        print("👨‍🎓 学生模型尝试回答...")
        try:
            student_response = self.student.chat(query)
            result["student_response"] = student_response
            print(f"✅ 学生回答完成 ({len(student_response)} chars)")
        except Exception as e:
            print(f"⚠️  学生回答失败: {e}")
            result["student_response"] = None
        
        # 3. 简单的质量评估
        if use_teacher and result.get("student_response"):
            quality_score = self._simple_quality_evaluate(
                query,
                result["teacher_response"],
                result["student_response"]
            )
            result["quality_score"] = quality_score
            print(f"📊 学生回答质量评分: {quality_score:.2f}/1.00")
        
        # 4. 保存样本
        if save_example and use_teacher:
            example = DistillationExample(
                query=query,
                teacher_response=result["teacher_response"],
                student_response=result.get("student_response"),
                timestamp=result["timestamp"],
                quality_score=result.get("quality_score", 0)
            )
            self._save_example(example)
            print(f"💾 样本已保存 (累计: {len(self.examples)})")
        
        # 5. 返回老师的回答（当前优先用老师）
        result["final_response"] = result.get("teacher_response", result.get("student_response"))
        
        return result
    
    def _simple_quality_evaluate(
        self,
        query: str,
        teacher_response: str,
        student_response: str
    ) -> float:
        """
        简单的质量评估（实际可以用更复杂的方法）
        
        评分策略：
        - 长度相似度
        - 关键词重叠
        - 简单的语义相似度（这里简化了）
        """
        score = 0.0
        
        # 1. 长度相似度
        len_teacher = len(teacher_response)
        len_student = len(student_response)
        if len_teacher > 0:
            len_ratio = min(len_student / len_teacher, len_teacher / len_student)
            score += 0.3 * len_ratio
        
        # 2. 简单的关键词重叠
        words_teacher = set(teacher_response.lower().split())
        words_student = set(student_response.lower().split())
        if words_teacher:
            overlap = len(words_teacher & words_student) / len(words_teacher)
            score += 0.4 * overlap
        
        # 3. 完整性检查（学生回答是否包含关键信息
        key_phrases = ["```", "代码", "示例", "方法", "步骤", "注意"]
        for phrase in key_phrases:
            if phrase in teacher_response and phrase in student_response:
                score += 0.05  # 每个关键词加5分
        
        return min(score, 1.0)
    
    def _save_example(self, example: DistillationExample):
        """保存一个样本"""
        self.examples.append(example)
        
        # 追加到文件
        with open(self.examples_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "query": example.query,
                "teacher_response": example.teacher_response,
                "student_response": example.student_response,
                "timestamp": example.timestamp,
                "quality_score": example.quality_score
            }, ensure_ascii=False) + "\n")
    
    def _load_examples(self):
        """加载已有样本"""
        if not self.examples_path.exists():
            return
        
        with open(self.examples_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    example = DistillationExample(
                        query=data["query"],
                        teacher_response=data["teacher_response"],
                        student_response=data.get("student_response"),
                        timestamp=data.get("timestamp", 0),
                        quality_score=data.get("quality_score", 0)
                    )
                    self.examples.append(example)
                except Exception as e:
                    print(f"⚠️  加载样本失败: {e}")
    
    def get_student_progress(self) -> Dict[str, Any]:
        """获取学生模型的学习进度"""
        if not self.examples:
            return {"message": "还没有样本"}
        
        # 计算平均质量分
        scores = [e.quality_score for e in self.examples if e.quality_score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 最近10个样本的趋势
        recent_scores = scores[-10:]
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        return {
            "total_examples": len(self.examples),
            "avg_quality_score": avg_score,
            "recent_avg_score": recent_avg,
            "improving": recent_avg > avg_score if len(scores) > 10 else None,
            "examples": [
                {
                    "query": e.query[:50] + "...",
                    "quality_score": e.quality_score,
                    "time": time.strftime("%Y-%m-%d %H:%M", time.localtime(e.timestamp))
                }
                for e in self.examples[-5:]  # 最近5个
            ]
        }
    
    def export_finetuning_data(self, output_path: str = "finetuning_data.jsonl"):
        """导出为微调数据格式"""
        with open(output_path, "w", encoding="utf-8") as f:
            for example in self.examples:
                # 用chat format
                data = {
                    "messages": [
                        {"role": "user", "content": example.query},
                        {"role": "assistant", "content": example.teacher_response}
                    ]
                }
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        
        print(f"✅ 已导出 {len(self.examples)} 条微调数据到 {output_path}")
        return output_path


# ============================================
# 简单示例
# ============================================

def demo():
    """演示蒸馏系统"""
    print("="*60)
    print("🧠 模型蒸馏系统 - 演示")
    print("="*60)
    print()
    
    # 这里用mock模型演示，实际可以换成oMLX
    from simple_llm_client_mock import SimpleLLMClient as MockClient
    from simple_llm_client_omlx import SimpleLLMClient as OMLXClient
    
    print("🔧 初始化模型...")
    
    # 老师模型（用真实的oMLX）
    teacher = OMLXClient(api_key="omlx")
    
    # 学生模型（这里先用mock演示，实际可以换成更小的本地模型）
    student = MockClient(model="Mock-Student-1B")
    
    # 初始化蒸馏系统
    distiller = ModelDistillationSystem(
        teacher_model=teacher,
        student_model=student
    )
    
    print()
    
    # 测试查询
    query = "如何优化Python代码的性能？"
    print(f"🤔 测试查询: {query}")
    print()
    
    result = distiller.query(query, use_teacher=True, save_example=True)
    
    print()
    print("="*60)
    print("✨ 最终回答（老师模型）:")
    print("="*60)
    print(result["final_response"][:500] + "..." if len(result["final_response"]) > 500 else result["final_response"])
    print()
    
    # 查看进度
    progress = distiller.get_student_progress()
    print("="*60)
    print("📊 学生学习进度:")
    print("="*60)
    print(f"   总样本数: {progress['total_examples']}")
    print(f"   平均质量分: {progress.get('avg_quality_score', 0):.2f}")
    print()


if __name__ == '__main__':
    demo()
