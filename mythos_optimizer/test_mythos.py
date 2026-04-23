"""
Mythos 优化模块测试
"""
import pytest
from mythos_optimizer import (
    MythosConfig,
    RecurrentDepthReasoner,
    ExpertRouter,
    AdaptiveComputationTimeController,
    MythosLLMAdapter,
    Expert,
)


# ============================================================
# 配置测试
# ============================================================

def test_config_defaults():
    """测试默认配置"""
    config = MythosConfig()
    assert config.use_recurrent_depth is True
    assert config.use_moe is True
    assert config.max_thinking_steps == 10
    assert config.min_reasoning_steps == 2
    assert config.n_experts_per_tok == 4
    assert config.n_shared_experts == 2
    assert config.act_mode == "balanced"
    assert config.early_termination_threshold == 0.7


def test_config_custom():
    """测试自定义配置"""
    config = MythosConfig(
        max_thinking_steps=15,
        act_mode="conservative",
        use_moe=False,
    )
    assert config.max_thinking_steps == 15
    assert config.act_mode == "conservative"
    assert config.use_moe is False


# ============================================================
# 专家路由测试
# ============================================================

def test_router_initialization():
    """测试路由器初始化"""
    config = MythosConfig()
    router = ExpertRouter(config)
    assert len(router.list_experts()) > 0


def test_router_route():
    """测试路由功能"""
    config = MythosConfig()
    router = ExpertRouter(config)
    
    query = "如何优化Python代码性能？"
    decision = router.route(query)
    
    assert decision.query == query
    assert len(decision.selected_experts) > 0
    assert len(decision.shared_experts) > 0
    assert len(decision.routing_scores) > 0


def test_router_add_expert():
    """测试添加专家"""
    config = MythosConfig()
    router = ExpertRouter(config)
    
    initial_count = len(router.list_experts())
    
    new_expert = Expert(
        id="test_expert",
        name="测试专家",
        specialty=["测试", "test"],
    )
    router.add_expert(new_expert)
    
    assert len(router.list_experts()) == initial_count + 1
    assert router.get_expert("test_expert") is not None


def test_router_build_prompt():
    """测试专家提示词构建"""
    config = MythosConfig()
    router = ExpertRouter(config)
    
    experts = router.list_experts()[:2]
    expert_ids = [e.id for e in experts]
    
    prompt = router.build_expert_prompt(expert_ids, base_prompt="测试基础提示词")
    
    assert "测试基础提示词" in prompt
    for expert in experts:
        assert expert.name in prompt


# ============================================================
# 自适应计算时间测试
# ============================================================

def test_act_initialization():
    """测试ACT控制器初始化"""
    config = MythosConfig()
    act_controller = AdaptiveComputationTimeController(config)
    assert act_controller is not None


def test_act_complexity_estimation():
    """测试复杂度评估"""
    config = MythosConfig()
    act_controller = AdaptiveComputationTimeController(config)
    
    # 简单问题
    simple_query = "你好"
    simple_estimate = act_controller.estimate_complexity(simple_query)
    assert simple_estimate.complexity_score < 0.5
    assert simple_estimate.difficulty_level in ["simple", "medium"]
    
    # 复杂问题
    complex_query = "设计一个微服务架构，包含用户服务、订单服务、支付服务，需要考虑高可用和数据一致性。"
    complex_estimate = act_controller.estimate_complexity(complex_query)
    assert complex_estimate.complexity_score > 0.3
    assert complex_estimate.estimated_steps > simple_estimate.estimated_steps


def test_act_cache():
    """测试缓存功能"""
    config = MythosConfig()
    act_controller = AdaptiveComputationTimeController(config)
    
    query = "缓存测试查询"
    
    # 第一次评估
    estimate1 = act_controller.estimate_complexity(query, use_cache=False)
    
    # 第二次评估（使用缓存）
    estimate2 = act_controller.estimate_complexity(query, use_cache=True)
    
    # 应该是同一个对象
    assert estimate1 is not estimate2  # 因为 use_cache=False 强制重新计算
    assert estimate1.complexity_score == estimate2.complexity_score
    
    # 再试一次，这次使用缓存
    estimate3 = act_controller.estimate_complexity(query, use_cache=True)
    estimate4 = act_controller.estimate_complexity(query, use_cache=True)
    assert estimate3 is estimate4  # 缓存命中
    
    # 清空缓存
    act_controller.clear_cache()


def test_act_optimal_steps():
    """测试最优步数计算"""
    config = MythosConfig()
    act_controller = AdaptiveComputationTimeController(config)
    
    query = "测试查询"
    steps = act_controller.get_optimal_steps(query)
    
    assert steps >= config.min_reasoning_steps
    assert steps <= config.max_thinking_steps


# ============================================================
# 循环深度推理测试
# ============================================================

def test_reasoner_initialization():
    """测试推理器初始化"""
    config = MythosConfig()
    
    def mock_llm(prompt, **kwargs):
        return "模拟回答"
    
    reasoner = RecurrentDepthReasoner(config, mock_llm)
    assert reasoner is not None


# ============================================================
# 主适配器测试
# ============================================================

def test_adapter_initialization():
    """测试适配器初始化"""
    config = MythosConfig()
    
    def mock_llm(prompt, **kwargs):
        return "模拟回答"
    
    adapter = MythosLLMAdapter(
        config=config,
        llm_call_fn=mock_llm,
    )
    assert adapter is not None


def test_adapter_chat():
    """测试适配器聊天功能"""
    config = MythosConfig(auto_use_depth=False)
    
    def mock_llm(prompt, **kwargs):
        return f"回答: {prompt}"
    
    adapter = MythosLLMAdapter(
        config=config,
        llm_call_fn=mock_llm,
    )
    
    response = adapter.chat("测试消息")
    assert "测试消息" in response


def test_adapter_config_methods():
    """测试适配器配置方法"""
    config = MythosConfig()
    
    def mock_llm(prompt, **kwargs):
        return "模拟回答"
    
    adapter = MythosLLMAdapter(
        config=config,
        llm_call_fn=mock_llm,
    )
    
    # 测试启用/禁用深度思考
    adapter.disable_depth()
    assert adapter.config.use_recurrent_depth is False
    
    adapter.enable_depth()
    assert adapter.config.use_recurrent_depth is True
    
    # 测试启用/禁用专家路由
    adapter.disable_moe()
    assert adapter.config.use_moe is False
    
    adapter.enable_moe()
    assert adapter.config.use_moe is True
    
    # 测试ACT模式
    adapter.set_act_mode("conservative")
    assert adapter.config.act_mode == "conservative"
    
    adapter.set_act_mode("balanced")
    assert adapter.config.act_mode == "balanced"


def test_adapter_expert_management():
    """测试适配器专家管理"""
    config = MythosConfig()
    
    def mock_llm(prompt, **kwargs):
        return "模拟回答"
    
    adapter = MythosLLMAdapter(
        config=config,
        llm_call_fn=mock_llm,
    )
    
    initial_count = len(adapter.list_experts())
    
    new_expert = Expert(
        id="adapter_test_expert",
        name="适配器测试专家",
        specialty=["适配器", "测试"],
    )
    adapter.add_expert(new_expert)
    
    assert len(adapter.list_experts()) == initial_count + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
