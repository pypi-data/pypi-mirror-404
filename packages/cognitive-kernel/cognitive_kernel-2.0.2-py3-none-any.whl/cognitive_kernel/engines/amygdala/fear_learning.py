"""
Rescorla-Wagner Fear Learning Module
공포 조건화 학습 모듈

이 모듈은 고전적 조건화(Classical Conditioning)의 수학적 기반인
Rescorla-Wagner 모델을 구현한다.

📐 핵심 수식:
    ΔV = α × β × (λ - V)
    
    여기서:
    - V: 현재 연합 강도 (associative strength)
    - ΔV: 연합 강도의 변화량
    - α: 조건 자극(CS)의 현저성 (0~1)
    - β: 무조건 자극(US)에 대한 학습률 (0~1)
    - λ: 무조건 자극이 지원하는 최대 연합 강도

🔬 이론적 배경:
    Rescorla & Wagner (1972)는 Pavlovian 조건화에서 연합 학습이
    **예측 오차(prediction error)**에 비례한다고 제안했다.
    
    - λ - V: "놀라움(surprise)" 또는 예측 오차
    - 이미 예측된 결과(V ≈ λ)는 추가 학습을 유발하지 않음
    - 예상치 못한 결과(V << λ)는 강한 학습을 유발함

⚠️ 주의:
    이 모델은 공포 학습의 한 측면만을 단순화한 것이다.
    실제 편도체의 공포 회로는 훨씬 복잡하며, 다음을 포함한다:
    - 측기저 편도체(BLA)의 시냅스 가소성
    - 중심 편도체(CeA)의 출력 조절
    - 해마와의 맥락 의존적 상호작용
    - 전전두엽 피질의 하향 조절

📚 참고 문헌:
    - Rescorla, R. A., & Wagner, A. R. (1972). A theory of Pavlovian 
      conditioning: Variations in the effectiveness of reinforcement 
      and nonreinforcement.
    - Schultz, W., Dayan, P., & Montague, P. R. (1997). A neural 
      substrate of prediction and reward. Science.

Author: GNJz (Qquarts)
Version: 1.0.0
License: MIT License
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import time


@dataclass
class FearAssociation:
    """
    공포 연합 (CS-US 페어링)
    
    조건 자극(CS)과 무조건 자극(US) 간의 연합 강도를 추적한다.
    
    Attributes:
        cs_id: 조건 자극 식별자 (예: "bell", "context_A")
        us_id: 무조건 자극 식별자 (예: "shock", "loud_noise")
        strength: 현재 연합 강도 V (0~1)
        acquisition_count: 획득 시행 횟수
        extinction_count: 소거 시행 횟수
        last_update: 마지막 업데이트 시간
    """
    cs_id: str
    us_id: str = "aversive_us"
    strength: float = 0.0
    acquisition_count: int = 0
    extinction_count: int = 0
    last_update: float = field(default_factory=time.time)
    
    # 학습 이력 (연구용)
    history: List[Tuple[float, float, str]] = field(default_factory=list)
    # (timestamp, strength, event_type)


@dataclass
class RescorlaWagnerConfig:
    """
    Rescorla-Wagner 모델 설정
    
    파라미터 선택에 대한 고려:
    - alpha_cs: CS 현저성. 강렬한 자극(밝은 빛, 큰 소리)일수록 높음
    - beta_acquisition: US 제시 시 학습률. 강한 US일수록 높음
    - beta_extinction: US 생략 시 학습률. 일반적으로 beta_acquisition보다 낮음
    - lambda_max: US가 지원하는 최대 연합 강도
    
    ⚠️ 이 값들은 경험적 추정치이며, 실제 생물학적 파라미터와
       직접적으로 대응하지 않을 수 있다.
    """
    # 학습 파라미터
    alpha_cs: float = 0.5           # CS 현저성 (0~1)
    beta_acquisition: float = 0.3   # 획득 학습률 (US 제시)
    beta_extinction: float = 0.1    # 소거 학습률 (US 생략)
    lambda_max: float = 1.0         # 최대 연합 강도
    
    # 자발적 회복 (Spontaneous Recovery)
    # 소거 후 시간 경과에 따른 공포 재출현
    spontaneous_recovery_rate: float = 0.01  # 시간당 회복률
    spontaneous_recovery_cap: float = 0.5    # 회복 상한선 (원래 강도의 비율)
    
    # 일반화 (Generalization)
    generalization_decay: float = 0.3  # 유사 자극에 대한 감쇠율


class RescorlaWagnerLearner:
    """
    Rescorla-Wagner 공포 학습 모듈
    
    이 클래스는 고전적 조건화의 획득(acquisition)과 소거(extinction)를
    모델링한다. 연구 및 시뮬레이션 목적으로 설계되었다.
    
    💡 사용 시나리오:
    
    1. PTSD 공포 조건화 시뮬레이션:
       - 외상 사건 후 neutral cue가 공포 반응과 연합되는 과정
       - 노출 치료(exposure therapy)를 통한 소거 과정
    
    2. 공포 일반화 연구:
       - 원래 CS와 유사한 자극에 대한 공포 반응 확산
       - 과잉 일반화가 불안장애에서 관찰되는 현상과의 관련성
    
    3. 자발적 회복 관찰:
       - 소거 후에도 공포가 재출현하는 현상
       - 재발(relapse) 메커니즘 탐구
    
    Example:
        >>> learner = RescorlaWagnerLearner()
        >>> 
        >>> # 공포 획득: CS(종소리)와 US(전기 충격) 페어링
        >>> for _ in range(10):
        ...     learner.acquisition_trial("bell", us_intensity=0.8)
        >>> 
        >>> # 현재 공포 수준 확인
        >>> fear = learner.get_fear_level("bell")
        >>> print(f"공포 수준: {fear:.2f}")  # 높은 값 예상
        >>> 
        >>> # 소거 시행: CS만 제시 (US 없음)
        >>> for _ in range(20):
        ...     learner.extinction_trial("bell")
        >>> 
        >>> fear_after = learner.get_fear_level("bell")
        >>> print(f"소거 후: {fear_after:.2f}")  # 감소된 값 예상
    """
    
    def __init__(self, config: Optional[RescorlaWagnerConfig] = None):
        self.config = config or RescorlaWagnerConfig()
        self.associations: Dict[str, FearAssociation] = {}
        self._peak_strengths: Dict[str, float] = {}  # 자발적 회복 계산용
        
    def acquisition_trial(
        self, 
        cs_id: str, 
        us_intensity: float = 1.0,
        alpha_override: Optional[float] = None
    ) -> Dict:
        """
        공포 획득 시행 (CS + US 페어링)
        
        Rescorla-Wagner 업데이트:
            ΔV = α × β × (λ - V)
            V_new = V + ΔV
        
        Args:
            cs_id: 조건 자극 식별자
            us_intensity: 무조건 자극 강도 (0~1). λ를 조절함
            alpha_override: CS 현저성 오버라이드 (선택적)
        
        Returns:
            Dict with:
                - delta_v: 연합 강도 변화량
                - new_strength: 새 연합 강도
                - prediction_error: 예측 오차 (λ - V)
        """
        # 연합 생성 또는 조회
        if cs_id not in self.associations:
            self.associations[cs_id] = FearAssociation(cs_id=cs_id)
        
        assoc = self.associations[cs_id]
        V = assoc.strength
        
        # 파라미터
        alpha = alpha_override if alpha_override is not None else self.config.alpha_cs
        beta = self.config.beta_acquisition
        lambda_us = self.config.lambda_max * us_intensity
        
        # Rescorla-Wagner 업데이트
        prediction_error = lambda_us - V
        delta_v = alpha * beta * prediction_error
        
        # 강도 업데이트 (0~1 범위 유지)
        new_strength = max(0.0, min(1.0, V + delta_v))
        
        assoc.strength = new_strength
        assoc.acquisition_count += 1
        assoc.last_update = time.time()
        assoc.history.append((time.time(), new_strength, "acquisition"))
        
        # 최고점 기록 (자발적 회복용)
        if new_strength > self._peak_strengths.get(cs_id, 0):
            self._peak_strengths[cs_id] = new_strength
        
        return {
            'cs_id': cs_id,
            'old_strength': V,
            'delta_v': delta_v,
            'new_strength': new_strength,
            'prediction_error': prediction_error,
            'trial_type': 'acquisition'
        }
    
    def extinction_trial(
        self, 
        cs_id: str,
        alpha_override: Optional[float] = None
    ) -> Dict:
        """
        공포 소거 시행 (CS만 제시, US 없음)
        
        소거에서는 λ = 0 (US가 없으므로)
            ΔV = α × β_extinction × (0 - V) = -α × β_extinction × V
        
        🔬 관찰 사항:
            소거는 연합을 "삭제"하는 것이 아니라, 새로운 억제 연합을
            형성하는 것으로 해석된다 (Bouton, 2004).
            이것이 자발적 회복, 맥락 갱신 등의 현상을 설명한다.
        
        Args:
            cs_id: 조건 자극 식별자
            alpha_override: CS 현저성 오버라이드 (선택적)
        
        Returns:
            Dict with extinction trial results
        """
        if cs_id not in self.associations:
            return {'cs_id': cs_id, 'error': 'no_association'}
        
        assoc = self.associations[cs_id]
        V = assoc.strength
        
        alpha = alpha_override if alpha_override is not None else self.config.alpha_cs
        beta = self.config.beta_extinction
        
        # 소거: λ = 0
        prediction_error = 0.0 - V
        delta_v = alpha * beta * prediction_error  # 음수
        
        new_strength = max(0.0, V + delta_v)
        
        assoc.strength = new_strength
        assoc.extinction_count += 1
        assoc.last_update = time.time()
        assoc.history.append((time.time(), new_strength, "extinction"))
        
        return {
            'cs_id': cs_id,
            'old_strength': V,
            'delta_v': delta_v,
            'new_strength': new_strength,
            'prediction_error': prediction_error,
            'trial_type': 'extinction'
        }
    
    def get_fear_level(
        self, 
        cs_id: str, 
        include_spontaneous_recovery: bool = True
    ) -> float:
        """
        현재 공포 수준 조회
        
        Args:
            cs_id: 조건 자극 식별자
            include_spontaneous_recovery: 자발적 회복 포함 여부
        
        Returns:
            공포 수준 (0~1)
        """
        if cs_id not in self.associations:
            return 0.0
        
        assoc = self.associations[cs_id]
        strength = assoc.strength
        
        if include_spontaneous_recovery and cs_id in self._peak_strengths:
            # 자발적 회복 계산
            # 소거 후 시간이 경과하면 공포가 부분적으로 회복됨
            time_since_update = time.time() - assoc.last_update
            hours_passed = time_since_update / 3600.0
            
            peak = self._peak_strengths[cs_id]
            recovery_ceiling = peak * self.config.spontaneous_recovery_cap
            
            if strength < recovery_ceiling:
                recovery_amount = self.config.spontaneous_recovery_rate * hours_passed
                strength = min(recovery_ceiling, strength + recovery_amount)
        
        return strength
    
    def get_generalized_fear(
        self, 
        cs_id: str, 
        similarity: float = 1.0
    ) -> float:
        """
        일반화된 공포 수준
        
        원래 CS와 유사한 자극에 대한 공포 반응을 계산한다.
        
        🔬 임상적 관련성:
            과잉 일반화(overgeneralization)는 불안장애, PTSD에서
            관찰되는 특징적 현상이다. 안전한 자극도 위협으로 인식됨.
        
        Args:
            cs_id: 원래 CS 식별자
            similarity: 새 자극과 원래 CS의 유사도 (0~1)
        
        Returns:
            일반화된 공포 수준
        """
        base_fear = self.get_fear_level(cs_id, include_spontaneous_recovery=False)
        
        # 유사도에 따른 기하급수적 감쇠
        generalization_factor = math.exp(
            -self.config.generalization_decay * (1 - similarity)
        )
        
        return base_fear * generalization_factor
    
    def get_association_state(self, cs_id: str) -> Optional[Dict]:
        """
        연합 상태 조회 (연구/디버깅용)
        """
        if cs_id not in self.associations:
            return None
        
        assoc = self.associations[cs_id]
        return {
            'cs_id': assoc.cs_id,
            'us_id': assoc.us_id,
            'strength': assoc.strength,
            'acquisition_count': assoc.acquisition_count,
            'extinction_count': assoc.extinction_count,
            'last_update': assoc.last_update,
            'history_length': len(assoc.history),
            'peak_strength': self._peak_strengths.get(cs_id, 0)
        }
    
    def get_learning_curve(self, cs_id: str) -> List[Tuple[float, float, str]]:
        """
        학습 곡선 데이터 반환
        
        Returns:
            List of (timestamp, strength, trial_type) tuples
        """
        if cs_id not in self.associations:
            return []
        return self.associations[cs_id].history.copy()
    
    def reset(self, cs_id: Optional[str] = None) -> None:
        """
        연합 초기화
        
        Args:
            cs_id: 특정 CS만 초기화 (None이면 전체 초기화)
        """
        if cs_id is None:
            self.associations.clear()
            self._peak_strengths.clear()
        elif cs_id in self.associations:
            del self.associations[cs_id]
            if cs_id in self._peak_strengths:
                del self._peak_strengths[cs_id]


def demonstrate_fear_conditioning():
    """
    공포 조건화 시연
    
    이 함수는 Rescorla-Wagner 모델의 기본 동작을 보여준다.
    """
    print("=" * 60)
    print("Rescorla-Wagner Fear Learning Demonstration")
    print("=" * 60)
    
    learner = RescorlaWagnerLearner(RescorlaWagnerConfig(
        alpha_cs=0.5,
        beta_acquisition=0.3,
        beta_extinction=0.15
    ))
    
    cs = "tone"
    
    # 1. 획득 단계
    print("\n📈 [ACQUISITION PHASE]")
    print("CS(tone) + US(shock) 페어링 10회")
    print("-" * 40)
    
    for i in range(10):
        result = learner.acquisition_trial(cs, us_intensity=0.8)
        print(f"Trial {i+1:2d}: V={result['new_strength']:.3f} "
              f"(ΔV={result['delta_v']:+.3f}, PE={result['prediction_error']:.3f})")
    
    # 2. 소거 단계
    print("\n📉 [EXTINCTION PHASE]")
    print("CS만 제시 (US 없음) 15회")
    print("-" * 40)
    
    for i in range(15):
        result = learner.extinction_trial(cs)
        print(f"Trial {i+1:2d}: V={result['new_strength']:.3f} "
              f"(ΔV={result['delta_v']:+.3f})")
    
    # 3. 일반화 테스트
    print("\n🔄 [GENERALIZATION TEST]")
    print("유사 자극에 대한 공포 반응")
    print("-" * 40)
    
    for sim in [1.0, 0.8, 0.5, 0.2]:
        gen_fear = learner.get_generalized_fear(cs, similarity=sim)
        print(f"Similarity={sim:.1f}: Fear={gen_fear:.3f}")
    
    # 4. 상태 요약
    state = learner.get_association_state(cs)
    print("\n📊 [FINAL STATE]")
    print("-" * 40)
    print(f"Current strength: {state['strength']:.3f}")
    print(f"Peak strength: {state['peak_strength']:.3f}")
    print(f"Acquisition trials: {state['acquisition_count']}")
    print(f"Extinction trials: {state['extinction_count']}")
    
    print("\n" + "=" * 60)
    print("이 결과는 Rescorla-Wagner 모델의 예측을 반영한다.")
    print("실제 공포 반응은 맥락, 개인차 등 다양한 요인의 영향을 받는다.")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_fear_conditioning()

