"""
Dynamics Engine Data Models
동역학 엔진 데이터 모델

Author: GNJz (Qquarts)
Version: 2.0.1+
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DynamicsState:
    """
    동역학 상태
    
    모든 동역학 관련 상태를 캡슐화합니다.
    """
    
    # 현재 상태
    entropy: float = 0.0  # 현재 엔트로피
    core_strength: float = 0.0  # 현재 코어 강도
    precession_phi: float = 0.0  # 회전 위상
    
    # Core Decay 상태
    persistent_core: Optional[float] = None  # 지속 코어 강도
    last_decay_time: Optional[float] = None  # 마지막 감쇠 시간
    
    # 인지적 절규 상태
    cognitive_distress: bool = False  # 인지적 절규 상태
    
    # 히스토리
    entropy_history: List[float] = field(default_factory=list)
    core_strength_history: List[float] = field(default_factory=list)
    
    def reset(self) -> None:
        """상태 초기화"""
        self.entropy = 0.0
        self.core_strength = 0.0
        self.precession_phi = 0.0
        self.persistent_core = None
        self.last_decay_time = None
        self.cognitive_distress = False
        self.entropy_history.clear()
        self.core_strength_history.clear()
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "entropy": self.entropy,
            "core_strength": self.core_strength,
            "precession_phi": self.precession_phi,
            "persistent_core": self.persistent_core,
            "last_decay_time": self.last_decay_time,
            "cognitive_distress": self.cognitive_distress,
            "entropy_history_length": len(self.entropy_history),
            "core_strength_history_length": len(self.core_strength_history),
        }

