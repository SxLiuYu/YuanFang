"""
agents/hyper/evolutionary_memory.py
进化记忆 · EvolutionaryMemory
TaskAgent × MetaAgent 闭环的策略存储
"""
import os
import json
import uuid
import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EVOLUTION_DIR = Path(__file__).parent / "evolution_memory"


class EvolutionaryMemory:
    def __init__(self, storage_dir=None):
        self.storage_dir = Path(storage_dir) if storage_dir else EVOLUTION_DIR
        self.storage_dir.mkdir(exist_ok=True)
        self.index_file = self.storage_dir / "strategy_index.json"
        self.strategies = self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text("utf-8"))
            except Exception:
                pass
        return {"strategies": [], "domains": {}}

    def _save_index(self):
        self.index_file.write_text(json.dumps(self.strategies, ensure_ascii=False, indent=2), encoding="utf-8")

    def _get_strategy(self, strategy_id: str) -> dict:
        strategy_file = self.storage_dir / f"strategy_{strategy_id}.json"
        if strategy_file.exists():
            return json.loads(strategy_file.read_text("utf-8"))
        return {}

    def store(self, improvement, task_summary: str):
        strategy_id = str(uuid.uuid4())[:8]
        strategy_file = self.storage_dir / f"strategy_{strategy_id}.json"

        entry = {
            "id": strategy_id,
            "task_summary": task_summary[:100],
            "quality_score": improvement.get("quality_score", 5),
            "improvement_strategy": improvement.get("improvement_strategy", ""),
            "domain_hint": improvement.get("domain_hint", "general"),
            "tags": improvement.get("tags", []),
            "strengths": improvement.get("strengths", []),
            "weaknesses": improvement.get("weaknesses", []),
            "created_at": datetime.datetime.now().isoformat(),
            "use_count": 0
        }

        strategy_file.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        self.strategies["strategies"].append(strategy_id)

        domain = improvement.get("domain_hint", "general")
        if domain not in self.strategies["domains"]:
            self.strategies["domains"][domain] = []
        self.strategies["domains"][domain].append(strategy_id)

        self.strategies["strategies"].sort(
            key=lambda sid: self._get_strategy(sid).get("quality_score", 0),
            reverse=True
        )
        self._save_index()
        logger.info(f"存储策略 {strategy_id}，领域 {domain}，质量 {entry['quality_score']}/10")

    def retrieve(self, query: str, top_k: int = 3):
        retrieved = []
        query_lower = query.lower()

        for strategy_id in self.strategies["strategies"][:10]:
            entry = self._get_strategy(strategy_id)
            if not entry:
                continue

            score = 0
            tags = entry.get("tags", [])
            domain = entry.get("domain_hint", "")

            for tag in tags:
                if tag in query_lower:
                    score += 3
            if domain in query_lower:
                score += 5
            if entry.get("quality_score", 0) >= 8:
                score += 2

            if score > 0:
                entry["match_score"] = score
                retrieved.append(entry)

        retrieved.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return retrieved[:top_k]

    def get_context(self, query: str) -> str | None:
        strategies = self.retrieve(query)
        if not strategies:
            return None
        context_lines = []
        for s in strategies:
            context_lines.append(
                f"- [{s['domain_hint']}] 质量{s['quality_score']}/10: {s['improvement_strategy']}"
            )
        return "\n".join(context_lines)

    def evolution_report(self) -> dict:
        total = len(self.strategies["strategies"])
        if total == 0:
            return {"total_strategies": 0, "message": "还没有存储任何策略"}

        total_score = 0
        count = 0
        for sid in self.strategies["strategies"]:
            entry = self._get_strategy(sid)
            if entry:
                total_score += entry.get("quality_score", 0)
                count += 1

        avg_score = total_score / count if count > 0 else 0
        return {
            "total_strategies": total,
            "domains": list(self.strategies["domains"].keys()),
            "domain_count": len(self.strategies["domains"]),
            "average_quality_score": round(avg_score, 1),
            "message": f"已积累 {total} 条策略，覆盖 {len(self.strategies['domains'])} 个领域，平均质量 {avg_score:.1f}/10"
        }
