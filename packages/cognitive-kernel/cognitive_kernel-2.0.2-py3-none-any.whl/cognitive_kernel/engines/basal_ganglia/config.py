"""
Basal Ganglia Engine Configuration
기저핵 엔진 설정

Author: GNJz (Qquarts)
Version: 1.0.0-alpha
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class BasalGangliaConfig:
    """
    기저핵 엔진 설정
    
    생물학적 근거:
    - 기저핵은 개인차가 큰 뇌 영역 (충동성, 인내심 등)
    - 이 설정을 통해 다양한 "행동 성향"을 구현 가능
    
    수식 참고:
    - Q-value 업데이트: Q(s,a) ← Q(s,a) + α[R + γ·max(Q(s',a')) - Q(s,a)]
      → alpha = 학습률
      → gamma = 할인율 (미래 보상)
    - 행동 선택: P(a) = softmax(Q(s,a) / τ)
      → tau = 소프트맥스 온도 (탐색 vs 활용)
    - 습관 강도: H = H + β·(success - H)
      → habit_beta = 습관 강화율
    """
    
    # ===== 학습 파라미터 =====
    alpha: float = 0.1                  # 학습률 (Q-learning)
    gamma: float = 0.9                   # 할인율 (미래 보상 중시도)
    tau: float = 0.5                     # 소프트맥스 온도 (탐색 vs 활용)
    
    # ===== 습관 파라미터 =====
    habit_threshold: float = 0.7         # 습관화 임계값 (0~1)
    habit_beta: float = 0.1              # 습관 강화율
    
    # ===== 감쇠/보너스 =====
    decay_rate: float = 0.01             # Q-값 감쇠율 (사용하지 않는 행동 잊기)
    exploration_bonus: float = 0.2       # 탐색 보너스 (새 행동 초기 Q-값)
    
    # ===== 도파민 설정 =====
    dopamine_baseline: float = 0.5       # 도파민 기준선 (0~1)
    dopamine_boost_factor: float = 0.6   # 도파민 보정 계수 (학습률 조절)
    
    # ===== 메모리 설정 =====
    max_history: int = 100               # 최대 행동 기록 수
    
    # ===== 성향 설정 (Bias) =====
    # 외부에서 주입 가능한 행동 성향
    impulsivity: Optional[float] = None  # 충동성 (0~1): 높으면 탐색↑, 습관 형성↑
    patience: Optional[float] = None     # 인내심 (0~1): 높으면 미래 보상 중시
    
    def __post_init__(self):
        """설정 검증 및 성향 적용"""
        # 충동성 적용
        if self.impulsivity is not None:
            imp = max(0.0, min(1.0, self.impulsivity))
            self.tau = 0.5 + (imp * 0.5)  # 0.5~1.0
            self.habit_threshold = 0.7 - (imp * 0.2)  # 0.5~0.7
        
        # 인내심 적용
        if self.patience is not None:
            pat = max(0.0, min(1.0, self.patience))
            self.gamma = 0.8 + (pat * 0.15)  # 0.8~0.95
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'learning': {
                'alpha': self.alpha,
                'gamma': self.gamma,
                'tau': self.tau,
            },
            'habit': {
                'threshold': self.habit_threshold,
                'beta': self.habit_beta,
            },
            'decay': {
                'rate': self.decay_rate,
                'exploration_bonus': self.exploration_bonus,
            },
            'dopamine': {
                'baseline': self.dopamine_baseline,
                'boost_factor': self.dopamine_boost_factor,
            },
            'memory': {
                'max_history': self.max_history,
            },
            'bias': {
                'impulsivity': self.impulsivity,
                'patience': self.patience,
            },
        }

