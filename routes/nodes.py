# routes/nodes.py
"""
节点管理路由
提供节点状态查询和健康检查API
"""
from flask import Blueprint, request, jsonify
import logging
from adapters.node_manager import get_node_manager

logger = logging.getLogger(__name__)

nodes_bp = Blueprint("nodes", __name__)
node_manager = get_node_manager()


@nodes_bp.route("/api/nodes/health", methods=["GET"])
def check_all_nodes():
    """检查所有节点健康状态"""
    results = node_manager.check_all_health()
    summary = node_manager.get_summary()
    # 整理成前端需要的格式 {node_id: {name, type, healthy, ...}}
    nodes_out = {}
    for node_id, r in results.items():
        node = node_manager.get_node(node_id)
        nodes_out[node_id] = {
            "id": node_id,
            "name": node.name if node else node_id,
            "type": node.type if node else "unknown",
            "description": node.description if node and node.description else "",
            "healthy": r.get("healthy", False),
            "last_health_check_ok": r.get("healthy", False),
            "last_health_check_at": r.get("checked_at", "-"),
            "last_seen": node.last_seen if node else "-",
            "latency_ms": r.get("latency_ms", 0),
        }
    return jsonify({
        "success": True,
        "results": results,
        "summary": summary,
        "nodes": nodes_out
    }), 200


@nodes_bp.route("/api/nodes/health/<node_id>", methods=["GET"])
def check_single_node(node_id):
    """检查单个节点健康状态"""
    healthy = node_manager.check_health(node_id)
    node = node_manager.get_node(node_id)
    if not node:
        return jsonify({"error": "Node not found"}), 404
    return jsonify({
        "success": True,
        "node_id": node_id,
        "healthy": healthy,
        "node_info": {
            "name": node.name,
            "type": node.type,
            "url": node.url,
            "enabled": node.enabled,
            "health_ok": node.health_ok,
            "last_seen": node.last_seen
        }
    }), 200


@nodes_bp.route("/api/nodes", methods=["GET"])
def list_all_nodes():
    """列出所有节点"""
    only_enabled = request.args.get("enabled_only", "true").lower() == "true"
    nodes = node_manager.list_nodes(only_enabled=only_enabled)
    return jsonify({
        "success": True,
        "count": len(nodes),
        "nodes": nodes
    }), 200


@nodes_bp.route("/api/nodes/summary", methods=["GET"])
def node_summary():
    """获取节点汇总信息"""
    summary = node_manager.get_summary()
    return jsonify({
        "success": True,
        "summary": summary
    }), 200


def init_nodes_routes(app):
    """注册节点路由"""
    app.register_blueprint(nodes_bp)
    logger.info("[Nodes] 路由已注册: /api/nodes")
    # 启动自动心跳检查（间隔60秒）
    def heartbeat_callback(evt):
        if evt["offline_nodes"]:
            names = [node_manager.get_node(nid).name for nid in evt["offline_nodes"]]
            logger.warning(f"[Heartbeat] 节点离线: {', '.join(names)}")
    node_manager.start_heartbeat(interval_seconds=60, callback=heartbeat_callback)
    logger.info("[Nodes] 自动心跳检查已启动 (60秒间隔)")