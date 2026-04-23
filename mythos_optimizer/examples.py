"""
Mythos 优化模块使用示例
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import List

# 配置日志
logging.basicConfig(level=logging.INFO)

# ============================================================
# 示例 1: 基本使用（需要 LLM）
# ============================================================

def example_basic_usage():
    """
    基本使用示例
    
    注意：需要实际的 LLM 后端才能运行
    """
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    from mythos_optimizer import MythosLLMAdapter, MythosConfig
    
    # 创建配置
    config = MythosConfig(
        use_recurrent_depth=True,
        use_moe=True,
        max_thinking_steps=8,
        n_experts_per_tok=4,
        act_mode="balanced",
    )
    
    # 创建适配器（需要提供 LLM 后端）
    # 方式 1: 使用 llm_call_fn
    def mock_llm_call(prompt: str, **kwargs) -> str:
        """模拟 LLM 调用（示例用）"""
        return f"这是对 '{prompt[:30]}...' 的模拟回答"
    
    adapter = MythosLLMAdapter(
        config=config,
        llm_call_fn=mock_llm_call,
    )
    
    # 直接使用（透明代理）
    response = adapter.chat("你好，世界")
    print(f"直接调用: {response}")
    
    print("\n✅ 示例 1 完成\n")


# ============================================================
# 示例 2: 组件单独使用
# ============================================================

def example_component_usage():
    """
    组件单独使用示例
    
    展示如何单独使用各个核心组件
    """
    print("=" * 60)
    print("示例 2: 组件单独使用")
    print("=" * 60)
    
    from mythos_optimizer import (
        MythosConfig,
        ExpertRouter,
        AdaptiveComputationTimeController,
    )
    
    config = MythosConfig()
    
    # 1. 专家路由
    print("\n--- 专家路由示例 ---")
    router = ExpertRouter(config)
    
    # 列出专家
    print("可用专家:")
    for expert in router.list_experts():
        shared = " [共享]" if expert.is_shared else ""
        print(f"  - {expert.name}{shared}: {', '.join(expert.specialty)}")
    
    # 路由一个查询
    query = "如何优化Python代码的性能？"
    decision = router.route(query)
    print(f"\n查询: {query}")
    print(f"选择的专家: {decision.selected_experts}")
    print(f"共享专家: {decision.shared_experts}")
    print(f"路由专家: {decision.routed_experts}")
    
    # 2. 自适应计算时间控制器
    print("\n--- 自适应计算时间示例 ---")
    act_controller = AdaptiveComputationTimeController(config)
    
    # 测试不同复杂度的查询
    test_queries = [
        "你好",
        "什么是Python？",
        "如何优化Python性能？",
        "设计一个微服务架构，包含用户服务、订单服务、支付服务，需要考虑高可用和数据一致性。",
    ]
    
    for q in test_queries:
        estimate = act_controller.estimate_complexity(q)
        print(f"\n  查询: {q[:30]}...")
        print(f"    复杂度: {estimate.complexity_score:.2f} ({estimate.difficulty_level})")
        print(f"    估计步数: {estimate.estimated_steps}")
        print(f"    估计 tokens: {estimate.estimated_tokens}")
    
    print("\n✅ 示例 2 完成\n")


# ============================================================
# 示例 3: 添加自定义专家
# ============================================================

def example_custom_experts():
    """
    添加自定义专家示例
    """
    print("=" * 60)
    print("示例 3: 自定义专家")
    print("=" * 60)
    
    from mythos_optimizer import MythosConfig, ExpertRouter, Expert
    
    config = MythosConfig()
    router = ExpertRouter(config)
    
    # 添加自定义专家
    custom_experts = [
        Expert(
            id="game_dev",
            name="游戏开发专家",
            specialty=["游戏", "unity", "unreal", "gamedev"],
            description="专注于游戏开发的专家",
        ),
        Expert(
            id="cooking",
            name="烹饪专家",
            specialty=["烹饪", "食谱", "美食", "cooking"],
            description="专注于烹饪和美食的专家",
        ),
    ]
    
    for expert in custom_experts:
        router.add_expert(expert)
        print(f"添加专家: {expert.name}")
    
    # 测试路由
    queries = [
        "如何用Unity做一个2D游戏？",
        "红烧肉怎么做最好吃？",
    ]
    
    for query in queries:
        decision = router.route(query)
        print(f"\n查询: {query}")
        print(f"选择专家: {decision.selected_experts}")
    
    print("\n✅ 示例 3 完成\n")


# ============================================================
# 示例 4: 配置定制
# ============================================================

def example_config_customization():
    """
    配置定制示例
    """
    print("=" * 60)
    print("示例 4: 配置定制")
    print("=" * 60)
    
    from mythos_optimizer import MythosConfig, MythosLLMAdapter
    
    # 场景 1: 保守模式 - 更深入的思考，更高质量
    print("\n--- 保守模式配置 ---")
    conservative_config = MythosConfig(
        use_recurrent_depth=True,
        use_moe=True,
        max_thinking_steps=12,
        min_reasoning_steps=4,
        n_experts_per_tok=6,
        act_mode="conservative",
        early_termination_threshold=0.85,
    )
    print(f"最大思考步数: {conservative_config.max_thinking_steps}")
    print(f"最少思考步数: {conservative_config.min_reasoning_steps}")
    print(f"每轮专家数: {conservative_config.n_experts_per_tok}")
    print(f"ACT 模式: {conservative_config.act_mode}")
    print(f"早停阈值: {conservative_config.early_termination_threshold}")
    
    # 场景 2: 激进模式 - 快速响应，低延迟
    print("\n--- 激进模式配置 ---")
    aggressive_config = MythosConfig(
        use_recurrent_depth=True,
        use_moe=True,
        max_thinking_steps=4,
        min_reasoning_steps=1,
        n_experts_per_tok=2,
        act_mode="aggressive",
        early_termination_threshold=0.6,
    )
    print(f"最大思考步数: {aggressive_config.max_thinking_steps}")
    print(f"最少思考步数: {aggressive_config.min_reasoning_steps}")
    print(f"每轮专家数: {aggressive_config.n_experts_per_tok}")
    print(f"ACT 模式: {aggressive_config.act_mode}")
    
    # 场景 3: 纯 MoE 模式 - 不使用深度思考，只使用专家路由
    print("\n--- 纯 MoE 模式配置 ---")
    moe_only_config = MythosConfig(
        use_recurrent_depth=False,
        use_moe=True,
        n_experts_per_tok=4,
    )
    print(f"使用深度思考: {moe_only_config.use_recurrent_depth}")
    print(f"使用专家路由: {moe_only_config.use_moe}")
    
    # 场景 4: 纯深度思考模式 - 不使用 MoE
    print("\n--- 纯深度思考模式配置 ---")
    depth_only_config = MythosConfig(
        use_recurrent_depth=True,
        use_moe=False,
        max_thinking_steps=8,
    )
    print(f"使用深度思考: {depth_only_config.use_recurrent_depth}")
    print(f"使用专家路由: {depth_only_config.use_moe}")
    
    print("\n✅ 示例 4 完成\n")


# ============================================================
# 主运行函数
# ============================================================

def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("🧠 Mythos 优化模块 - 使用示例")
    print("=" * 60 + "\n")
    
    # 运行示例（需要 LLM 的示例注释掉）
    # example_basic_usage()
    example_component_usage()
    example_custom_experts()
    example_config_customization()
    
    print("=" * 60)
    print("🎉 所有示例运行完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
