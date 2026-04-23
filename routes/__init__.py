# routes/__init__.py
"""
Flask Blueprints 聚合入口
"""
from flask import Flask

from routes.personality import personality_bp
from routes.memory import memory_bp
from routes.skills import skills_bp
from routes.kairos import kairos_bp, init_kairos
from routes.hyper import hyper_bp
from routes.agent import agent_bp, init_agent
from routes.voice_pipeline import voice_bp


def register_all_blueprints(app: Flask):
    """注册所有 Blueprint 到 Flask app"""
    app.register_blueprint(personality_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(kairos_bp)
    app.register_blueprint(hyper_bp)
    app.register_blueprint(agent_bp)


__all__ = [
    "personality_bp",
    "memory_bp",
    "skills_bp",
    "kairos_bp",
    "hyper_bp",
    "agent_bp",
    "voice_bp",
    "register_all_blueprints",
    "init_kairos",
    "init_agent",
]
