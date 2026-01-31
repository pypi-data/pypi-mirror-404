"""
Basal Ganglia Engine
기저핵 엔진 - 행동 선택 및 습관 형성 시스템

Author: GNJz (Qquarts)
Version: 1.0.0-alpha
"""

from .basal_ganglia_engine import BasalGangliaEngine
from .data_types import ActionType, Action, ActionResult
from .config import BasalGangliaConfig

__all__ = [
    'BasalGangliaEngine',
    'ActionType',
    'Action',
    'ActionResult',
    'BasalGangliaConfig',
]

__version__ = '1.0.0-alpha'

