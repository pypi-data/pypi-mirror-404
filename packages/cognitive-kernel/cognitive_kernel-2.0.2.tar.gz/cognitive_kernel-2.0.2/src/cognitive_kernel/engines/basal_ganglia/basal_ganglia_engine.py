"""
Basal Ganglia Engine
기저핵 엔진 - 행동 선택 및 습관 형성 시스템

Author: GNJz (Qquarts)
Version: 1.0.0-alpha

생물학적 모델:
    기저핵 = 뇌의 "행동 게이트키퍼"
    
    1. 행동 선택 (Action Selection)
       - 여러 행동 옵션 중 하나만 실행 (Go/NoGo)
       - 나머지는 억제
       
    2. 습관 형성 (Habit Formation)
       - 반복된 행동 → 자동화
       - 전두엽 우회 → 빠른 실행
       
    3. 보상 학습 (Reward Learning)
       - 도파민 신호 기반
       - Q-Learning과 유사

핵심 수식:
    Q-value 업데이트: Q(s,a) ← Q(s,a) + α[R + γ·max(Q(s',a')) - Q(s,a)]
    행동 선택: P(a) = softmax(Q(s,a) / τ)
    습관 강도: H = H + β·(success - H)
    도파민 보정: Q_update = Q_update · (1 + D_boost)

참고 논문:
    - Schultz (1997): Dopamine reward prediction
    - Graybiel (2008): Habits, rituals, and the evaluative brain
    - Frank (2005): Go/NoGo model of basal ganglia
"""

import math
import time
import random
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

from .data_types import ActionType, Action, ActionResult
from .config import BasalGangliaConfig


class BasalGangliaEngine:
    """
    기저핵 엔진 (Basal Ganglia Engine)
    
    행동 선택 및 습관 형성 시스템
    
    구조:
        Striatum (선조체) - 입력, 상황-행동 매핑
        GPi/SNr (담창구) - 출력, Go/NoGo 결정
        STN (시상하핵) - 억제 조절
        
    학습:
        도파민 신호 기반 강화학습 (TD-Learning)
    """
    
    def __init__(self, 
                 config: Optional[BasalGangliaConfig] = None,
                 use_hash: bool = False):
        """
        기저핵 엔진 초기화
        
        Args:
            config: 설정 객체 (None이면 기본 설정 사용)
            use_hash: 긴 컨텍스트를 해시로 저장 (메모리 최적화)
        """
        # 설정
        self.config = config if config else BasalGangliaConfig()
        
        # ===== Q-테이블 (상황 → 행동 → 가치) =====
        # {context: {action_name: Action}}
        self.q_table: Dict[str, Dict[str, Action]] = defaultdict(dict)
        
        # 컨텍스트 해싱 모드
        self.use_hash = use_hash
        
        # ===== 도파민 상태 =====
        self.dopamine_level = self.config.dopamine_baseline  # 현재 도파민 (0~1)
        
        # ===== 최근 행동 기록 =====
        self.recent_actions: List[Tuple[str, str, float]] = []  # (context, action, reward)
        
        # ===== 통계 =====
        self.stats = {
            'total_decisions': 0,
            'habit_executions': 0,
            'deliberate_executions': 0,
            'explorations': 0,
            'total_reward': 0.0,
        }
    
    # ============================================
    # 1. 행동 선택 (Action Selection)
    # ============================================
    
    def select_action(self, 
                      context: str, 
                      possible_actions: List[str],
                      allow_exploration: bool = True) -> ActionResult:
        """
        행동 선택 (Go/NoGo/Explore)
        
        1. 습관 체크 → 자동 실행 (Fast Path)
        2. Q-값 기반 선택 → 의식적 결정 (Slow Path)
        3. 탐색 → 새로운 시도
        
        Args:
            context: 현재 상황/맥락
            possible_actions: 가능한 행동 목록
            allow_exploration: 탐색 허용 여부
            
        Returns:
            ActionResult
        """
        self.stats['total_decisions'] += 1
        
        # 컨텍스트 정규화
        context = self._normalize_context(context)
        
        # 1. 습관 체크 (Fast Path)
        habit_action = self._check_habit(context, possible_actions)
        if habit_action:
            self.stats['habit_executions'] += 1
            return ActionResult(
                action=habit_action,
                decision=ActionType.GO,
                confidence=habit_action.habit_strength,
                is_automatic=True,
                reasoning=f"습관: '{habit_action.name}' (강도: {habit_action.habit_strength:.2f})"
            )
        
        # 2. Q-값 기반 선택 (Slow Path)
        actions = self._get_or_create_actions(context, possible_actions)
        
        if not actions:
            # 행동 없음
            return ActionResult(
                action=Action(name="none", context=context),
                decision=ActionType.NOGO,
                confidence=0.0,
                is_automatic=False,
                reasoning="가능한 행동 없음"
            )
        
        # 탐색 vs 활용 결정
        if allow_exploration and self._should_explore():
            # 탐색: 랜덤 또는 낮은 Q-값 행동
            self.stats['explorations'] += 1
            action = self._explore(actions)
            return ActionResult(
                action=action,
                decision=ActionType.EXPLORE,
                confidence=0.3,
                is_automatic=False,
                reasoning=f"탐색: '{action.name}' (새로운 시도)"
            )
        
        # 활용: Q-값 기반 소프트맥스 선택
        self.stats['deliberate_executions'] += 1
        action, confidence = self._exploit(actions)
        
        # Go/NoGo 결정
        decision = ActionType.GO if confidence > 0.3 else ActionType.NOGO
        
        return ActionResult(
            action=action,
            decision=decision,
            confidence=confidence,
            is_automatic=False,
            reasoning=f"선택: '{action.name}' (Q={action.q_value:.2f}, 확신: {confidence:.2f})"
        )
    
    def _check_habit(self, context: str, possible_actions: List[str]) -> Optional[Action]:
        """
        습관 체크
        
        습관화된 행동이 있으면 즉시 반환 (Fast Path)
        """
        if context not in self.q_table:
            return None
        
        for action_name in possible_actions:
            if action_name in self.q_table[context]:
                action = self.q_table[context][action_name]
                if action.is_habit:
                    return action
        
        return None
    
    def _get_or_create_actions(self, context: str, action_names: List[str]) -> List[Action]:
        """행동 객체 가져오기 또는 생성"""
        actions = []
        
        for name in action_names:
            if name in self.q_table[context]:
                actions.append(self.q_table[context][name])
            else:
                # 새 행동 생성
                action = Action(
                    name=name,
                    context=context,
                    q_value=self.config.exploration_bonus  # 초기값에 탐색 보너스
                )
                self.q_table[context][name] = action
                actions.append(action)
        
        return actions
    
    def _should_explore(self) -> bool:
        """
        탐색할지 결정 (epsilon-greedy 유사)
        
        수식:
            explore_prob = 0.1 + (1 - dopamine_level) * 0.2
            → 도파민이 낮으면 탐색 증가 (새로운 보상 찾기)
        """
        explore_prob = 0.1 + (1 - self.dopamine_level) * 0.2
        return random.random() < explore_prob
    
    def _explore(self, actions: List[Action]) -> Action:
        """
        탐색: 낮은 실행 횟수 행동 선호
        
        수식:
            weights = [1.0 / (execution_count + 1) for action in actions]
            → 실행 횟수가 적은 행동에 높은 가중치
        """
        weights = [1.0 / (a.execution_count + 1) for a in actions]
        total = sum(weights)
        probs = [w / total for w in weights]
        
        return random.choices(actions, weights=probs)[0]
    
    def _exploit(self, actions: List[Action]) -> Tuple[Action, float]:
        """
        활용: Q-값 기반 소프트맥스 선택
        
        수식:
            P(a) = exp(Q(s,a) / τ) / Σ exp(Q(s,a') / τ)
            → Q-값이 높을수록 선택 확률 증가
            → τ (온도)가 높을수록 탐색 증가
        """
        tau = self.config.tau
        
        # 소프트맥스 확률 계산
        q_values = [a.q_value for a in actions]
        max_q = max(q_values) if q_values else 0
        
        # 수치 안정성을 위해 max 빼기
        exp_values = [math.exp((q - max_q) / tau) for q in q_values]
        total = sum(exp_values)
        probs = [e / total for e in exp_values]
        
        # 선택
        selected = random.choices(actions, weights=probs)[0]
        confidence = probs[actions.index(selected)]
        
        return selected, confidence
    
    def _normalize_context(self, context: str) -> str:
        """
        컨텍스트 정규화
        
        use_hash=True 시 긴 문자열 해싱 (메모리 최적화)
        """
        normalized = context.lower().strip()
        
        if self.use_hash and len(normalized) > 50:
            # 긴 컨텍스트는 해시로 변환 (메모리 절약)
            return hashlib.md5(normalized.encode()).hexdigest()
        
        # 기본: 50자로 자름 (디버깅 용이)
        return normalized[:50]
    
    # ============================================
    # 2. 학습 (Learning)
    # ============================================
    
    def learn(self, context: str, action_name: str, reward: float, 
              next_context: Optional[str] = None):
        """
        보상 학습 (TD-Learning)
        
        수식:
            Q(s,a) ← Q(s,a) + α[R + γ·max(Q(s',a')) - Q(s,a)]
            
            - α (alpha): 학습률
            - γ (gamma): 할인율 (미래 보상)
            - R: 현재 보상
            - max(Q(s',a')): 다음 상태의 최대 Q-값
        
        도파민 보정:
            learning_rate = alpha * (1.0 + dopamine_boost)
            → 도파민이 높으면 학습률 증가
        
        Args:
            context: 상황
            action_name: 실행한 행동
            reward: 받은 보상 (-1 ~ +1)
            next_context: 다음 상황 (None이면 종료 상태)
        """
        context = self._normalize_context(context)
        
        # 행동 가져오기
        if action_name not in self.q_table[context]:
            self.q_table[context][action_name] = Action(
                name=action_name, context=context
            )
        
        action = self.q_table[context][action_name]
        
        # 실행 기록
        action.execution_count += 1
        action.last_executed = time.time()
        
        if reward > 0:
            action.success_count += 1
        
        # TD 업데이트
        alpha = self.config.alpha
        gamma = self.config.gamma
        
        # 다음 상태의 최대 Q-값
        if next_context:
            next_context = self._normalize_context(next_context)
            next_q_values = [a.q_value for a in self.q_table[next_context].values()]
            max_next_q = max(next_q_values) if next_q_values else 0
        else:
            max_next_q = 0
        
        # Q-value 업데이트
        td_error = reward + gamma * max_next_q - action.q_value
        
        # 도파민 보정 (보상 기반 학습 강화)
        # 도파민이 높으면 학습률 증가 (기준선 기준으로 ±0.5)
        dopamine_boost = (self.dopamine_level - self.config.dopamine_baseline) * self.config.dopamine_boost_factor
        dopamine_boost = max(-0.5, min(0.5, dopamine_boost))  # -0.5 ~ 0.5로 제한
        
        # 도파민 보정 적용: (1 + D_boost)로 학습률 조절
        learning_rate = alpha * (1.0 + dopamine_boost)
        action.q_value += learning_rate * td_error
        
        # 도파민 업데이트 (TD error 기반)
        self._update_dopamine(td_error)
        
        # 습관 강화/약화 (성공/실패 시)
        if reward > 0:
            self._strengthen_habit(action)
        elif reward < 0:
            self._weaken_habit(action)
        
        # 기록
        self.recent_actions.append((context, action_name, reward))
        self.recent_actions = self.recent_actions[-self.config.max_history:]
        self.stats['total_reward'] += reward
    
    def set_dopamine_level(self, level: float) -> None:
        """
        도파민 레벨 설정
        
        외부 모듈(예: Hypothalamus)에서 도파민 레벨을 주입할 수 있도록 함
        
        Args:
            level: 도파민 레벨 (0.0 ~ 1.0)
        """
        self.dopamine_level = max(0.0, min(1.0, level))
    
    def _update_dopamine(self, td_error: float):
        """
        도파민 업데이트 (TD error 기반)
        
        수식:
            delta = td_error * 0.1
            dopamine_level = clamp(dopamine_level + delta, 0, 1)
            
            - TD error > 0: 예상보다 좋음 → 도파민 증가
            - TD error < 0: 예상보다 나쁨 → 도파민 감소
        
        기준선으로 서서히 복귀:
            dopamine_level += 0.05 * (baseline - dopamine_level)
        """
        # TD error 기반 변화
        delta = td_error * 0.1
        self.dopamine_level = max(0, min(1, self.dopamine_level + delta))
        
        # 기준선으로 서서히 복귀
        decay = 0.05
        self.dopamine_level += decay * (self.config.dopamine_baseline - self.dopamine_level)
    
    def _strengthen_habit(self, action: Action):
        """
        습관 강화
        
        수식:
            H = H + β·(1 - H)
            → 점진적으로 1에 접근
        """
        beta = self.config.habit_beta
        action.habit_strength += beta * (1 - action.habit_strength)
    
    def _weaken_habit(self, action: Action):
        """
        습관 약화
        
        수식:
            H = H - (β/2)·H
            → 약화는 강화보다 느리게
        """
        beta = self.config.habit_beta * 0.5  # 약화는 더 느리게
        action.habit_strength = max(0, action.habit_strength - beta)
    
    # ============================================
    # 3. 습관 관리
    # ============================================
    
    def get_habits(self) -> List[Action]:
        """모든 습관화된 행동 반환"""
        habits = []
        for context, actions in self.q_table.items():
            for action in actions.values():
                if action.is_habit:
                    habits.append(action)
        return habits
    
    def break_habit(self, context: str, action_name: str):
        """습관 깨기"""
        context = self._normalize_context(context)
        if context in self.q_table and action_name in self.q_table[context]:
            self.q_table[context][action_name].habit_strength = 0.0
    
    def decay_all(self):
        """
        모든 Q-값 감쇠 (사용하지 않는 행동 잊기)
        
        수식:
            Q(s,a) = Q(s,a) * (1 - decay_rate)
        """
        decay = self.config.decay_rate
        for context, actions in self.q_table.items():
            for action in actions.values():
                action.q_value *= (1 - decay)
                # 너무 오래된 습관도 약화
                time_since = time.time() - action.last_executed
                if time_since > 3600:  # 1시간 이상
                    action.habit_strength *= 0.99
    
    # ============================================
    # 4. 상태 조회
    # ============================================
    
    def get_best_action(self, context: str) -> Optional[Action]:
        """특정 상황에서 최선의 행동"""
        context = self._normalize_context(context)
        if context not in self.q_table:
            return None
        
        actions = list(self.q_table[context].values())
        if not actions:
            return None
        
        return max(actions, key=lambda a: a.q_value)
    
    def get_state(self) -> Dict[str, Any]:
        """전체 상태 반환"""
        habits = self.get_habits()
        
        return {
            'dopamine': round(self.dopamine_level, 3),
            'total_contexts': len(self.q_table),
            'total_actions': sum(len(a) for a in self.q_table.values()),
            'habits': [
                {
                    'context': h.context, 
                    'action': h.name, 
                    'strength': round(h.habit_strength, 3)
                }
                for h in habits[:5]  # 상위 5개
            ],
            'stats': self.stats.copy(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return self.stats.copy()

