"""
Amygdala Engine - 데이터 타입 정의

Author: GNJz (Qquarts)
Version: 1.0.0-alpha
"""

import time
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmotionState:
    """
    감정 상태 (Valence-Arousal 모델)
    
    Attributes:
        valence: 쾌-불쾌 (-1 ~ +1)
        arousal: 각성도 (0 ~ 1)
        dominant: 지배적 감정
        timestamp: 타임스탬프
    """
    valence: float = 0.0
    arousal: float = 0.0
    dominant: str = "neutral"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """범위 클램프"""
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(0.0, min(1.0, self.arousal))
    
    @property
    def intensity(self) -> float:
        """
        감정 강도
        
        수식: E = √(V² + A²)
        """
        return math.sqrt(self.valence**2 + self.arousal**2)
    
    def decay(self, lambda_rate: float = 0.1, baseline: float = 0.0) -> 'EmotionState':
        """
        감정 감쇠
        
        수식: E(t) = E_0 · e^(-λt) + E_baseline
        
        Args:
            lambda_rate: 감쇠율
            baseline: 기준선 값
            
        Returns:
            감쇠된 감정 상태
        """
        dt = time.time() - self.timestamp
        decay_factor = math.exp(-lambda_rate * dt)
        
        new_valence = self.valence * decay_factor + baseline
        new_arousal = self.arousal * decay_factor
        
        new_intensity = math.sqrt(new_valence**2 + new_arousal**2)
        
        return EmotionState(
            valence=new_valence,
            arousal=new_arousal,
            dominant=self.dominant if new_intensity > 0.3 else "neutral",
            timestamp=time.time()
        )


@dataclass
class ThreatSignal:
    """
    위협 신호
    
    Attributes:
        source: 위협 출처
        threat_level: 위협 수준 (0 ~ 1)
        threat_type: 위협 유형
        response: 권장 반응
        timestamp: 타임스탬프
    """
    source: str
    threat_level: float
    threat_type: str
    response: str
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """범위 클램프"""
        self.threat_level = max(0.0, min(1.0, self.threat_level))


@dataclass
class FearMemory:
    """
    공포 기억 (조건화)
    
    Attributes:
        stimulus: 조건 자극 (CS)
        threat: 무조건 자극과 연결된 위협 (US)
        strength: 연합 강도 (0 ~ 1)
        created_at: 생성 시간
        last_activated: 마지막 활성화 시간
        activation_count: 활성화 횟수
    """
    stimulus: str
    threat: str
    strength: float = 0.5
    created_at: float = field(default_factory=time.time)
    last_activated: float = field(default_factory=time.time)
    activation_count: int = 0
    
    def __post_init__(self):
        """범위 클램프"""
        self.strength = max(0.0, min(1.0, self.strength))

