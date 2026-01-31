"""PFC (Prefrontal Cortex) Engine v1.0

🎬 기억의 영화관에서 "영사기 + 감독" 역할

핵심 기능:
1. Working Memory: 중요 정보를 임시 저장 (용량 제한, 시간 감쇠)
2. Action Evaluator: 행동의 기대 효용 계산 (U = reward - cost - risk*κ)
3. Inhibitor: 위험한 행동 억제 (Go/No-Go gate)
4. Selector: Softmax 확률적 행동 선택
"""

from __future__ import annotations

import math
import time
import uuid
from typing import Dict, List, Optional, Tuple, Any

from .config import PFCConfig
from .models import WorkingMemorySlot, Action, ActionResult


class PFCEngine:
    """PFC Engine v1.0 - 작업 기억 + 행동 선택 + 억제 엔진."""

    def __init__(self, config: Optional[PFCConfig] = None):
        self.config = config or PFCConfig()
        self._working_memory: List[WorkingMemorySlot] = []
        self._current_goal: Optional[str] = None
        self._current_goal_priority: float = 0.5
        self._last_update_time: float = time.time()

    # ------------------------------------------------------------------
    # Working Memory
    # ------------------------------------------------------------------
    def load_to_working_memory(
        self,
        content: Any,
        relevance: float,
        source: str = "external",
    ) -> str:
        """작업 기억에 항목 추가.

        용량 초과 시 가장 낮은 relevance 항목 제거 (Miller's Law).
        """
        slot_id = str(uuid.uuid4())
        slot = WorkingMemorySlot(
            id=slot_id,
            content=content,
            relevance=relevance,
            timestamp=time.time(),
            source=source,
        )

        self._working_memory.append(slot)

        # 용량 초과 시 eviction
        while len(self._working_memory) > self.config.working_memory_capacity:
            # 가장 낮은 relevance 항목 제거
            min_idx = min(range(len(self._working_memory)),
                          key=lambda i: self._working_memory[i].relevance)
            self._working_memory.pop(min_idx)

        return slot_id

    def load_from_memoryrank(
        self,
        top_memories: List[Tuple[str, float]],
    ) -> List[str]:
        """MemoryRank 결과를 작업 기억에 로드.

        Args:
            top_memories: [(memory_id, rank_score), ...] from MemoryRank

        Returns:
            생성된 슬롯 ID 리스트
        """
        slot_ids = []
        for memory_id, score in top_memories:
            # rank score를 relevance로 변환 (정규화)
            relevance = min(1.0, score * 2.0)  # score는 보통 0~0.5 범위
            sid = self.load_to_working_memory(
                content={"memory_id": memory_id, "rank_score": score},
                relevance=relevance,
                source="memoryrank",
            )
            slot_ids.append(sid)
        return slot_ids

    def get_working_memory(self) -> List[WorkingMemorySlot]:
        """현재 작업 기억 내용 반환."""
        return list(self._working_memory)

    def clear_working_memory(self) -> None:
        """작업 기억 초기화."""
        self._working_memory.clear()

    def update_decay(self, dt: Optional[float] = None) -> None:
        """시간 경과에 따른 작업 기억 감쇠 적용.

        relevance(t) = relevance_0 × exp(-λ × Δt)
        """
        now = time.time()
        if dt is None:
            dt = now - self._last_update_time
        self._last_update_time = now

        decay_factor = math.exp(-self.config.decay_rate * dt)

        for slot in self._working_memory:
            # frozen이 아니므로 직접 수정
            object.__setattr__(slot, 'relevance', slot.relevance * decay_factor)

        # relevance가 너무 낮은 항목 제거 (0.01 미만)
        self._working_memory = [s for s in self._working_memory if s.relevance >= 0.01]

    # ------------------------------------------------------------------
    # Goal Management (v1.0: 단일 목표만)
    # ------------------------------------------------------------------
    def set_goal(self, description: str, priority: float = 0.5) -> None:
        """현재 목표 설정."""
        self._current_goal = description
        self._current_goal_priority = max(0.0, min(1.0, priority))

    def get_goal(self) -> Optional[Tuple[str, float]]:
        """현재 목표 반환."""
        if self._current_goal:
            return (self._current_goal, self._current_goal_priority)
        return None

    # ------------------------------------------------------------------
    # Action Evaluation
    # ------------------------------------------------------------------
    def evaluate_action(self, action: Action) -> float:
        """행동의 기대 효용(Expected Utility) 계산.

        U(action) = expected_reward - effort_cost - risk × risk_aversion
        """
        risk_penalty = action.risk * self.config.risk_aversion
        utility = action.expected_reward - action.effort_cost - risk_penalty
        return utility

    def evaluate_actions(self, actions: List[Action]) -> List[Tuple[Action, float]]:
        """여러 행동의 효용 계산."""
        return [(a, self.evaluate_action(a)) for a in actions]

    # ------------------------------------------------------------------
    # Inhibition
    # ------------------------------------------------------------------
    def calculate_conflict_signal(
        self,
        action: Action,
        competing_actions: Optional[List[Action]] = None,
    ) -> float:
        """갈등 신호 계산.

        conflict = max(competing_utilities) - current_utility (if > 0)
        또는 risk가 높으면 갈등 신호 증가
        """
        current_utility = self.evaluate_action(action)

        # 위험 기반 갈등
        risk_conflict = action.risk

        # 경쟁 행동 기반 갈등
        competition_conflict = 0.0
        if competing_actions:
            competing_utilities = [self.evaluate_action(a) for a in competing_actions]
            max_competing = max(competing_utilities) if competing_utilities else 0.0
            if max_competing > current_utility:
                competition_conflict = max_competing - current_utility

        # 종합 갈등 신호
        conflict_signal = max(risk_conflict, competition_conflict)
        return min(1.0, conflict_signal)

    def should_inhibit(
        self,
        action: Action,
        competing_actions: Optional[List[Action]] = None,
    ) -> Tuple[bool, float]:
        """억제 여부 판단 (Go/No-Go).

        Returns:
            (억제 여부, 갈등 신호)
        """
        conflict_signal = self.calculate_conflict_signal(action, competing_actions)
        inhibit = conflict_signal > self.config.inhibition_threshold
        return (inhibit, conflict_signal)

    # ------------------------------------------------------------------
    # Selection (Softmax)
    # ------------------------------------------------------------------
    def softmax_probabilities(self, utilities: List[float]) -> List[float]:
        """Softmax 확률 계산.

        P(i) = exp(β × U_i) / Σ exp(β × U_j)
        """
        beta = self.config.decision_temperature

        # overflow 방지를 위한 정규화
        max_u = max(utilities) if utilities else 0.0
        exp_values = [math.exp(beta * (u - max_u)) for u in utilities]
        total = sum(exp_values)

        if total == 0:
            return [1.0 / len(utilities)] * len(utilities) if utilities else []

        return [e / total for e in exp_values]

    def select_action(
        self,
        actions: List[Action],
        deterministic: bool = False,
    ) -> ActionResult:
        """행동 선택 (Softmax 또는 argmax).

        Args:
            actions: 후보 행동 리스트
            deterministic: True면 argmax, False면 softmax 샘플링

        Returns:
            ActionResult (선택된 행동, 효용, 억제 여부 등)
        """
        if not actions:
            return ActionResult(
                action=None,
                utility=0.0,
                inhibited=False,
                conflict_signal=0.0,
                selection_probability=0.0,
            )

        # 효용 계산
        utilities = [self.evaluate_action(a) for a in actions]
        probabilities = self.softmax_probabilities(utilities)

        # 선택
        if deterministic:
            max_idx = max(range(len(utilities)), key=lambda i: utilities[i])
        else:
            # 확률적 샘플링
            import random
            r = random.random()
            cumsum = 0.0
            max_idx = len(actions) - 1
            for i, p in enumerate(probabilities):
                cumsum += p
                if r < cumsum:
                    max_idx = i
                    break

        selected_action = actions[max_idx]
        selected_utility = utilities[max_idx]
        selected_prob = probabilities[max_idx]

        # 억제 체크
        other_actions = [a for i, a in enumerate(actions) if i != max_idx]
        inhibit, conflict_signal = self.should_inhibit(selected_action, other_actions)

        if inhibit:
            return ActionResult(
                action=None,
                utility=selected_utility,
                inhibited=True,
                conflict_signal=conflict_signal,
                selection_probability=selected_prob,
            )

        return ActionResult(
            action=selected_action,
            utility=selected_utility,
            inhibited=False,
            conflict_signal=conflict_signal,
            selection_probability=selected_prob,
        )

    # ------------------------------------------------------------------
    # Integrated Pipeline
    # ------------------------------------------------------------------
    def process(
        self,
        candidate_actions: List[Action],
        top_memories: Optional[List[Tuple[str, float]]] = None,
        goal: Optional[str] = None,
        goal_priority: float = 0.5,
        deterministic: bool = False,
    ) -> ActionResult:
        """통합 처리 파이프라인.

        1. 목표 설정
        2. MemoryRank 결과 로드 (있으면)
        3. 감쇠 적용
        4. 행동 선택

        Args:
            candidate_actions: 후보 행동 리스트
            top_memories: MemoryRank 결과 (optional)
            goal: 현재 목표 (optional)
            goal_priority: 목표 우선순위
            deterministic: argmax 선택 여부

        Returns:
            ActionResult
        """
        # 1. 목표 설정
        if goal:
            self.set_goal(goal, goal_priority)

        # 2. MemoryRank 결과 로드
        if top_memories:
            self.load_from_memoryrank(top_memories)

        # 3. 감쇠 적용
        self.update_decay()

        # 4. 행동 선택
        return self.select_action(candidate_actions, deterministic)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def get_state(self) -> Dict:
        """현재 PFC 상태 반환."""
        return {
            "working_memory_count": len(self._working_memory),
            "working_memory_capacity": self.config.working_memory_capacity,
            "current_goal": self._current_goal,
            "goal_priority": self._current_goal_priority,
            "config": {
                "decay_rate": self.config.decay_rate,
                "risk_aversion": self.config.risk_aversion,
                "inhibition_threshold": self.config.inhibition_threshold,
                "decision_temperature": self.config.decision_temperature,
            },
        }
