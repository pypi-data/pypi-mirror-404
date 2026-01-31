"""
Hypothalamus Engine Data Types
시상하부 엔진 데이터 타입 정의

Author: GNJz (Qquarts)
Version: 1.0.0-alpha
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class DriveType(Enum):
    """
    욕구 유형 (Drive Type)
    
    생물학적 근거:
    - 시상하부는 다양한 생존 욕구를 관리하는 뇌의 "조종석"
    - 각 욕구는 내부 상태(에너지, 지루함, 스트레스 등)에 기반하여 계산됨
    """
    SLEEP = "SLEEP_DRIVE"         # 수면 욕구 (에너지 고갈)
    EXPLORE = "EXPLORE_DRIVE"     # 탐험 욕구 (지루함)
    SOCIAL = "SOCIAL_DRIVE"       # 사회적 욕구 (외로움)
    LEARN = "LEARN_DRIVE"         # 학습 욕구 (지적 허기)
    REST = "REST_DRIVE"           # 휴식 욕구 (스트레스)
    STAY = "STAY_DRIVE"           # 대기 상태 (안정)


@dataclass
class InternalState:
    """
    내부 상태 (Internal State)
    
    시상하부가 관리하는 생리적/심리적 상태 변수들
    
    수식 참고:
    - 에너지 감쇠: E(t) = E_0 · e^(-λ·t) + E_min
    - 지루함 증가: B(t) = B_0 + α·t·(1-S)
    - 도파민 반응: D = D_base + β·R·(1-D)
    
    모든 값은 0.0 ~ 1.0 범위로 정규화됨
    """
    energy: float = 1.0           # 에너지 (0~1): 활동 능력
    dopamine: float = 0.5         # 도파민/의욕 (0~1): 동기 부여
    boredom: float = 0.0          # 지루함 (0~1): 자극 부족
    curiosity: float = 0.5        # 호기심 (0~1): 학습 동기
    stress: float = 0.0           # 스트레스 (0~1): 부하/위협
    loneliness: float = 0.0       # 외로움 (0~1): 사회적 고립
    satisfaction: float = 0.5     # 만족감 (0~1): 보상 누적
    
    def to_dict(self) -> Dict[str, float]:
        """딕셔너리로 변환"""
        return {
            'energy': round(self.energy, 3),
            'dopamine': round(self.dopamine, 3),
            'boredom': round(self.boredom, 3),
            'curiosity': round(self.curiosity, 3),
            'stress': round(self.stress, 3),
            'loneliness': round(self.loneliness, 3),
            'satisfaction': round(self.satisfaction, 3),
        }


@dataclass
class DriveSignal:
    """
    욕구 신호 (Drive Signal)
    
    현재 가장 시급한 욕구와 그에 대한 정보
    
    수식:
        욕구 우선순위: P = w_E·(1-E) + w_B·B + w_C·C
        - w_E: 에너지 가중치
        - w_B: 지루함 가중치
        - w_C: 호기심 가중치
        - E: 에너지 (0~1)
        - B: 지루함 (0~1)
        - C: 호기심 (0~1)
    """
    drive_type: DriveType         # 욕구 유형
    urgency: float                # 긴급도 (0~1): 높을수록 즉시 처리 필요
    message: str                 # 상태 메시지 (자연어)
    action_suggestion: str        # 권장 행동 (예: "sleep", "explore", "learn")
    timestamp: float = field(default_factory=time.time)  # 생성 시간

