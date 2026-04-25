#!/usr/bin/env python3
"""
伪Qwen3.5 Plus - 用小模型模仿大模型
核心：RAG + 思维链 + 自我反思 + 多步推理
"""

from typing import List, Dict, Any, Optional
import json
import time
from dataclasses import dataclass


@dataclass
class ThoughtStep:
    """思考步骤"""
    step_num: int
    step_type: str  # "analyze", "reason", "critic", "final"
    content: str
    timestamp: float


@dataclass
class RAGResult:
    """RAG检索结果"""
    query: str
    chunks: List[Dict]
    sources: List[str]


class PseudoQwen35Plus:
    """伪Qwen3.5 Plus核心引擎"""
    
    def __init__(self, llm_client, rag_retriever=None):
        """
        Args:
            llm_client: LLM客户端（需要有chat方法）
            rag_retriever: RAG检索器（可选）
        """
        self.llm = llm_client
        self.rag = rag_retriever
        self.thought_history: List[ThoughtStep] = []
    
    def chat(self, query: str, enable_rag: bool = True, num_thought_steps: int = 3) -> str:
        """
        主入口：聊天
        
        Args:
            query: 用户问题
            enable_rag: 是否启用RAG
            num_thought_steps: 思维链步数
        
        Returns:
            str - 最终答案
        """
        self.thought_history = []
        start_time = time.time()
        
        print(f"🧠 [伪Qwen3.5 Plus] 处理中...")
        print(f"🤔 问题: {query[:50]}...")
        
        # Step 1: 问题分析
        analysis = self._analyze_query(query)
        # 保存结构化的analysis，但记录时用字符串
        self._last_analysis = analysis
        self._add_thought(1, "analyze", f"问题分析完成:\n- 意图: {analysis.get('intent', 'unknown')}\n- 类型: {analysis.get('question_type', 'general')}\n- 复杂度: {analysis.get('complexity', 'medium')}")
        
        # Step 2: RAG检索（可选）
        rag_context = ""
        if enable_rag and self.rag and self._needs_rag(analysis):
            print("📚 检索知识中...")
            rag_result = self.rag.retrieve(query)
            rag_context = self._format_rag_context(rag_result)
            self._add_thought(2, "rag", f"检索到 {len(rag_result.chunks)} 条相关知识")
        
        # Step 3-5: 深度思维链推理
        for i in range(num_thought_steps):
            step_num = 3 + i
            thought = self._deep_reasoning(
                query, 
                rag_context, 
                self.thought_history,
                step_num,
                num_thought_steps
            )
            self._add_thought(step_num, "reason", thought)
            print(f"💭 思考步骤 {step_num}/{2+num_thought_steps} 完成")
        
        # Step N: 自我反思/批评
        print("🔍 自我反思中...")
        critique = self._self_critique(query, self.thought_history)
        self._add_thought(2+num_thought_steps, "critic", critique)
        
        # Step N+1: 最终优化输出
        print("✨ 生成最终答案...")
        final_answer = self._generate_final_answer(
            query, 
            rag_context, 
            self.thought_history
        )
        self._add_thought(3+num_thought_steps, "final", final_answer)
        
        elapsed = time.time() - start_time
        print(f"✅ 完成！耗时 {elapsed:.2f}s")
        
        return final_answer
    
    def _analyze_query(self, query: str) -> dict:
        """Step 1: 分析问题"""
        prompt = f"""请分析以下用户问题，用JSON格式输出：

用户问题：{query}

请输出：
{{
    "intent": "用户的真实意图",
    "question_type": "coding|writing|analysis|math|general|other",
    "complexity": "simple|medium|hard",
    "needs_rag": true/false,
    "key_points": ["关键点1", "关键点2"]
}}

只输出JSON，不要其他内容。"""
        
        response = self.llm.chat(prompt, temperature=0.3)
        return self._extract_json(response)
    
    def _needs_rag(self, analysis: Dict) -> bool:
        """判断是否需要RAG"""
        return analysis.get("needs_rag", False)
    
    def _deep_reasoning(
        self, 
        query: str, 
        rag_context: str, 
        previous_thoughts: List[ThoughtStep],
        step_num: int,
        total_steps: int
    ) -> str:
        """深度思维链推理"""
        
        # 构建上下文
        thoughts_str = "\n".join([
            f"[步骤 {t.step_num} - {t.step_type}]\n{t.content}\n"
            for t in previous_thoughts
        ])
        
        prompt = f"""你是一个深度思考的AI助手。请继续思考这个问题。

用户问题：{query}

已有的思考过程：
{thoughts_str}

参考知识：
{rag_context if rag_context else '（无）'}

当前是第 {step_num}/{total_steps} 步思考。

请继续深入思考：
1. 基于之前的思考，继续推进
2. 不要重复之前的内容
3. 考虑不同的角度
4. 提出新的见解

请用清晰、结构化的语言输出你的思考。"""
        
        return self.llm.chat(prompt, temperature=0.7)
    
    def _self_critique(self, query: str, thoughts: List[ThoughtStep]) -> str:
        """自我反思/批评"""
        
        thoughts_str = "\n".join([
            f"[步骤 {t.step_num} - {t.step_type}]\n{t.content}\n"
            for t in thoughts
        ])
        
        prompt = f"""请对以下思考过程进行自我批评和反思：

用户问题：{query}

思考过程：
{thoughts_str}

请回答：
1. 刚才的思考有什么遗漏？
2. 有什么错误或不准确的地方？
3. 可以从哪些角度改进？
4. 还需要考虑什么？

请诚实、具体地指出问题所在。"""
        
        return self.llm.chat(prompt, temperature=0.5)
    
    def _generate_final_answer(
        self, 
        query: str, 
        rag_context: str, 
        thoughts: List[ThoughtStep]
    ) -> str:
        """生成最终答案"""
        
        thoughts_str = "\n".join([
            f"[步骤 {t.step_num} - {t.step_type}]\n{t.content}\n"
            for t in thoughts
        ])
        
        prompt = f"""你是一个专业、友好的AI助手（模仿Qwen3.5 Plus的风格）。

请基于以下所有思考，给用户一个高质量的最终答案：

用户问题：{query}

完整思考过程：
{thoughts_str}

参考知识：
{rag_context if rag_context else '（无）'}

要求：
1. 答案要全面、准确、有深度
2. 语言自然、友好
3. 结构清晰、易读
4. 如果有代码，要规范并带注释
5. 如果是分析，要有理有据
6. 不要暴露你的"思考过程"，只给最终答案

请输出最终答案："""
        
        return self.llm.chat(prompt, temperature=0.8)
    
    def _add_thought(self, step_num: int, step_type: str, content: str):
        """添加思考记录"""
        self.thought_history.append(ThoughtStep(
            step_num=step_num,
            step_type=step_type,
            content=str(content),
            timestamp=time.time()
        ))
    
    def _format_rag_context(self, rag_result: RAGResult) -> str:
        """格式化RAG上下文"""
        if not rag_result.chunks:
            return ""
        
        chunks_str = "\n".join([
            f"[{i+1}] {chunk.get('content', '')[:200]}..."
            for i, chunk in enumerate(rag_result.chunks[:5])  # 最多5条
        ])
        
        return f"""相关知识：
{chunks_str}
来源：{', '.join(rag_result.sources[:3])}"""
    
    def _extract_json(self, text: str) -> Dict:
        """从文本中提取JSON"""
        try:
            # 尝试直接解析
            return json.loads(text)
        except:
            # 尝试找到{...}
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        # 如果解析失败，返回默认值
        return {
            "intent": "unknown",
            "question_type": "general",
            "complexity": "medium",
            "needs_rag": False,
            "key_points": []
        }
    
    def print_thought_trace(self):
        """打印思考过程"""
        print("\n" + "="*60)
        print("🧠 伪Qwen3.5 Plus 思考追踪")
        print("="*60)
        
        for thought in self.thought_history:
            type_emoji = {
                "analyze": "🔍",
                "rag": "📚",
                "reason": "💭",
                "critic": "🎯",
                "final": "✨"
            }.get(thought.step_type, "💡")
            
            print(f"\n{type_emoji} 步骤 {thought.step_num} - {thought.step_type}")
            print(f"   时间: {time.strftime('%H:%M:%S', time.localtime(thought.timestamp))}")
            content_display = thought.content[:800]
            if len(thought.content) > 800:
                content_display += "..."
            print(f"   内容:\n{content_display}\n")
        
        print("="*60 + "\n")
