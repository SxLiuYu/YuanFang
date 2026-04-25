#!/usr/bin/env python3
"""Mock版LLM客户端 - 用于测试伪Qwen3.5 Plus流程"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class SimpleLLMClient:
    """Mock版LLM客户端 - 用于测试流程"""
    
    def __init__(self, model="Mock-Qwen3.5-4B"):
        self.model = model
        print(f"🔧 初始化Mock LLM客户端")
        print(f"   模型: {self.model} (模拟)")
    
    def chat(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Mock聊天 - 返回预设的回复"""
        
        # 模拟网络延迟
        delay = 0.5 + random.random() * 1.0
        time.sleep(delay)
        
        # 根据prompt返回不同的mock回复（注意：顺序很重要！）
        if "请输出最终答案" in prompt or "只给最终答案" in prompt or "模仿Qwen3.5 Plus的风格" in prompt:
            # 最终答案的回复（优先级最高！）
            return '''# Python代码性能优化指南

## 1. 使用profiler找到瓶颈
```python
import cProfile
cProfile.run('your_function()')
```

## 2. 优化数据结构
- 用`set`代替`list`做成员检查
- 用`collections.defaultdict`
- 用`itertools`避免中间列表

## 3. 使用JIT编译器
```python
from numba import jit

@jit(nopython=True)
def fast_function(x):
    return x * x
```

## 4. 其他技巧
- 使用`__slots__`节省内存
- 用`numpy`向量化运算
- 避免在循环里做重复计算

希望这些方法能帮到你！'''
        
        elif "JSON格式" in prompt or "intent" in prompt.lower() or "question_type" in prompt.lower():
            # 问题分析的回复
            return '''{
    "intent": "用户想了解如何优化Python代码",
    "question_type": "coding",
    "complexity": "medium",
    "needs_rag": false,
    "key_points": ["Python性能优化", "代码示例"]
}'''
        
        elif "自我批评" in prompt or "遗漏" in prompt:
            # 自我反思的回复
            return '''1. 刚才的思考遗漏了内存优化方面
2. 没有提到PyPy JIT编译器
3. 缺少profiling工具的具体使用示例
4. 可以补充C扩展和Cython的内容
5. 建议增加性能测试基准对比'''
        
        elif "基于之前的思考" in prompt or "继续推进" in prompt:
            # 深度思考的回复
            return '''让我继续深入分析...

从Python性能优化的角度看，我们还可以考虑：

1. **算法层面优化**：
   - 时间复杂度：O(n²) → O(n log n)
   - 空间复杂度：避免不必要的内存分配

2. **IO优化**：
   - 批量读写代替单条
   - 使用缓冲
   - 异步IO（asyncio）

3. **并发/并行**：
   - multiprocessing（CPU密集）
   - threading/asyncio（IO密集）

这些是更深层次的优化方向。'''
        
        elif "介绍一下自己" in prompt:
            return "你好！我是伪Qwen3.5 Plus，一个用思维链+自我反思增强的AI助手！"
        
        else:
            # 通用的深度思考回复
            return f'''让我思考一下这个问题...

首先，我需要理解问题的核心。然后从几个角度分析：
1. 技术可行性
2. 实现复杂度
3. 性能影响
4. 用户体验

基于以上分析，我认为可以这样来处理...'''


def test_client():
    """测试Mock客户端"""
    print("="*60)
    print("🧪 测试Mock LLM客户端")
    print("="*60)
    
    client = SimpleLLMClient()
    
    print("\n1️⃣  测试简单对话...")
    response = client.chat("你好，请介绍一下自己")
    print(f"   回复: {response[:80]}...")
    
    print("\n2️⃣  测试问题分析...")
    response = client.chat("请分析这个问题，用JSON格式输出")
    print(f"   回复: {response[:100]}...")
    
    print("\n✅ Mock客户端测试完成！")
    return client


if __name__ == '__main__':
    test_client()
