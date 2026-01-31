"""
Dynamics Engine
동역학 엔진

엔트로피, 코어 강도, 회전 토크 계산 및 Core Decay 동역학 처리.

Author: GNJz (Qquarts)
Version: 2.0.1+
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Tuple, Any, Union

from .config import DynamicsConfig
from .models import DynamicsState


class DynamicsEngine:
    """
    동역학 엔진
    
    역할:
    - 엔트로피 계산
    - 코어 강도 계산 (Core Decay 포함)
    - 회전 토크 생성
    - 인지적 절규 확인
    - 상태 관리 (히스토리 포함)
    """
    
    def __init__(self, config: Optional[DynamicsConfig] = None):
        """
        Args:
            config: 동역학 엔진 설정 (None이면 기본값 사용)
        """
        self.config = config or DynamicsConfig()
        self.config.validate()
        self.state = DynamicsState()
    
    def calculate_entropy(self, probabilities: List[float]) -> float:
        """
        엔트로피 계산
        
        수식: E = -Σ P(k) ln P(k)
        
        Args:
            probabilities: 확률 분포 리스트
            
        Returns:
            엔트로피 값
        """
        entropy = 0.0
        for prob in probabilities:
            if prob > 0:
                entropy -= prob * math.log(prob)
        
        self.state.entropy = entropy
        return entropy
    
    def calculate_core_strength(
        self,
        memories: List[Dict[str, Any]],
        memory_update_failure: float = 0.0,
        alpha: Optional[float] = None,
    ) -> float:
        """
        코어 강도 계산 (Core Decay 동역학 적용)
        
        수식:
        - 원시 코어: C_raw = α * (Σ importance) / N
        - Core Decay: C(t) = C(0) * exp(-λ * Δt)
        - 시간축 분리: 오래된 기억과 새 기억에 다른 감쇠율 적용
        
        Args:
            memories: 기억 리스트 (각 기억은 timestamp 또는 age 정보 포함 가능)
            memory_update_failure: 새 기억 중요도 반영 실패율 (0~1)
            alpha: 기억 영향 계수 (None이면 config에서 가져옴)
            
        Returns:
            코어 강도 (0~1)
        """
        if alpha is None:
            alpha = self.config.memory_alpha
        
        # 1. 현재 원시 코어 강도 계산 (시간축 분리 적용)
        current_raw_core = 0.0
        if memories:
            current_time = time.time()
            total_importance = 0.0
            
            for m in memories:
                importance = m.get("importance", 0.0)
                
                # 시간축 분리: 오래된 기억 vs 새 기억
                memory_timestamp = m.get("timestamp", current_time)
                memory_age = current_time - memory_timestamp
                
                # 오래된 기억 감쇠 (치매 특성: 최근 기억부터 지워짐)
                if self.config.old_memory_decay_rate > 0 and memory_age > self.config.memory_age_threshold:
                    # 오래된 기억: 더 빠른 감쇠
                    decay_factor = math.exp(-self.config.old_memory_decay_rate * memory_age)
                    importance *= decay_factor
                
                # 새 기억 감쇠 (알츠하이머 특성: 새 기억이 전혀 저장되지 않음)
                if self.config.new_memory_decay_rate > 0 and memory_age <= self.config.memory_age_threshold:
                    # 새 기억: 매우 빠른 감쇠 (거의 즉시 소실)
                    decay_factor = math.exp(-self.config.new_memory_decay_rate * memory_age)
                    importance *= decay_factor
                
                total_importance += importance
            
            # 새 기억의 중요도 반영 차단 (알츠하이머)
            if memory_update_failure > 0:
                total_importance *= (1.0 - memory_update_failure)
            
            current_raw_core = min(
                1.0, alpha * total_importance / len(memories) if memories else 0.0
            )
        
        # 2. Core Decay (물리적 시간 붕괴 항 적용)
        # 수식: C(t) = C(0) * exp(-λ * Δt)
        if self.config.core_decay_rate > 0:
            # 초기화
            if self.state.persistent_core is None:
                self.state.persistent_core = current_raw_core
                self.state.last_decay_time = time.time()
            
            # 시간 경과 계산
            delta_t = time.time() - self.state.last_decay_time
            lambda_decay = self.config.core_decay_rate
            
            # 지수 감쇠 적용
            self.state.persistent_core *= math.exp(-lambda_decay * delta_t)
            core_strength = self.state.persistent_core
            self.state.last_decay_time = time.time()
        else:
            # 정상 모드: 원시 코어 강도 사용
            core_strength = current_raw_core
            self.state.persistent_core = None
            self.state.last_decay_time = None
        
        self.state.core_strength = core_strength
        return core_strength
    
    def generate_torque(
        self,
        options: List[str],
        entropy: float,
        mode: Optional[Union[str, Any]] = None,  # CognitiveMode 또는 문자열
        base_gamma: Optional[float] = None,
        omega: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        회전 토크 생성
        
        수식:
        - 정규화된 엔트로피: E_norm = E / E_max
        - 토크 세기: T = γ * E_norm
        - 회전 토크: T(k) = T * cos(φ - ψ_k)
        
        Args:
            options: 옵션 리스트
            entropy: 현재 엔트로피
            mode: 인지 모드 (CognitiveMode 또는 문자열: "adhd", "asd", "normal" 등)
            base_gamma: 기본 회전 토크 세기 (None이면 config에서 가져옴)
            omega: 세차 속도 (None이면 config에서 가져옴)
            
        Returns:
            옵션별 회전 토크 딕셔너리
        """
        if len(options) <= 1:
            return {}
        
        if base_gamma is None:
            base_gamma = self.config.base_gamma
        if omega is None:
            omega = self.config.omega
        
        # 모드별 gamma 조정 (독립 배포를 위해 유연하게 처리)
        gamma = base_gamma
        if mode is not None:
            # 문자열 모드 처리
            if isinstance(mode, str):
                mode_str = mode.lower()
                if mode_str == "adhd":
                    gamma = base_gamma * 1.5  # ADHD: 더 강한 회전
                elif mode_str == "asd":
                    gamma = base_gamma * 0.5  # ASD: 약한 회전
            # CognitiveMode 객체 처리 (선택적 의존성)
            else:
                try:
                    from ...cognitive_modes import CognitiveMode
                    if mode == CognitiveMode.ADHD:
                        gamma = base_gamma * 1.5
                    elif mode == CognitiveMode.ASD:
                        gamma = base_gamma * 0.5
                except ImportError:
                    # CognitiveMode가 없으면 기본값 사용
                    pass
        
        # 이론적 최대 엔트로피 (균등 분포)
        max_entropy = math.log(len(options))
        # 정규화된 엔트로피 (0~1)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        
        # 토크 세기
        torque_strength = gamma * normalized_entropy
        
        # 옵션별 위상 (균등 분포)
        psi = {
            opt: i * 2 * math.pi / len(options)
            for i, opt in enumerate(options)
        }
        
        # 회전 토크 계산: T(k) = torque_strength * cos(φ - ψ_k)
        auto_torque = {}
        for opt in options:
            auto_torque[opt] = torque_strength * math.cos(
                self.state.precession_phi - psi[opt]
            )
        
        # 위상 업데이트 (느린 시간척도)
        self.state.precession_phi += omega
        # 2π 주기로 정규화
        if self.state.precession_phi >= 2 * math.pi:
            self.state.precession_phi -= 2 * math.pi
        
        return auto_torque
    
    def check_cognitive_distress(
        self,
        entropy: float,
        core_strength: float,
        num_options: int,
    ) -> Tuple[bool, str]:
        """
        인지적 절규 확인
        
        조건:
        - 엔트로피 > 임계값 (최대치의 80%)
        - 코어 강도 < 임계값 (0.3)
        
        Args:
            entropy: 현재 엔트로피
            core_strength: 현재 코어 강도
            num_options: 옵션 수
            
        Returns:
            (절규 여부, 메시지) 튜플
        """
        if num_options <= 1:
            self.state.cognitive_distress = False
            return False, ""
        
        max_entropy = math.log(num_options)
        entropy_threshold = max_entropy * self.config.entropy_threshold_ratio
        
        if entropy > entropy_threshold and core_strength < self.config.core_distress_threshold:
            self.state.cognitive_distress = True
            return True, "기억이 안 나..."
        else:
            self.state.cognitive_distress = False
            return False, ""
    
    def update_history(self, entropy: float, core_strength: float) -> None:
        """
        히스토리 업데이트
        
        Args:
            entropy: 엔트로피 값
            core_strength: 코어 강도 값
        """
        self.state.entropy_history.append(entropy)
        if len(self.state.entropy_history) > self.config.history_size:
            self.state.entropy_history = self.state.entropy_history[-self.config.history_size:]
        
        self.state.core_strength_history.append(core_strength)
        if len(self.state.core_strength_history) > self.config.history_size:
            self.state.core_strength_history = self.state.core_strength_history[-self.config.history_size:]
    
    def reset(self) -> None:
        """상태 초기화"""
        self.state.reset()
    
    def get_state(self) -> DynamicsState:
        """상태 조회"""
        return self.state
    
    def get_status(self) -> Dict[str, Any]:
        """상태 딕셔너리 반환"""
        return {
            "entropy": self.state.entropy,
            "core_strength": self.state.core_strength,
            "precession_phi": self.state.precession_phi,
            "cognitive_distress": self.state.cognitive_distress,
            "persistent_core": self.state.persistent_core,
            "entropy_history_length": len(self.state.entropy_history),
            "core_strength_history_length": len(self.state.core_strength_history),
        }

