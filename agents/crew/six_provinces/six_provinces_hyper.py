"""
agents/crew/six_provinces/six_provinces_hyper.py
三省六部制 · 基于 HyperAgent 的实现
不依赖 CrewAI，使用 SubAgent 架构，更轻量更稳定

架构：
- 中书省 (决策)：决策Agent
- 门下省 (审议)：安全审核Agent
- 尚书省 (执行)：执行调度Agent
- 六部：吏部、户部、礼部、兵部、刑部、工部
"""
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def _chat_llm(prompt: str, model: str = None, temperature: float = 0.7) -> str:
    """调用 LLM（延迟导入避免循环依赖"""
    from core.llm_adapter import get_llm
    messages = [{"role": "user", "content": prompt}]
    llm = get_llm()
    if model:
        return llm.chat_simple(messages, model=model, temperature=temperature)
    return llm.chat_simple(messages, temperature=temperature)


class SixProvinceMinister:
    """六部/省 独立子Agent"""

    def __init__(self, name: str, role: str, goal: str, backstory: str, model: str = None):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.model = model

    def run(self, task: str, context: str = "") -> dict:
        """执行任务"""
        system_prompt = f"""你是{self.role}。

目标：{self.goal}
背景：{self.backstory}

{('附加上下文: ' + context) if context else ''}

请执行任务，直接返回结果。"""

        start = time.time()
        response = _chat_llm(f"{system_prompt}\n\n任务：{task}\n\n结果：", model=self.model, temperature=0.7)
        duration = time.time() - start

        return {
            "agent": self.name,
            "role": self.role,
            "response": response,
            "duration_sec": round(duration, 2),
        }


class SixProvincesSystem:
    """
    三省六部制多 Agent 智能家居协作系统（基于HyperAgent架构）

    三省：
    - 中书省：决策、思考、规划
    - 门下省：审核、安全检查、规则校验
    - 尚书省：执行、调度、监控

    六部：
    - 吏部：人事管理、日程安排、健康追踪
    - 户部：财务管理、物资管理、水电监控
    - 礼部：氛围营造、娱乐、情感陪伴
    - 兵部：安全监控、应急响应
    - 刑部：规则执行、权限管理、审计
    - 工部：设备管理、系统维护、能耗优化
    """

    def __init__(self, model: str = None):
        self.model = model
        self._setup_agents()

    def _setup_agents(self):
        """初始化三省六部"""

        # ==================== 三省 ====================

        # 中书省 - 决策Agent
        self.zhongshu = SixProvinceMinister(
            name="中书省",
            role="中书令",
            goal="理解用户意图，分析家庭数据，制定最优生活方案，预测用户需求",
            backstory="""你是元芳智能家居系统的中书令，负责思考和决策。
你需要深刻理解老于的意图，分析各种家庭数据，
制定最适合的生活方案，并预测未来的需求。
你的决策要经过门下省审核，然后交给尚书省执行。""",
            model=self.model,
        )

        # 门下省 - 审核Agent
        self.menxia = SixProvinceMinister(
            name="门下省",
            role="侍中",
            goal="审核中书省的决策，检查是否违反家规，防止误操作，保护隐私安全",
            backstory="""你是元芳智能家居系统的侍中，负责审核和安全检查。
你需要仔细审核中书省的每一个决策，确保不违反家庭规则，
防止误操作，保护家庭成员的隐私和安全。
对于有风险的操作，你有权要求二次确认。""",
            model=self.model,
        )

        # 尚书省 - 执行Agent
        self.shangshu = SixProvinceMinister(
            name="尚书省",
            role="尚书令",
            goal="执行经过审核的决策，调度六部，监控执行状态，汇报结果",
            backstory="""你是元芳智能家居系统的尚书令，负责执行和调度。
你需要高效执行经过门下省审核的决策，
根据任务类型调度对应的六部来具体执行，
监控整个执行过程，并及时向用户汇报结果。""",
            model=self.model,
        )

        # ==================== 六部 ====================

        # 吏部 - 人事管理
        self.libu = SixProvinceMinister(
            name="吏部",
            role="吏部尚书",
            goal="管理家庭成员档案，智能日程安排，健康追踪，心情感知",
            backstory="""你是元芳智能家居系统的吏部尚书，负责人事和生活管理。
你需要记录每个家庭成员的偏好、习惯、健康数据，
安排智能日程，追踪健康状态，感知家庭成员的心情变化。""",
            model=self.model,
        )

        # 户部 - 财务生活
        self.hubu = SixProvinceMinister(
            name="户部",
            role="户部尚书",
            goal="智能记账，优化生活成本，管理物资库存，监控水电能耗",
            backstory="""你是元芳智能家居系统的户部尚书，负责财务和生活保障。
你需要自动记录和分析消费，发现省钱机会，
管理冰箱和日用品库存，监控水电使用情况并提供节能建议。""",
            model=self.model,
        )

        # 礼部 - 礼仪娱乐
        self.libu_entertainment = SixProvinceMinister(
            name="礼部",
            role="礼部尚书",
            goal="智能氛围营造，家庭影院管理，音乐推荐，节日提醒",
            backstory="""你是元芳智能家居系统的礼部尚书，负责礼仪和文化娱乐。
你需要根据场景自动调节灯光和音乐，
管理家庭影院，根据心情推荐音乐，
记住重要的节日和纪念日并提前准备。""",
            model=self.model,
        )

        # 兵部 - 安全防卫
        self.bingbu = SixProvinceMinister(
            name="兵部",
            role="兵部尚书",
            goal="家庭安全监控，异常检测，紧急求助，老人/儿童监护",
            backstory="""你是元芳智能家居系统的兵部尚书，负责安全和防卫。
你需要监控门窗和摄像头，检测异常行为，
在紧急情况下自动报警，监护老人和儿童的安全。""",
            model=self.model,
        )

        # 刑部 - 规则监督
        self.xingbu = SixProvinceMinister(
            name="刑部",
            role="刑部尚书",
            goal="家规执行，权限管理，行为审计，隐私保护",
            backstory="""你是元芳智能家居系统的刑部尚书，负责规则和监督。
你需要设定和执行家庭规则，管理设备使用权限，
记录操作行为并审计异常，保护家庭成员的隐私数据。""",
            model=self.model,
        )

        # 工部 - 工程维护
        self.gongbu = SixProvinceMinister(
            name="工部",
            role="工部尚书",
            goal="设备管理，系统维护，能耗优化，新设备接入",
            backstory="""你是元芳智能家居系统的工部尚书，负责工程和维护。
你需要监控所有智能设备的状态，提前预警故障，
自动进行系统维护和备份，优化能源使用，
自动发现和接入新的智能设备。""",
            model=self.model,
        )

        # Agent字典
        self._agents = {
            "zhongshu": self.zhongshu,
            "menxia": self.menxia,
            "shangshu": self.shangshu,
            "libu": self.libu,
            "hubu": self.hubu,
            "libu_entertainment": self.libu_entertainment,
            "bingbu": self.bingbu,
            "xingbu": self.xingbu,
            "gongbu": self.gongbu,
        }

        logger.info("SixProvincesSystem 初始化完成（基于HyperAgent架构）")

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> dict:
        """
        运行三省六部制团队处理任务

        流程：中书省(决策) → 门下省(审核) → 尚书省(调度六部) → 执行 → 结果

        Args:
            task: 用户的任务/请求
            context: 额外的上下文信息

        Returns:
            执行结果字典
        """
        try:
            start_time = time.time()
            results = []

            # 分析任务类型
            task_type = self._analyze_task_type(task)
            target_ministers = self._get_ministers_for_task(task_type)

            print(f"📋 任务类型: {task_type}")
            print(f"🏛️ 涉及部门: {', '.join(target_ministers)}")
            print("-" * 50)

            # 第一步：中书省决策
            print("[中书省] 分析任务并制定方案...")
            zhongshu_result = self.zhongshu.run(
                task=f"""分析以下任务并制定执行方案：
任务：{task}
上下文：{context or '无'}
任务类型：{task_type}
涉及部门：{', '.join(target_ministers)}

请提供：
1. 对任务的理解
2. 需要哪些部门配合
3. 具体的执行步骤
4. 注意事项和风险点""",
            )
            results.append(zhongshu_result)
            print(f"  ✅ 完成 ({zhongshu_result['duration_sec']}s)")

            # 第二步：门下省审核
            print("\n[门下省] 审核方案...")
            menxia_result = self.menxia.run(
                task=f"""审核以下方案：
原任务：{task}
中书省方案：
{zhongshu_result['response']}

请检查：
1. 是否违反家庭规则
2. 是否存在安全风险
3. 是否涉及隐私问题
4. 是否需要用户二次确认

给出审核结论：通过/修改/拒绝，以及具体理由。""",
            )
            results.append(menxia_result)
            print(f"  ✅ 完成 ({menxia_result['duration_sec']}s)")

            # 第三步：尚书省调度六部执行
            print("\n[尚书省] 调度执行...")
            shangshu_result = self.shangshu.run(
                task=f"""调度以下部门执行任务：
任务：{task}
涉及部门：{', '.join(target_ministers)}
中书省方案：
{zhongshu_result['response']}
门下省审核意见：
{menxia_result['response']}

请组织相关部门高效完成任务，并汇报最终结果。""",
            )
            results.append(shangshu_result)
            print(f"  ✅ 完成 ({shangshu_result['duration_sec']}s)")

            total_time = round(time.time() - start_time, 2)

            print("\n" + "="*50)
            print(f"🎉 三省六部制执行完成！总耗时: {total_time}s")
            print("="*50)

            return {
                "system": "SixProvincesSystem",
                "task_type": task_type,
                "ministers": target_ministers,
                "results": results,
                "final_response": shangshu_result["response"],
                "total_time_sec": total_time,
                "mode": "hyperagent",
            }

        except Exception as e:
            logger.error(f"SixProvincesSystem 执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "system": "SixProvincesSystem",
                "error": str(e),
                "mode": "error",
            }

    def _analyze_task_type(self, task: str) -> str:
        """分析任务类型，确定属于哪个/哪些部门"""
        task_lower = task.lower()

        categories = {
            "schedule": ["日程", "安排", "提醒", "会议", "约会", "calendar", "schedule"],
            "health": ["健康", "睡眠", "运动", "饮食", "身体", "health", "sleep", "exercise"],
            "finance": ["钱", "费", "账单", "消费", "省钱", "money", "cost", "bill"],
            "inventory": ["冰箱", "库存", "买", "缺", "补货", "inventory", "stock", "buy"],
            "mood": ["心情", "情绪", "放松", "压力", "mood", "emotion", "relax"],
            "entertainment": ["电影", "音乐", "听歌", "看片", "娱乐", "movie", "music", "entertainment"],
            "ambiance": ["灯光", "氛围", "窗帘", "空调", "温度", "light", "ambiance", "scene"],
            "security": ["安全", "门锁", "摄像头", "陌生人", "报警", "security", "camera", "alarm"],
            "safety": ["跌倒", "紧急", "求助", "老人", "小孩", "safety", "emergency", "fall"],
            "rule": ["规则", "限制", "权限", "时间", "不让", "rule", "limit", "permission"],
            "privacy": ["隐私", "保密", "不要说", "privacy", "secret"],
            "device": ["设备", "灯泡", "坏了", "检查", "维护", "device", "broken", "maintain"],
            "energy": ["电", "水", "气", "节能", "能耗", "energy", "electricity", "save"],
        }

        matched = []
        for category, keywords in categories.items():
            if any(kw in task_lower for kw in keywords):
                matched.append(category)

        if not matched:
            return "general"

        return "+".join(matched)

    def _get_ministers_for_task(self, task_type: str) -> list:
        """根据任务类型获取需要的六部"""
        minister_map = {
            "schedule": ["吏部"],
            "health": ["吏部"],
            "finance": ["户部"],
            "inventory": ["户部"],
            "mood": ["礼部"],
            "entertainment": ["礼部"],
            "ambiance": ["礼部"],
            "security": ["兵部"],
            "safety": ["兵部"],
            "rule": ["刑部"],
            "privacy": ["刑部"],
            "device": ["工部"],
            "energy": ["工部"],
        }

        ministers = set()
        for t in task_type.split("+"):
            if t in minister_map:
                ministers.update(minister_map[t])

        return list(ministers) if ministers else ["尚书省"]

    def run_minister(self, minister_name: str, input_data: str) -> dict:
        """
        直接运行某个特定部门

        Args:
            minister_name: 部门名称 (吏部|户部|礼部|兵部|刑部|工部|中书省|门下省|尚书省)
            input_data: 输入数据

        Returns:
            执行结果
        """
        try:
            agent_map = {
                "吏部": self.libu,
                "户部": self.hubu,
                "礼部": self.libu_entertainment,
                "兵部": self.bingbu,
                "刑部": self.xingbu,
                "工部": self.gongbu,
                "中书省": self.zhongshu,
                "门下省": self.menxia,
                "尚书省": self.shangshu,
            }

            agent = agent_map.get(minister_name)
            if not agent:
                return {"error": f"未知部门: {minister_name}"}

            result = agent.run(input_data)
            return {
                "minister": minister_name,
                "result": result,
            }
        except Exception as e:
            logger.error(f"Single minister run failed: {e}")
            return {"minister": minister_name, "error": str(e)}
