#!/usr/bin/env python3
"""
伪Qwen3.5 Plus 完整版
- 问题分析
- RAG知识检索（可选）
- 深度思维链推理（3-5步）
- 自我反思/批评
- 最终优化输出
"""

from typing import List, Dict, Any, Optional
import json
import time
from dataclasses import dataclass


@dataclass
class ThoughtStep:
    """思考步骤"""
    step_num: int
    step_type: str  # "analyze", "rag", "reason", "critic", "final"
    content: str
    timestamp: float


@dataclass
class RAGChunk:
    """RAG检索结果块"""
    content: str
    source: str
    score: float = 0.0


@dataclass
class RAGResult:
    """RAG检索结果"""
    query: str
    chunks: List[RAGChunk]
    sources: List[str]


class SimpleRAGRetriever:
    """简单的RAG检索器（示例）"""
    
    def __init__(self, knowledge_base: Dict[str, str] = None):
        """
        初始化RAG检索器
        
        Args:
            knowledge_base: 知识库，格式: {topic: content}
        """
        self.knowledge_base = knowledge_base or {}
    
    def retrieve(self, query: str, top_k: int = 3) -> RAGResult:
        """
        简单的关键词匹配检索（实际可以用向量检索）
        
        Args:
            query: 查询
            top_k: 返回前k个结果
        
        Returns:
            RAGResult
        """
        chunks = []
        
        # 简单的关键词匹配
        for topic, content in self.knowledge_base.items():
            if any(keyword in query.lower() or keyword in topic.lower() 
                   for keyword in query.lower().split()):
                chunks.append(RAGChunk(
                    content=content,
                    source=topic,
                    score=1.0
                ))
        
        # 简单截断
        chunks = chunks[:top_k]
        
        return RAGResult(
            query=query,
            chunks=chunks,
            sources=[c.source for c in chunks]
        )


class PseudoQwen35Plus:
    """伪Qwen3.5 Plus核心引擎 - 完整版"""
    
    def __init__(self, llm_client, rag_retriever=None):
        """
        Args:
            llm_client: LLM客户端（需要有chat方法）
            rag_retriever: RAG检索器（可选）
        """
        self.llm = llm_client
        self.rag = rag_retriever
        self.thought_history: List[ThoughtStep] = []
        self._last_analysis = None
    
    def chat(
        self, 
        query: str, 
        enable_rag: bool = True, 
        num_thought_steps: int = 3,
        enable_self_critique: bool = True
    ) -> str:
        """
        主入口：聊天
        
        Args:
            query: 用户问题
            enable_rag: 是否启用RAG
            num_thought_steps: 思维链步数
            enable_self_critique: 是否启用自我反思
        
        Returns:
            str - 最终答案
        """
        self.thought_history = []
        start_time = time.time()
        
        print(f"🧠 [伪Qwen3.5 Plus] 处理中...")
        print(f"🤔 问题: {query[:60]}...")
        
        # Step 1: 问题分析
        analysis = self._analyze_query(query)
        self._last_analysis = analysis
        self._add_thought(1, "analyze", f"""问题分析完成:
- 意图: {analysis.get('intent', 'unknown')}
- 类型: {analysis.get('question_type', 'general')}
- 复杂度: {analysis.get('complexity', 'medium')}
- 需要RAG: {'是' if analysis.get('needs_rag', False) else '否'}""")
        
        # Step 2: RAG检索（可选）
        rag_context = ""
        if enable_rag and self.rag and analysis.get('needs_rag', False):
            print("📚 检索知识中...")
            rag_result = self.rag.retrieve(query)
            rag_context = self._format_rag_context(rag_result)
            self._add_thought(2, "rag", f"检索到 {len(rag_result.chunks)} 条相关知识")
        
        # Step 3-N: 深度思维链推理
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
        
        # Step N+1: 自我反思/批评（可选）
        if enable_self_critique:
            print("🔍 自我反思中...")
            critique = self._self_critique(query, self.thought_history, rag_context)
            self._add_thought(2+num_thought_steps, "critic", critique)
        
        # Step N+2: 最终优化输出
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
    "intent": "用户的真实意图（1-2句话）",
    "question_type": "coding|writing|analysis|math|general|other",
    "complexity": "simple|medium|hard",
    "needs_rag": true/false,
    "key_points": ["关键点1", "关键点2", "关键点3"]
}}

只输出JSON，不要其他内容。"""
        
        response = self.llm.chat(prompt, temperature=0.3, max_tokens=512)
        return self._extract_json(response)
    
    def _deep_reasoning(
        self, 
        query: str, 
        rag_context: str, 
        previous_thoughts: List[ThoughtStep],
        step_num: int,
        total_steps: int
    ) -> str:
        """深度思维链推理"""
        
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
5. 如果是编程问题，考虑具体实现

请用清晰、结构化的语言输出你的思考。"""
        
        return self.llm.chat(prompt, temperature=0.7, max_tokens=1024)
    
    def _self_critique(
        self, 
        query: str, 
        thoughts: List[ThoughtStep],
        rag_context: str
    ) -> str:
        """自我反思/批评"""
        
        thoughts_str = "\n".join([
            f"[步骤 {t.step_num} - {t.step_type}]\n{t.content}\n"
            for t in thoughts
        ])
        
        prompt = f"""请对以下思考过程进行自我批评和反思：

用户问题：{query}

思考过程：
{thoughts_str}

参考知识：
{rag_context if rag_context else '（无）'}

请诚实地回答：
1. 刚才的思考有什么遗漏？
2. 有什么错误或不准确的地方？
3. 可以从哪些角度改进？
4. 还需要考虑什么？
5. 如果是代码，有没有边界情况没考虑？

请具体、详细地指出问题所在。"""
        
        return self.llm.chat(prompt, temperature=0.5, max_tokens=768)
    
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
7. 适当使用Markdown格式

请输出最终答案："""
        
        return self.llm.chat(prompt, temperature=0.8, max_tokens=2048)
    
    def _format_rag_context(self, rag_result: RAGResult) -> str:
        """格式化RAG上下文"""
        if not rag_result.chunks:
            return ""
        
        chunks_str = "\n".join([
            f"[{i+1}] 来源: {chunk.source}\n   内容: {chunk.content[:300]}..."
            for i, chunk in enumerate(rag_result.chunks[:5])
        ])
        
        return f"""相关知识：
{chunks_str}"""
    
    def _extract_json(self, text: str) -> Dict:
        """从文本中提取JSON"""
        try:
            return json.loads(text)
        except:
            import re
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        return {
            "intent": "unknown",
            "question_type": "general",
            "complexity": "medium",
            "needs_rag": False,
            "key_points": []
        }
    
    def _add_thought(self, step_num: int, step_type: str, content: str):
        """添加思考记录"""
        self.thought_history.append(ThoughtStep(
            step_num=step_num,
            step_type=step_type,
            content=str(content),
            timestamp=time.time()
        ))
    
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
            content_display = thought.content[:1000]
            if len(thought.content) > 1000:
                content_display += "..."
            print(f"   内容:\n{content_display}\n")
        
        print("="*60 + "\n")
