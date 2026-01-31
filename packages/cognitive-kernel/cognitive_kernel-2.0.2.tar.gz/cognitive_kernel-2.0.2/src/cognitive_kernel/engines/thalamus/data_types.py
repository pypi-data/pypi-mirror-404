"""
Thalamus Engine - 데이터 타입 정의

Author: GNJz (Qquarts)
Version: 1.0.0
"""

import time
from typing import Any, Dict
from dataclasses import dataclass, field
from enum import Enum


class ModalityType(Enum):
    """감각 양식"""
    VISUAL = "visual"           # 시각
    AUDITORY = "auditory"       # 청각
    SEMANTIC = "semantic"       # 의미
    EMOTIONAL = "emotional"     # 감정
    EPISODIC = "episodic"       # 에피소드
    MOTOR = "motor"             # 운동
    INTERNAL = "internal"       # 내부 상태


@dataclass
class SensoryInput:
    """
    감각 입력 (불변 객체)
    
    Attributes:
        content: 입력 내용 (Any)
        modality: 감각 양식 (ModalityType)
        intensity: 강도 (0~1)
        salience: 현저성 (0~1) - 주의 끌기 정도
        timestamp: 타임스탬프
        metadata: 추가 메타데이터
    """
    content: Any
    modality: ModalityType
    intensity: float = 1.0
    salience: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """범위 클램프"""
        self.intensity = max(0.0, min(1.0, self.intensity))
        self.salience = max(0.0, min(1.0, self.salience))


@dataclass
class FilteredOutput:
    """
    필터링된 출력
    
    Attributes:
        content: 출력 내용
        modality: 감각 양식
        attention_weight: 주의 가중치
        passed_gate: 게이트 통과 여부
        priority: 우선순위 (낮을수록 높음)
        computed_salience: 계산된 현저성
    """
    content: Any
    modality: ModalityType
    attention_weight: float
    passed_gate: bool
    priority: int
    computed_salience: float

