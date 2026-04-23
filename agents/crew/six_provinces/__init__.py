"""
agents/crew/six_provinces/__init__.py
三省六部制 · Six Provinces System
基于 HyperAgent 的智能家居多 Agent 协作系统
"""
from .six_provinces_hyper import SixProvincesSystem
from .six_provinces_with_hass import SixProvincesWithHASS

__all__ = ["SixProvincesSystem", "SixProvincesWithHASS"]
