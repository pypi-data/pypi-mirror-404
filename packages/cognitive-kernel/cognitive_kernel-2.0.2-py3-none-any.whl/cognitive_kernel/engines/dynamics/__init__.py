"""
Dynamics Engine Package
동역학 엔진 패키지

엔트로피, 코어 강도, 회전 토크 계산 및 Core Decay 동역학 처리.

🔗 Edge AI 지원:
    독립적으로 사용 가능한 동역학 엔진

Author: GNJz (Qquarts)
Version: 2.0.1+
"""

from .config import DynamicsConfig
from .models import DynamicsState
from .dynamics_engine import DynamicsEngine

__all__ = [
    "DynamicsConfig",
    "DynamicsState",
    "DynamicsEngine",
]

__version__ = "1.0.0"

