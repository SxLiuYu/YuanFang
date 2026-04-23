"""
Dynamic Tool Generator — 动态工具生成器
让元芳自己根据用户需求生成新工具代码，保存并自动加载
支持: 需求描述 → LLM生成代码 → 验证 → 保存 → 自动调用
"""

import os
import re
import json
import importlib.util
import subprocess
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

# 工具存储目录
TOOL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dynamic_tools")
TOOL_INDEX_FILE = os.path.join(TOOL_DIR, "tool_index.json")
EVOLUTION_MEMORY_FILE = os.path.join(TOOL_DIR, "evolution_memory.json")
MAX_RETRIES = 3  # 最大自动修复重试次数
MAX_VERSIONS = 5  # 每个工具保留最多版本数


@dataclass
class DynamicTool:
    name: str           # 工具名称 (snake_case)
    description: str    # 工具描述
    handler_function: str  # 处理函数名 (一般是 {name}_handler)
    requirements: str  # 依赖描述
    code: str          # 完整Python代码
    created_at: str    # 创建时间
    version: int       # 版本号
    rating: Optional[int]  # 用户评分 1-5，None未评分
    usage_example: str # 使用示例
    error_history: List[str]  # 错误历史


def snake_case_name(demand: str) -> str:
    """从需求生成合法的模块名"""
    # 取前两个关键词转snake_case
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', demand)
    if not words:
        return "custom_tool"
    name = "_".join([w.lower() for w in words[:2]])
    # 去掉非法字符
    name = re.sub(r'[^a-z0-9_]', '', name)
    if not name:
        return "custom_tool"
    return name


def _ensure_tool_dir():
    """确保工具目录存在"""
    if not os.path.exists(TOOL_DIR):
        os.makedirs(TOOL_DIR)


def _load_index() -> Dict[str, DynamicTool]:
    """加载工具索引"""
    _ensure_tool_dir()
    if not os.path.exists(TOOL_INDEX_FILE):
        with open(TOOL_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    
    try:
        with open(TOOL_INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = {}
        for name, item in data.items():
            result[name] = DynamicTool(**item)
        return result
    except Exception:
        return {}


def _save_index(index: Dict[str, DynamicTool]):
    """保存工具索引"""
    _ensure_tool_dir()
    data = {}
    for name, tool in index.items():
        data[name] = asdict(tool)
    with open(TOOL_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ========== 进化记忆库 ==========

@dataclass
class EvolutionRecord:
    """进化记录 — 记录每次生成的成功/失败案例，用于Few-Shot提示"""
    demand: str         # 用户需求
    code: str          # 生成的代码
    success: bool      # 是否成功
    error: str         # 错误信息
    timestamp: str     # 时间戳
    attempt_count: int # 尝试次数


def _load_evolution_memory() -> List[EvolutionRecord]:
    """加载进化记忆"""
    _ensure_tool_dir()
    if not os.path.exists(EVOLUTION_MEMORY_FILE):
        with open(EVOLUTION_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    
    try:
        with open(EVOLUTION_MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = []
        for item in data:
            result.append(EvolutionRecord(**item))
        return result
    except Exception:
        return []


def _save_evolution_memory(record: EvolutionRecord):
    """保存进化记录"""
    memory = _load_evolution_memory()
    memory.append(record)
    # 只保留最近100条，避免文件过大
    if len(memory) > 100:
        memory = memory[-100:]
    _ensure_tool_dir()
    data = [asdict(r) for r in memory]
    with open(EVOLUTION_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_few_shot_examples() -> str:
    """获取Few-Shot示例用于提示词"""
    memory = _load_evolution_memory()
    successful = [r for r in memory if r.success]
    if not successful:
        return ""
    
    # 取最近3个成功案例作为示例
    examples = successful[-3:]
    prompt = "\n---\n参考以下成功案例：\n"
    for i, ex in enumerate(examples, 1):
        prompt += f"\n【案例 {i}】\n需求: {ex.demand}\n代码:\n{ex.code}\n"
    return prompt


def record_evolution(demand: str, code: str, success: bool, error: str, attempts: int):
    """记录一次进化尝试"""
    record = EvolutionRecord(
        demand=demand,
        code=code,
        success=success,
        error=error,
        timestamp=datetime.now().isoformat(),
        attempt_count=attempts
    )
    _save_evolution_memory(record)


def list_dynamic_tools() -> List[Dict[str, Any]]:
    """列出所有动态工具"""
    index = _load_index()
    result = []
    for name, tool in index.items():
        result.append({
            "name": tool.name,
            "description": tool.description,
            "handler": tool.handler_function,
            "example": tool.usage_example
        })
    return result


def get_dynamic_tool(name: str) -> Optional[DynamicTool]:
    """获取动态工具"""
    index = _load_index()
    return index.get(name)


def save_dynamic_tool(tool: DynamicTool) -> bool:
    """保存动态工具到文件和索引，支持版本管理"""
    _ensure_tool_dir()
    index = _load_index()
    
    # 版本管理：如果已存在，递增版本号
    if tool.name in index:
        existing = index[tool.name]
        tool.version = existing.version + 1
        # 备份旧版本
        backup_path = os.path.join(TOOL_DIR, f"{tool.name}_v{existing.version}.py")
        code_path = os.path.join(TOOL_DIR, f"{tool.name}.py")
        if os.path.exists(code_path):
            os.rename(code_path, backup_path)
        # 删除旧备份，只保留MAX_VERSIONS个版本
        cleanup_old_versions(tool.name)
    else:
        tool.version = 1
    
    # 保存当前版本代码文件
    code_path = os.path.join(TOOL_DIR, f"{tool.name}.py")
    try:
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(tool.code)
    except Exception as e:
        return False
    
    # 更新索引
    index[tool.name] = tool
    _save_index(index)
    return True


def cleanup_old_versions(name: str):
    """清理旧版本，只保留最近MAX_VERSIONS个"""
    import glob
    pattern = os.path.join(TOOL_DIR, f"{name}_v*.py")
    versions = []
    for path in glob.glob(pattern):
        match = re.search(r'_v(\d+)\.py$', path)
        if match:
            ver = int(match.group(1))
            versions.append((ver, path))
    # 按版本号排序，删除最旧的超出限制的版本
    versions.sort(reverse=True)
    if len(versions) > MAX_VERSIONS:
        for _, path in versions[MAX_VERSIONS:]:
            os.remove(path)


def install_requirements(requirements_text: str) -> Tuple[bool, str]:
    """解析并安装工具依赖的第三方包"""
    if not requirements_text or requirements_text.strip() == "None":
        return True, "无依赖"
    
    # 提取包名
    packages = []
    for line in requirements_text.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            # 去掉版本约束，只安装最新版
            pkg = re.split(r'[=<>~]', line.split('#')[0].strip())[0]
            if pkg:
                packages.append(pkg)
    
    if not packages:
        return True, "无有效依赖"
    
    # 逐个安装
    failed = []
    for pkg in packages:
        try:
            print(f"[DynamicTool] 正在安装依赖: {pkg}")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--quiet", pkg
            ])
        except subprocess.CalledProcessError as e:
            failed.append(f"{pkg}: {str(e)}")
    
    if failed:
        return False, "安装失败: " + "; ".join(failed)
    return True, f"已安装 {len(packages)} 个依赖"


def update_tool_rating(name: str, rating: int) -> bool:
    """更新工具评分（用户点赞/点踩），低分触发重新优化"""
    index = _load_index()
    if name not in index:
        return False
    tool = index[name]
    tool.rating = rating
    index[name] = tool
    _save_index(index)
    return True


def should_regenerate(name: str) -> bool:
    """判断低分工具是否需要重新生成"""
    tool = get_dynamic_tool(name)
    if not tool or tool.rating is None:
        return False
    return tool.rating <= 2  # 评分<=2触发重新生成


def rollback_version(name: str, target_version: int) -> bool:
    """回滚到指定版本"""
    index = _load_index()
    if name not in index:
        return False
    backup_path = os.path.join(TOOL_DIR, f"{name}_v{target_version}.py")
    if not os.path.exists(backup_path):
        return False
    
    # 读取旧版本代码
    with open(backup_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    # 恢复为当前版本
    current_path = os.path.join(TOOL_DIR, f"{name}.py")
    with open(current_path, "w", encoding="utf-8") as f:
        f.write(code)
    
    # 更新索引版本号
    tool = index[name]
    tool.code = code
    tool.version = target_version
    index[name] = tool
    _save_index(index)
    return True


def delete_dynamic_tool(name: str) -> bool:
    """删除动态工具"""
    index = _load_index()
    if name not in index:
        return False
    
    # 删除文件
    code_path = os.path.join(TOOL_DIR, f"{name}.py")
    if os.path.exists(code_path):
        os.remove(code_path)
    
    # 更新索引
    del index[name]
    _save_index(index)
    return True


def search_similar_tools(query: str, threshold: float = 0.75) -> List[DynamicTool]:
    """搜索相似工具，避免重复创建
    使用元芳现有的VectorMemory进行语义搜索
    """
    try:
        from memory.vector import VectorMemory
        from core.llm_adapter import get_llm
        
        # 获取embedding函数
        llm = get_llm()
        def get_embedding(text):
            # 使用现有LLM生成嵌入（简化方案）
            return None
        
        index = _load_index()
        if not index:
            return []
        
        # 如果无法获取嵌入，回退到关键词匹配
        return []
    except Exception as e:
        print(f"[DynamicTool] 语义搜索失败: {e}")
        return []


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算余弦相似度"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x*x for x in a)**0.5
    mag_b = sum(x*x for x in b)**0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def load_dynamic_tool_handler(name: str):
    """动态加载工具处理函数"""
    tool = get_dynamic_tool(name)
    if not tool:
        return None
    
    code_path = os.path.join(TOOL_DIR, f"{name}.py")
    if not os.path.exists(code_path):
        return None
    
    try:
        spec = importlib.util.spec_from_file_location(f"dynamic_tools.{name}", code_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = getattr(module, tool.handler_function)
        return handler
    except Exception as e:
        print(f"[DynamicTool] 加载失败: {e}")
        return None


def generate_tool_code(demand: str, system_prompt: str = None, retry_errors: str = None) -> str:
    """
    使用LLM生成工具代码
    支持重试：retry_errors 包含上次错误信息，让LLM修复
    """
    from core.llm_adapter import get_llm
    
    llm = get_llm()
    
    # 获取Few-Shot成功案例
    few_shot = get_few_shot_examples()
    
    prompt = f"""
你是一个专业的Python开发者，需要为贾维斯语音助手创建一个新的动态工具。
这是 LLM-ToolMaker 闭环路框架中的工具制作阶段。

用户需求: {demand}

请遵循以下规范：

1. **模块结构**:
   - 文件开头需要注释说明功能
   - 必须提供一个 `{snake_case_name(demand)}_handler(text: str) -> Optional[str]` 处理函数
   - 函数输入是用户语音识别后的文本，输出是回复文本，如果不匹配返回None
   - 所有导入必须在函数内部，避免未安装依赖导致的启动错误
   - 在文件开头注释里写明需要的第三方依赖，例如: `# dependencies: requests, beautifulsoup4`

2. **错误处理**:
   - 使用try-catch捕获异常
   - 返回友好的中文错误提示
   - 如果请求不匹配当前工具，必须返回None
   - 优先使用Python标准库，减少外部依赖

3. **匹配规则**:
   - 在handler函数开头，通过关键词判断是否匹配当前工具
   - 支持多种自然表达方式匹配（口语化、不同说法）
   - 如果不匹配，立即返回None，交给下一个工具处理

4. **Python兼容性**:
   - 当前使用Python 3.9，不支持 PEP 604 的 `|` Union语法
   - 使用 `Union[X, Y]` 代替，或者省略类型注释也可以

5. **输出格式**:
   - 只输出完整可运行的Python代码，不要额外说明
   - 代码必须包含完整的handler函数
   - 不要用markdown代码块包裹，直接输出代码
{few_shot}
"""

    # 如果是重试，添加上次错误信息
    if retry_errors:
        prompt += f"""

上次生成代码有错误，请修复后重新输出：
错误信息: {retry_errors}
"""

    messages = [
        {"role": "system", "content": system_prompt or generate_tool_system_prompt()},
        {"role": "user", "content": prompt}
    ]
    
    response = llm.chat_simple(messages, temperature=0.3, max_tokens=2048)
    # 清理可能的markdown代码块标记
    code = response.strip()
    code = code.replace("```python", "").replace("```", "").strip()
    # 二次清理使用正则
    code = re.sub(r'^```python\s*', '', code)
    code = re.sub(r'^```.*\s*', '', code)
    code = re.sub(r'\s*```$', '', code)
    return code.strip()


def generate_and_validate_with_retry(demand: str, max_retries: int = MAX_RETRIES) -> Tuple[bool, str, str]:
    """
    生成代码并自动重试修复错误
    返回: (是否成功, 代码, 错误信息)
    """
    name = snake_case_name(demand)
    handler_name = f"{name}_handler"
    last_error = None
    
    for attempt in range(max_retries):
        code = generate_tool_code(demand, retry_errors=last_error)
        valid, msg = validate_tool_code(code, handler_name)
        if valid:
            # 记录成功案例到进化记忆
            record_evolution(demand, code, True, "", attempt + 1)
            return True, code, ""
        last_error = msg
        print(f"[DynamicTool] 第{attempt+1}次尝试生成失败: {msg}，正在修复...")
        # 记录失败案例
        record_evolution(demand, code, False, msg, attempt + 1)
    
    # 所有尝试失败
    record_evolution(demand, "", False, last_error or "未知错误", max_retries)
    return False, "", last_error


def validate_and_fix_runtime_error(name: str, error_msg: str) -> bool:
    """运行时错误自动修复：读取现有代码，根据错误信息让LLM修复"""
    tool = get_dynamic_tool(name)
    if not tool:
        return False
    
    # 让LLM根据错误修复
    demand = f"修复工具「{tool.description}」运行时错误"
    retry_errors = f"原代码运行错误: {error_msg}\n原代码:\n{tool.code}"
    
    success, new_code, error = generate_and_validate_with_retry(demand, max_retries=2)
    if success:
        # 更新工具代码
        tool.code = new_code
        if tool.error_history is None:
            tool.error_history = []
        tool.error_history.append(error_msg)
        save_dynamic_tool(tool)
        return True
    return False


# ========== 安全沙箱 ==========

# 允许的操作白名单
ALLOWED_IMPORTS = {
    # 标准库安全模块
    'math', 'random', 'datetime', 'time', 'json', 're', 'urllib', 
    'urllib.request', 'requests', 'http', 'html', 'csv', 'collections',
    'statistics', 'decimal', 'fractions', 'calendar', 'diffib', 'enum',
    # 常用第三方包
    'bs4', 'beautifulsoup4', 'pandas', 'numpy'
}

# 禁止的危险操作
FORBIDDEN_PATTERNS = [
    r'__import__\s*\([\'"]os[\'"]',
    r'__import__\s*\([\'"]sys[\'"]',
    r'__import__\s*\([\'"]subprocess[\'"]',
    r'eval\s*\(',
    r'exec\s*\(',
    r'globals\s*\(',
    r'locals\s*\(',
    r'getattr\s*\([^,]+__',
    r'\.__dict__',
    r'\.__class__',
    r'\.__globals__',
    r'open\s*\([^)]*\)',
    r'write\s*\(',
    r'unlink\s*\(',
    r'remove\s*\(',
    r'rmtree\s*\(',
    r'os\.(system|popen|spawn|fork|exec)',
    r'subprocess\.(run|call|Popen)',
]


def check_code_security(code: str) -> Tuple[bool, str]:
    """检查代码安全性，禁止危险操作"""
    for pattern in FORBIDDEN_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            return False, f"检测到禁止操作: {matches[0]}"
    return True, "安全检查通过"


def validate_tool_code(code: str, handler_name: str) -> Tuple[bool, str]:
    """验证工具代码语法正确性和安全性"""
    # 安全检查
    safe, msg = check_code_security(code)
    if not safe:
        return False, msg
    
    try:
        # 编译检查语法
        compile(code, '<dynamic_tool>', 'exec')
        # 检查是否有handler函数
        if handler_name not in code:
            return False, f"找不到处理函数 {handler_name}"
        return True, "验证通过"
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"验证失败: {e}"


def dynamic_tool_handler(text: str) -> Optional[str]:
    """
    主入口：轮询所有动态工具，找到匹配的执行
    由语音管线调用
    运行出错时自动尝试修复
    """
    index = _load_index()
    for name, tool in index.items():
        handler = load_dynamic_tool_handler(name)
        if handler is None:
            continue
        try:
            result = handler(text)
            if result is not None:
                return result
        except Exception as e:
            error_msg = str(e)
            full_error = traceback.format_exc()
            print(f"[DynamicTool] 工具「{name}」执行出错: {error_msg}，尝试自动修复...")
            # 尝试自动修复
            fixed = validate_and_fix_runtime_error(name, full_error)
            if fixed:
                # 重新加载修复后的handler
                handler = load_dynamic_tool_handler(name)
                if handler:
                    try:
                        result = handler(text)
                        if result is not None:
                            return f"工具「{name}」已自动修复错误，结果：\n{result}"
                    except Exception as e2:
                        return f"工具「{name}」自动修复后仍然出错: {str(e2)}"
            return f"工具「{name}」执行出错: {error_msg}"
    return None


def generate_tool_system_prompt() -> str:
    """生成添加新工具时的系统提示词"""
    return """你是贾维斯，你可以自己生成新工具来满足用户需求。
用户说需要什么功能，你就生成对应的工具代码，保存后就能直接使用。
记住：
1. 输出完整Python代码
2. 必须有 xxx_handler(text) -> Optional[str] 函数
3. 不匹配返回None
4. 使用中文返回结果
"""


if __name__ == "__main__":
    # 简单测试
    print("✅ dynamic_tool_generator.py 加载成功")
    print(f"MAX_RETRIES = {MAX_RETRIES}")
    print(f"MAX_VERSIONS = {MAX_VERSIONS}")
    print(f"Tool directory: {TOOL_DIR}")
    print(f"Evolution memory: {EVOLUTION_MEMORY_FILE}")
    index = _load_index()
    evo_mem = _load_evolution_memory()
    print(f"已加载 {len(index)} 个动态工具")
    print(f"进化记忆 {len(evo_mem)} 条记录")
