"""
🏠 Node Manager - 多设备节点管理
统一管理：Mac Mini 主节点、手机 Termux 节点、云服务器跳板节点
像贾维斯一样掌控所有设备！
"""
import os
import json
import logging
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """节点信息"""
    node_id: str
    name: str
    type: str  # "main", "mobile", "cloud"
    url: str
    ssh_host: Optional[str] = None
    ssh_port: int = 22
    ssh_user: Optional[str] = None
    enabled: bool = True
    last_seen: float = 0
    health_ok: bool = False


class NodeManager:
    """多节点管理器"""
    
    def __init__(self):
        self.nodes: Dict[str, NodeInfo] = {}
        self._load_config()
        # 自动添加已配置的节点
        self._auto_discover_nodes()
    
    def _load_config(self):
        """从环境变量加载节点配置"""
        config_path = os.getenv("NODES_CONFIG", "")
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                for node in data.get("nodes", []):
                    self.add_node(NodeInfo(**node))
    
    def _auto_discover_nodes(self):
        """自动发现已知节点"""
        # Mac Mini 主节点（本机）
        if not self.get_node("main"):
            self.add_node(NodeInfo(
                node_id="main",
                name="Mac Mini 主节点",
                type="main",
                url="http://localhost:8000",
                enabled=True
            ))
        
        # 手机 Termux 节点（已知配置）
        if os.getenv("TERMUX_API") and not self.get_node("mobile_01"):
            self.add_node(NodeInfo(
                node_id="mobile_01",
                name="手机 Termux 传感器节点",
                type="mobile",
                url=os.getenv("TERMUX_API", "http://192.168.1.10:8080"),
                ssh_host="192.168.1.10",
                ssh_port=8022,
                ssh_user="u0_a121",
                enabled=True
            ))
        
        # 云服务器跳板节点
        if not self.get_node("cloud_01"):
            self.add_node(NodeInfo(
                node_id="cloud_01",
                name="阿里云跳板服务器",
                type="cloud",
                url="http://123.57.107.21:8000",
                ssh_host="123.57.107.21",
                ssh_port=22,
                ssh_user="root",
                enabled=True
            ))
            
        # 备用云服务器
        if not self.get_node("cloud_02"):
            self.add_node(NodeInfo(
                node_id="cloud_02",
                name="Ubuntu 代理服务器",
                type="cloud",
                url="http://43.134.39.26:8000",
                ssh_host="43.134.39.26",
                ssh_port=22,
                ssh_user="ubuntu",
                enabled=True
            ))
    
    def add_node(self, node: NodeInfo) -> None:
        """添加节点"""
        self.nodes[node.node_id] = node
    
    def remove_node(self, node_id: str) -> bool:
        """移除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def list_nodes(self, only_enabled: bool = True) -> List[Dict]:
        """列出所有节点"""
        result = []
        for node in self.nodes.values():
            if only_enabled and not node.enabled:
                continue
            result.append(asdict(node))
        return result
    
    def check_health(self, node_id: str) -> bool:
        """检查节点健康状态"""
        node = self.get_node(node_id)
        if not node or not node.enabled:
            return False
        
        try:
            url = f"{node.url.rstrip('/')}/health"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                node.health_ok = True
                return True
        except Exception:
            pass
        
        node.health_ok = False
        return False
    
    def check_all_health(self) -> Dict[str, bool]:
        """检查所有节点健康状态"""
        results = {}
        for node_id in self.nodes:
            results[node_id] = self.check_health(node_id)
        return results
    
    def execute_remote(self, node_id: str, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """在远程节点执行API调用"""
        node = self.get_node(node_id)
        if not node or not node.enabled:
            return {"success": False, "error": "节点不存在或未启用"}
        
        url = f"{node.url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            if method.upper() == "GET":
                resp = requests.get(url, timeout=10)
            else:
                resp = requests.post(url, json=data or {}, timeout=10)
            
            return {
                "success": resp.status_code < 400,
                "status_code": resp.status_code,
                "data": resp.json() if resp.headers.get("content-type", "").find("json") >= 0 else resp.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_summary(self) -> Dict:
        """获取节点汇总信息"""
        total = len(self.nodes)
        enabled = sum(1 for n in self.nodes.values() if n.enabled)
        healthy = sum(1 for n in self.nodes.values() if n.enabled and n.health_ok)
        
        return {
            "total": total,
            "enabled": enabled,
            "healthy": healthy,
            "nodes": self.list_nodes()
        }


# 单例
_node_manager: Optional[NodeManager] = None


def get_node_manager() -> NodeManager:
    global _node_manager
    if _node_manager is None:
        _node_manager = NodeManager()
    return _node_manager
