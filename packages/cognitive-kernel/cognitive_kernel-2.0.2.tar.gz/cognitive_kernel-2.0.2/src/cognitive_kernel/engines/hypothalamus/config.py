"""
Hypothalamus Engine Configuration
시상하부 엔진 설정

Author: GNJz (Qquarts)
Version: 1.0.0-alpha
"""

from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class HypothalamusConfig:
    """
    시상하부 엔진 설정
    
    생물학적 근거:
    - 시상하부는 개인차가 큰 뇌 영역 (성격, 대사 속도 등)
    - 이 설정을 통해 다양한 "성격"을 구현 가능
    
    수식 참고:
    - 에너지 감쇠: E(t) = E_0 · e^(-λ·t) + E_min
      → energy_decay = λ (감쇠율)
    - 지루함 증가: B(t) = B_0 + α·t·(1-S)
      → boredom_increase = α (증가율)
    - 도파민 반응: D = D_base + β·R·(1-D)
      → dopamine_boost = β (보상 반응율)
    """
    
    # ===== 임계값 설정 =====
    sleep_threshold: float = 0.2        # 에너지 이 이하 → 수면 필요
    critical_threshold: float = 0.1     # 에너지 이 이하 → 강제 수면
    boredom_threshold: float = 0.7      # 지루함 이 이상 → 탐험 필요
    stress_threshold: float = 0.8       # 스트레스 이 이상 → 휴식 필요
    loneliness_threshold: float = 0.7   # 외로움 이 이상 → 상호작용 필요
    curiosity_threshold: float = 0.8    # 호기심 이 이상 → 학습 필요
    
    # ===== 감쇠/증가율 (대사 속도) =====
    energy_decay: float = 0.005        # 틱당 에너지 감소 (기본값)
    energy_recovery: float = 0.02       # 수면 시 에너지 회복 (기본값)
    boredom_increase: float = 0.01     # 틱당 지루함 증가 (자극 없을 때)
    boredom_decrease: float = 0.05     # 자극 시 지루함 감소
    dopamine_decay: float = 0.01       # 도파민 자연 감소
    dopamine_boost: float = 0.15        # 보상 시 도파민 증가
    stress_increase: float = 0.02      # 위협/부하 시 스트레스 증가
    stress_decrease: float = 0.01      # 자연 스트레스 감소
    loneliness_increase: float = 0.005  # 혼자 있을 때 외로움 증가
    curiosity_recovery: float = 0.02   # 호기심 자연 회복
    
    # ===== 욕구 가중치 (성격 커스터마이징) =====
    # 수식: P = w_E·(1-E) + w_B·B + w_C·C
    # 각 가중치가 높을수록 해당 욕구의 우선순위가 높아짐
    energy_weight: float = 1.5         # 에너지 부족 = 높은 우선순위
    boredom_weight: float = 1.0       # 지루함 가중치
    stress_weight: float = 1.2        # 스트레스 가중치
    loneliness_weight: float = 0.8    # 외로움 가중치
    curiosity_weight: float = 0.9     # 호기심 가중치
    
    # ===== 커스터마이징 =====
    # 외부에서 주입 가능한 추가 설정
    custom_rates: Optional[Dict[str, float]] = None
    custom_weights: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """설정 검증 및 커스터마이징 적용"""
        # 커스터마이징 적용
        if self.custom_rates:
            for key, value in self.custom_rates.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        if self.custom_weights:
            for key, value in self.custom_weights.items():
                weight_key = f"{key}_weight"
                if hasattr(self, weight_key):
                    setattr(self, weight_key, value)
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'thresholds': {
                'sleep': self.sleep_threshold,
                'critical': self.critical_threshold,
                'boredom': self.boredom_threshold,
                'stress': self.stress_threshold,
                'loneliness': self.loneliness_threshold,
                'curiosity': self.curiosity_threshold,
            },
            'rates': {
                'energy_decay': self.energy_decay,
                'energy_recovery': self.energy_recovery,
                'boredom_increase': self.boredom_increase,
                'boredom_decrease': self.boredom_decrease,
                'dopamine_decay': self.dopamine_decay,
                'dopamine_boost': self.dopamine_boost,
                'stress_increase': self.stress_increase,
                'stress_decrease': self.stress_decrease,
                'loneliness_increase': self.loneliness_increase,
                'curiosity_recovery': self.curiosity_recovery,
            },
            'weights': {
                'energy': self.energy_weight,
                'boredom': self.boredom_weight,
                'stress': self.stress_weight,
                'loneliness': self.loneliness_weight,
                'curiosity': self.curiosity_weight,
            },
        }

