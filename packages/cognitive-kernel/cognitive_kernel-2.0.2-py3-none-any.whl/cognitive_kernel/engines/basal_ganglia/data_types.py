"""
Basal Ganglia Engine Data Types
기저핵 엔진 데이터 타입 정의

Author: GNJz (Qquarts)
Version: 1.0.0-alpha
"""

import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ActionType(Enum):
    """
    행동 타입 (Action Type)
    
    생물학적 근거:
    - 기저핵은 Go/NoGo 결정을 담당하는 뇌의 "행동 게이트키퍼"
    - GO: 행동 실행
    - NOGO: 행동 억제
    - EXPLORE: 새로운 행동 탐색
    """
    GO = "GO"           # 실행
    NOGO = "NOGO"       # 억제
    EXPLORE = "EXPLORE" # 탐색 (새로운 시도)


@dataclass
class Action:
    """
    행동 (Action)
    
    Q-learning 기반 행동 선택을 위한 행동 정보
    
    수식 참고:
    - Q-value: Q(s,a) = 예상 보상 가치
    - 습관 강도: H = H + β·(success - H)
    - 성공률: success_rate = success_count / execution_count
    """
    name: str                           # 행동 이름
    context: str = ""                   # 상황/맥락
    q_value: float = 0.0                # Q-값 (예상 보상)
    execution_count: int = 0            # 실행 횟수
    success_count: int = 0               # 성공 횟수
    habit_strength: float = 0.0         # 습관 강도 (0~1)
    last_executed: float = field(default_factory=time.time)  # 마지막 실행 시간
    
    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    @property
    def is_habit(self) -> bool:
        """
        습관화 여부
        
        습관 강도가 임계값(기본 0.7) 이상이면 습관으로 간주
        습관화된 행동은 자동 실행 경로(Fast Path)로 처리됨
        """
        return self.habit_strength >= 0.7


@dataclass
class ActionResult:
    """
    행동 결과 (Action Result)
    
    행동 선택 후 반환되는 결과 정보
    """
    action: Action                      # 선택된 행동
    decision: ActionType                # 결정 타입 (GO/NOGO/EXPLORE)
    confidence: float                   # 확신도 (0~1)
    is_automatic: bool                  # 자동 실행 여부 (습관)
    reasoning: str                      # 선택 이유 (자연어)

