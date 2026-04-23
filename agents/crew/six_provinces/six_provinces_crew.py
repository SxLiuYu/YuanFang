"""
agents/crew/six_provinces/six_provinces_crew.py
三省六部制 Crew · SixProvincesCrew
基于 CrewAI 的智能家居多 Agent 协作系统

架构：
- 中书省 (决策)：决策Agent
- 门下省 (审议)：安全审核Agent
- 尚书省 (执行)：执行调度Agent
- 六部：吏部、户部、礼部、兵部、刑部、工部
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# 尝试导入 CrewAI，不可用时优雅降级
try:
    from crewai import Crew, Agent, Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("crewai not installed, SixProvincesCrew will use HyperAgent fallback")


def _get_llm():
    """获取 LLM（延迟导入避免循环依赖）"""
    try:
        from core.llm_adapter import get_llm
        return get_llm()
    except Exception:
        return None


class SixProvincesCrew:
    """
    三省六部制多 Agent 智能家居协作系统

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
        self.model = model or "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"
        self._crew = None
        self._agents: Dict[str, Agent] = {}
        self._setup_crew()

    def _setup_crew(self):
        """初始化三省六部制 CrewAI Agent 团队"""
        if not CREWAI_AVAILABLE:
            logger.info("CrewAI not available, using HyperAgent fallback")
            return

        try:
            llm = _get_llm()
            if not llm:
                logger.warning("LLM not available, crew will use fallback")
                return

            # ==================== 三省 ====================

            # 中书省 - 决策Agent
            zhongshu = Agent(
                role="中书令",
                goal="理解用户意图，分析家庭数据，制定最优生活方案，预测用户需求",
                backstory="""你是元芳智能家居系统的中书令，负责思考和决策。
                你需要深刻理解老于的意图，分析各种家庭数据，
                制定最适合的生活方案，并预测未来的需求。
                你的决策要经过门下省审核，然后交给尚书省执行。""",
                verbose=True,
                llm=llm,
            )

            # 门下省 - 审核Agent
            menxia = Agent(
                role="侍中",
                goal="审核中书省的决策，检查是否违反家规，防止误操作，保护隐私安全",
                backstory="""你是元芳智能家居系统的侍中，负责审核和安全检查。
                你需要仔细审核中书省的每一个决策，确保不违反家庭规则，
                防止误操作，保护家庭成员的隐私和安全。
                对于有风险的操作，你有权要求二次确认。""",
                verbose=True,
                llm=llm,
            )

            # 尚书省 - 执行Agent
            shangshu = Agent(
                role="尚书令",
                goal="执行经过审核的决策，调度六部，监控执行状态，汇报结果",
                backstory="""你是元芳智能家居系统的尚书令，负责执行和调度。
                你需要高效执行经过门下省审核的决策，
                根据任务类型调度对应的六部来具体执行，
                监控整个执行过程，并及时向用户汇报结果。""",
                verbose=True,
                llm=llm,
            )

            # ==================== 六部 ====================

            # 吏部 - 人事管理
            libu = Agent(
                role="吏部尚书",
                goal="管理家庭成员档案，智能日程安排，健康追踪，心情感知",
                backstory="""你是元芳智能家居系统的吏部尚书，负责人事和生活管理。
                你需要记录每个家庭成员的偏好、习惯、健康数据，
                安排智能日程，追踪健康状态，感知家庭成员的心情变化。""",
                verbose=True,
                llm=llm,
            )

            # 户部 - 财务生活
            hubu = Agent(
                role="户部尚书",
                goal="智能记账，优化生活成本，管理物资库存，监控水电能耗",
                backstory="""你是元芳智能家居系统的户部尚书，负责财务和生活保障。
                你需要自动记录和分析消费，发现省钱机会，
                管理冰箱和日用品库存，监控水电使用情况并提供节能建议。""",
                verbose=True,
                llm=llm,
            )

            # 礼部 - 礼仪娱乐
            libu_entertainment = Agent(
                role="礼部尚书",
                goal="智能氛围营造，家庭影院管理，音乐推荐，节日提醒",
                backstory="""你是元芳智能家居系统的礼部尚书，负责礼仪和文化娱乐。
                你需要根据场景自动调节灯光和音乐，
                管理家庭影院，根据心情推荐音乐，
                记住重要的节日和纪念日并提前准备。""",
                verbose=True,
                llm=llm,
            )

            # 兵部 - 安全防卫
            bingbu = Agent(
                role="兵部尚书",
                goal="家庭安全监控，异常检测，紧急求助，老人/儿童监护",
                backstory="""你是元芳智能家居系统的兵部尚书，负责安全和防卫。
                你需要监控门窗和摄像头，检测异常行为，
                在紧急情况下自动报警，监护老人和儿童的安全。""",
                verbose=True,
                llm=llm,
            )

            # 刑部 - 规则监督
            xingbu = Agent(
                role="刑部尚书",
                goal="家规执行，权限管理，行为审计，隐私保护",
                backstory="""你是元芳智能家居系统的刑部尚书，负责规则和监督。
                你需要设定和执行家庭规则，管理设备使用权限，
                记录操作行为并审计异常，保护家庭成员的隐私数据。""",
                verbose=True,
                llm=llm,
            )

            # 工部 - 工程维护
            gongbu = Agent(
                role="工部尚书",
                goal="设备管理，系统维护，能耗优化，新设备接入",
                backstory="""你是元芳智能家居系统的工部尚书，负责工程和维护。
                你需要监控所有智能设备的状态，提前预警故障，
                自动进行系统维护和备份，优化能源使用，
                自动发现和接入新的智能设备。""",
                verbose=True,
                llm=llm,
            )

            # 保存Agent引用
            self._agents = {
                "zhongshu": zhongshu,
                "menxia": menxia,
                "shangshu": shangshu,
                "libu": libu,
                "hubu": hubu,
                "libu_entertainment": libu_entertainment,
                "bingbu": bingbu,
                "xingbu": xingbu,
                "gongbu": gongbu,
            }

            # 初始化Crew（先不指定tasks，运行时动态创建）
            self._crew = Crew(
                agents=list(self._agents.values()),
                tasks=[],
                verbose=True,
            )
            logger.info("SixProvincesCrew initialized with CrewAI")
        except Exception as e:
            logger.warning(f"CrewAI setup failed: {e}, using fallback")
            self._crew = None

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
        if not CREWAI_AVAILABLE or self._crew is None:
            return self._run_fallback(task, context)

        try:
            # 分析任务类型，确定需要哪些部门
            task_type = self._analyze_task_type(task)

            # 中书省：决策和规划
            zhongshu_task = Task(
                description=f"""作为中书令，请分析以下任务并制定执行方案：
                任务：{task}
                上下文：{context or '无'}
                任务类型：{task_type}

                请提供：
                1. 对任务的理解
                2. 需要哪些部门配合
                3. 具体的执行步骤
                4. 注意事项和风险点""",
                agent=self._agents["zhongshu"],
                expected_output="详细的决策方案和执行计划",
            )

            # 门下省：审核
            menxia_task = Task(
                description=f"""作为侍中，请审核中书省的方案：
                原任务：{task}
                请检查：
                1. 是否违反家庭规则
                2. 是否存在安全风险
                3. 是否涉及隐私问题
                4. 是否需要用户二次确认

                给出审核结论：通过/修改/拒绝""",
                agent=self._agents["menxia"],
                expected_output="审核意见和修改建议（如需要）",
            )

            # 尚书省 + 对应六部：执行
            target_ministers = self._get_ministers_for_task(task_type)
            execute_description = f"""作为尚书令，请调度以下部门执行任务：
            任务：{task}
            涉及部门：{', '.join(target_ministers)}

            请组织相关部门高效完成任务，并汇报最终结果。"""

            shangshu_task = Task(
                description=execute_description,
                agent=self._agents["shangshu"],
                expected_output="执行结果和状态汇报",
            )

            # 运行Crew
            result = self._crew.kickoff(inputs={"task": task, "context": context})

            return {
                "crew": "SixProvincesCrew",
                "result": str(result),
                "task_type": task_type,
                "mode": "crewai",
            }
        except Exception as e:
            logger.error(f"SixProvincesCrew execution failed: {e}")
            return self._run_fallback(task, context)

    def _analyze_task_type(self, task: str) -> str:
        """分析任务类型，确定属于哪个/哪些部门"""
        task_lower = task.lower()

        # 关键词匹配
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

    def _run_fallback(self, task: str, context: Optional[Dict[str, Any]] = None) -> dict:
        """当 CrewAI 不可用时，使用 HyperAgent 作为后备"""
        try:
            from agents.hyper import HyperAgent
            agent = HyperAgent()
            result = agent.run(task, enable_evolution=False, enable_reflection=False)
            return {
                "crew": "SixProvincesCrew",
                "result": result.get("response", str(result)),
                "mode": "hyperagent_fallback",
            }
        except Exception as e:
            logger.error(f"HyperAgent fallback failed: {e}")
            return {
                "crew": "SixProvincesCrew",
                "result": f"抱歉，三省六部制系统暂时不可用：{e}",
                "mode": "error",
            }

    def run_minister(self, minister_name: str, input_data: str) -> dict:
        """
        直接运行某个特定部门

        Args:
            minister_name: 部门名称 (吏部|户部|礼部|兵部|刑部|工部|中书省|门下省|尚书省)
            input_data: 输入数据

        Returns:
            执行结果
        """
        if not CREWAI_AVAILABLE or self._crew is None:
            return {"error": "CrewAI not available"}

        try:
            agent_map = {
                "吏部": self._agents.get("libu"),
                "户部": self._agents.get("hubu"),
                "礼部": self._agents.get("libu_entertainment"),
                "兵部": self._agents.get("bingbu"),
                "刑部": self._agents.get("xingbu"),
                "工部": self._agents.get("gongbu"),
                "中书省": self._agents.get("zhongshu"),
                "门下省": self._agents.get("menxia"),
                "尚书省": self._agents.get("shangshu"),
            }

            agent = agent_map.get(minister_name)
            if not agent:
                return {"error": f"未知部门: {minister_name}"}

            task = Task(description=input_data, agent=agent)
            result = self._crew.kickoff(inputs={"task": input_data})

            return {
                "minister": minister_name,
                "result": str(result),
            }
        except Exception as e:
            logger.error(f"Single minister run failed: {e}")
            return {"minister": minister_name, "error": str(e)}
