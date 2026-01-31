from dataclasses import dataclass, field
from typing import Any, Optional, List
from enum import Enum
import uuid


class ActionStatus(Enum):
    """행동 상태."""
    PENDING = "pending"
    SELECTED = "selected"
    INHIBITED = "inhibited"
    EXECUTED = "executed"


@dataclass
class WorkingMemorySlot:
    """작업 기억 슬롯.

    - id: 고유 식별자
    - content: 저장된 정보 (MemoryRank에서 온 기억 ID 또는 임의 데이터)
    - relevance: 현재 목표와의 관련성 (0~1)
    - timestamp: 저장 시간
    - source: 출처 (예: "memoryrank", "external")
    """

    id: str
    content: Any
    relevance: float
    timestamp: float
    source: str = "external"

    def __post_init__(self):
        self.relevance = max(0.0, min(1.0, float(self.relevance)))


@dataclass
class Action:
    """행동 후보.

    - id: 고유 식별자
    - name: 행동 이름
    - expected_reward: 기대 보상 (0~1)
    - effort_cost: 노력 비용 (0~1)
    - risk: 위험도 (0~1)
    - context: 추가 맥락 정보
    """

    id: str
    name: str
    expected_reward: float = 0.5
    effort_cost: float = 0.3
    risk: float = 0.2
    context: dict = field(default_factory=dict)

    def __post_init__(self):
        self.expected_reward = max(0.0, min(1.0, float(self.expected_reward)))
        self.effort_cost = max(0.0, min(1.0, float(self.effort_cost)))
        self.risk = max(0.0, min(1.0, float(self.risk)))

    @staticmethod
    def create(name: str, reward: float = 0.5, cost: float = 0.3, risk: float = 0.2) -> "Action":
        """간편 생성자."""
        return Action(
            id=str(uuid.uuid4()),
            name=name,
            expected_reward=reward,
            effort_cost=cost,
            risk=risk,
        )


@dataclass
class ActionResult:
    """행동 선택 결과.

    - action: 선택된 행동 (억제된 경우 None)
    - utility: 계산된 효용값
    - inhibited: 억제 여부
    - conflict_signal: 갈등 신호 강도
    - selection_probability: 선택 확률 (softmax)
    """

    action: Optional[Action]
    utility: float
    inhibited: bool
    conflict_signal: float
    selection_probability: float
