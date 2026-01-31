"""
Dynamics Engine Configuration
동역학 엔진 설정 클래스

Author: GNJz (Qquarts)
Version: 2.0.1+
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DynamicsConfig:
    """
    동역학 엔진 설정
    
    파라미터:
    - base_gamma: 기본 회전 토크 세기
    - omega: 세차 속도 (느린 시간척도)
    - core_decay_rate: 코어 감쇠율 (초당, 0이면 정상)
    - memory_update_failure: 새 기억 중요도 반영 실패율 (0~1)
    - loop_integrity_decay: 루프 무결성 감쇠율 (0~1)
    - entropy_threshold_ratio: 인지적 절규 엔트로피 임계값 비율 (0~1)
    - core_distress_threshold: 코어 절규 임계값 (0~1)
    - history_size: 히스토리 최대 크기
    """
    
    # 회전 토크 설정
    base_gamma: float = 0.3  # 기본 회전 토크 세기
    omega: float = 0.05  # 세차 속도 (느린 시간척도)
    
    # Core Decay 설정
    core_decay_rate: float = 0.0  # 코어 감쇠율 (초당)
    memory_update_failure: float = 0.0  # 새 기억 중요도 반영 실패율 (0~1)
    loop_integrity_decay: float = 0.0  # 루프 무결성 감쇠율 (0~1)
    
    # 시간축 분리 (오래된 기억 vs 새 기억)
    old_memory_decay_rate: float = 0.0  # 오래된 기억 감쇠율 (초당, 치매 특성)
    new_memory_decay_rate: float = 0.0  # 새 기억 감쇠율 (초당, 알츠하이머 특성)
    memory_age_threshold: float = 3600.0  # 기억 나이 임계값 (초, 이보다 오래되면 "오래된 기억")
    
    # 인지적 절규 설정
    entropy_threshold_ratio: float = 0.8  # 엔트로피 임계값 비율 (최대치의 80%)
    core_distress_threshold: float = 0.3  # 코어 절규 임계값
    
    # 히스토리 설정
    history_size: int = 100  # 히스토리 최대 크기
    
    # 기억 영향 계수
    memory_alpha: float = 0.5  # 기억 영향 계수 (코어 강도 계산용)
    
    def validate(self) -> None:
        """설정 유효성 검증"""
        assert 0.0 <= self.base_gamma <= 1.0, "base_gamma must be in [0, 1]"
        assert self.omega > 0, "omega must be positive"
        assert self.core_decay_rate >= 0, "core_decay_rate must be non-negative"
        assert 0.0 <= self.memory_update_failure <= 1.0, "memory_update_failure must be in [0, 1]"
        assert 0.0 <= self.loop_integrity_decay <= 1.0, "loop_integrity_decay must be in [0, 1]"
        assert self.old_memory_decay_rate >= 0, "old_memory_decay_rate must be non-negative"
        assert self.new_memory_decay_rate >= 0, "new_memory_decay_rate must be non-negative"
        assert self.memory_age_threshold > 0, "memory_age_threshold must be positive"
        assert 0.0 <= self.entropy_threshold_ratio <= 1.0, "entropy_threshold_ratio must be in [0, 1]"
        assert 0.0 <= self.core_distress_threshold <= 1.0, "core_distress_threshold must be in [0, 1]"
        assert self.history_size > 0, "history_size must be positive"
        assert 0.0 <= self.memory_alpha <= 1.0, "memory_alpha must be in [0, 1]"

