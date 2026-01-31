"""
HPA Axis Dynamics Module
시상하부-뇌하수체-부신 축 동역학 모듈

이 모듈은 스트레스 반응의 핵심 경로인 HPA (Hypothalamic-Pituitary-Adrenal) 축의
코르티솔 동역학을 모델링한다.

📐 핵심 수식 (미분 방정식):
    dC/dt = -k₁ × C + k₂ × S × (1 - C/C_max)
    
    여기서:
    - C: 현재 코르티솔 수준 (정규화된 값 0~1)
    - dC/dt: 코르티솔 변화율
    - k₁: 코르티솔 제거율 (clearance rate)
    - k₂: 스트레스에 의한 생산율 (production rate)
    - S: 스트레스 입력 (0~1)
    - C_max: 최대 코르티솔 수준 (정규화에서 1.0)

🔬 이론적 배경:

    HPA 축은 스트레스 반응의 중심 경로이다:
    
    1. 시상하부(Hypothalamus)
       - 스트레스 인지 → CRH(Corticotropin-releasing hormone) 분비
    
    2. 뇌하수체(Pituitary)
       - CRH에 반응 → ACTH(Adrenocorticotropic hormone) 분비
    
    3. 부신(Adrenal)
       - ACTH에 반응 → 코르티솔(Cortisol) 분비
    
    4. 음성 피드백
       - 코르티솔이 높아지면 CRH, ACTH 분비 억제
       - 수식의 `(1 - C/C_max)` 항이 이 피드백을 반영

⚠️ 모델 한계:

    이 모델은 HPA 축의 단순화된 표현이다:
    - 실제 HPA 축은 ~90분 주기의 울트라디안 리듬을 가짐
    - 일주기 리듬(circadian rhythm)이 코르티솔 분비를 조절
    - 개인차, 성별, 연령에 따른 변이가 큼
    - CRH → ACTH → 코르티솔의 캐스케이드 지연이 있음 (~20-30분)
    
    본 모듈은 이러한 복잡성을 추상화하여 핵심 동역학만 포착한다.

📚 참고 문헌:
    - McEwen, B. S. (1998). Protective and damaging effects of stress 
      mediators. NEJM.
    - Herman, J. P. et al. (2016). Regulation of the 
      Hypothalamic-Pituitary-Adrenocortical stress response.
    - Tsigos, C., & Chrousos, G. P. (2002). Hypothalamic–pituitary–adrenal 
      axis, neuroendocrine factors and stress.

Author: GNJz (Qquarts)
Version: 1.0.0
License: MIT License
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import time


@dataclass
class HPAState:
    """
    HPA 축 상태
    
    Attributes:
        cortisol: 현재 코르티솔 수준 (0~1)
        baseline: 기저 코르티솔 수준 (개인차)
        chronic_stress_load: 만성 스트레스 누적 (장기 노출 효과)
        last_update: 마지막 업데이트 시간
    """
    cortisol: float = 0.3  # 기본 안정 상태
    baseline: float = 0.3  # 개인별 기저 수준
    chronic_stress_load: float = 0.0  # 만성 스트레스
    last_update: float = field(default_factory=time.time)
    
    # 연구용 기록
    history: List[Tuple[float, float, float]] = field(default_factory=list)
    # (timestamp, cortisol, stress_input)


@dataclass
class HPAConfig:
    """
    HPA 동역학 설정
    
    📐 핵심 파라미터:
        k1 (clearance_rate): 코르티솔 제거 속도
            - 높을수록 빠르게 정상화
            - 건강한 개인: ~0.1
            - 만성 스트레스: ~0.05 (제거 둔화)
        
        k2 (production_rate): 스트레스 반응 민감도
            - 높을수록 스트레스에 강하게 반응
            - 민감한 개인: ~0.3
            - 둔감한 개인: ~0.1
    
    ⚠️ 이 값들은 시뮬레이션용 추정치이며,
       실제 생리학적 값과 직접 대응하지 않음
    """
    # 동역학 파라미터
    k1_clearance: float = 0.1       # 코르티솔 제거율
    k2_production: float = 0.2      # 스트레스 반응 생산율
    c_max: float = 1.0              # 최대 코르티솔 (정규화)
    c_min: float = 0.1              # 최소 코르티솔 (완전히 0이 되지 않음)
    
    # 만성 스트레스 파라미터
    chronic_accumulation_rate: float = 0.01  # 만성 스트레스 누적 속도
    chronic_decay_rate: float = 0.005        # 만성 스트레스 회복 속도
    chronic_threshold: float = 0.5           # 만성 스트레스 임계값
    
    # 기저 수준 조절
    baseline_drift_rate: float = 0.002  # 기저 수준 변화 속도
    
    # 시뮬레이션 설정
    dt_default: float = 0.1  # 기본 시간 간격 (초)


class HPADynamics:
    """
    HPA 축 동역학 시뮬레이터
    
    이 클래스는 스트레스 입력에 대한 코르티솔 반응을 모델링한다.
    핵심 ODE: dC/dt = -k₁×C + k₂×S×(1 - C/C_max)
    
    💡 사용 시나리오:
    
    1. 급성 스트레스 반응 관찰:
       - 짧은 시간 내 코르티솔 급등 → 점진적 회복
       - "fight or flight" 반응의 생화학적 기반
    
    2. 만성 스트레스 효과 탐구:
       - 지속적 스트레스 → 기저 수준 상승
       - 음성 피드백 둔화 → 코르티솔 만성 상승
       - 우울증, PTSD에서 관찰되는 HPA 축 조절 이상
    
    3. 회복 탄력성 연구:
       - 스트레스 후 정상화 속도 비교
       - 개인차 파라미터 조정
    
    Example:
        >>> hpa = HPADynamics()
        >>> 
        >>> # 급성 스트레스 (강도 0.8)
        >>> for _ in range(50):
        ...     hpa.step(stress_input=0.8, dt=0.1)
        >>> 
        >>> print(f"스트레스 중 코르티솔: {hpa.state.cortisol:.2f}")
        >>> 
        >>> # 회복 (스트레스 제거)
        >>> for _ in range(100):
        ...     hpa.step(stress_input=0.0, dt=0.1)
        >>> 
        >>> print(f"회복 후 코르티솔: {hpa.state.cortisol:.2f}")
    """
    
    def __init__(self, config: Optional[HPAConfig] = None):
        self.config = config or HPAConfig()
        self.state = HPAState()
        
    def step(
        self, 
        stress_input: float, 
        dt: Optional[float] = None
    ) -> Dict:
        """
        HPA 동역학 한 스텝 진행
        
        핵심 ODE를 오일러 방법으로 이산화:
            C_new = C + dt × dC/dt
            dC/dt = -k₁×C + k₂×S×(1 - C/C_max)
        
        Args:
            stress_input: 스트레스 입력 (0~1)
            dt: 시간 간격 (None이면 config.dt_default 사용)
        
        Returns:
            Dict with:
                - cortisol: 현재 코르티솔 수준
                - delta_c: 코르티솔 변화량
                - clearance_term: 제거 항 (-k₁C)
                - production_term: 생산 항 (k₂S(1-C/Cmax))
                - saturation_factor: 포화 계수 (1-C/Cmax)
        """
        if dt is None:
            dt = self.config.dt_default
        
        S = max(0.0, min(1.0, stress_input))
        C = self.state.cortisol
        
        k1 = self.config.k1_clearance
        k2 = self.config.k2_production
        c_max = self.config.c_max
        
        # === HPA ODE ===
        # dC/dt = -k₁×C + k₂×S×(1 - C/C_max)
        
        # 제거 항: 코르티솔은 자연적으로 제거됨
        clearance_term = -k1 * C
        
        # 포화 계수: 코르티솔이 최대치에 가까울수록 생산 억제
        # 이것이 음성 피드백의 핵심
        saturation_factor = 1.0 - (C / c_max)
        saturation_factor = max(0.0, saturation_factor)  # 음수 방지
        
        # 생산 항: 스트레스에 비례, 포화에 반비례
        production_term = k2 * S * saturation_factor
        
        # 총 변화율
        dC_dt = clearance_term + production_term
        
        # 오일러 적분
        C_new = C + dt * dC_dt
        
        # 범위 제한
        C_new = max(self.config.c_min, min(c_max, C_new))
        
        # 상태 업데이트
        delta_c = C_new - C
        self.state.cortisol = C_new
        self.state.last_update = time.time()
        
        # 기록 (연구용)
        self.state.history.append((time.time(), C_new, S))
        
        # === 만성 스트레스 누적 ===
        # 지속적 고스트레스는 만성 스트레스 부하를 증가시킴
        if S > 0.5:
            self.state.chronic_stress_load += (
                self.config.chronic_accumulation_rate * (S - 0.5) * dt
            )
        else:
            # 스트레스가 낮으면 회복
            self.state.chronic_stress_load -= (
                self.config.chronic_decay_rate * dt
            )
        
        self.state.chronic_stress_load = max(0.0, min(1.0, self.state.chronic_stress_load))
        
        # === 기저 수준 조절 (장기 효과) ===
        # 만성 스트레스가 높으면 기저 수준 상승
        if self.state.chronic_stress_load > self.config.chronic_threshold:
            baseline_shift = self.config.baseline_drift_rate * dt
            self.state.baseline = min(0.6, self.state.baseline + baseline_shift)
        else:
            # 회복 시 기저 수준 정상화
            if self.state.baseline > 0.3:
                self.state.baseline -= self.config.baseline_drift_rate * 0.5 * dt
        
        return {
            'cortisol': C_new,
            'delta_c': delta_c,
            'clearance_term': clearance_term,
            'production_term': production_term,
            'saturation_factor': saturation_factor,
            'chronic_stress_load': self.state.chronic_stress_load,
            'baseline': self.state.baseline
        }
    
    def simulate(
        self, 
        stress_profile: List[float], 
        dt: float = 0.1
    ) -> Dict:
        """
        스트레스 프로파일에 따른 시뮬레이션 실행
        
        Args:
            stress_profile: 시간별 스트레스 입력 리스트
            dt: 각 스텝의 시간 간격
        
        Returns:
            시뮬레이션 결과 (cortisol_trace, statistics)
        """
        cortisol_trace = []
        
        for S in stress_profile:
            result = self.step(S, dt)
            cortisol_trace.append(result['cortisol'])
        
        # 통계 계산
        peak_cortisol = max(cortisol_trace)
        mean_cortisol = sum(cortisol_trace) / len(cortisol_trace)
        final_cortisol = cortisol_trace[-1]
        
        # 회복 시간 추정 (스트레스 종료 후 기저 수준으로 돌아오는 시간)
        stress_end_idx = len(stress_profile) - 1
        for i, S in enumerate(stress_profile):
            if S < 0.1:
                stress_end_idx = i
                break
        
        recovery_time = None
        for i in range(stress_end_idx, len(cortisol_trace)):
            if cortisol_trace[i] < self.state.baseline + 0.1:
                recovery_time = (i - stress_end_idx) * dt
                break
        
        return {
            'cortisol_trace': cortisol_trace,
            'peak_cortisol': peak_cortisol,
            'mean_cortisol': mean_cortisol,
            'final_cortisol': final_cortisol,
            'recovery_time': recovery_time,
            'chronic_stress_load': self.state.chronic_stress_load,
            'baseline': self.state.baseline
        }
    
    def get_stress_response_type(self) -> str:
        """
        현재 상태 기반 스트레스 반응 유형 분류
        
        ⚠️ 이것은 진단이 아닌 시뮬레이션 상태 분류입니다.
        
        Returns:
            'normal' | 'acute_stress' | 'elevated' | 'chronic'
        """
        C = self.state.cortisol
        baseline = self.state.baseline
        chronic = self.state.chronic_stress_load
        
        if chronic > self.config.chronic_threshold:
            return 'chronic'
        elif C > 0.7:
            return 'acute_stress'
        elif C > baseline + 0.15:
            return 'elevated'
        else:
            return 'normal'
    
    def reset(self, preserve_chronic: bool = False) -> None:
        """
        상태 초기화
        
        Args:
            preserve_chronic: True면 만성 스트레스 부하 유지
        """
        chronic = self.state.chronic_stress_load if preserve_chronic else 0.0
        baseline = self.state.baseline if preserve_chronic else 0.3
        
        self.state = HPAState(
            cortisol=baseline,
            baseline=baseline,
            chronic_stress_load=chronic
        )
    
    def get_state_summary(self) -> Dict:
        """상태 요약 반환"""
        return {
            'cortisol': self.state.cortisol,
            'baseline': self.state.baseline,
            'chronic_stress_load': self.state.chronic_stress_load,
            'response_type': self.get_stress_response_type(),
            'history_length': len(self.state.history)
        }


def demonstrate_hpa_dynamics():
    """
    HPA 동역학 시연
    
    급성 스트레스 반응 → 회복 과정을 시뮬레이션한다.
    """
    print("=" * 60)
    print("HPA Axis Dynamics Demonstration")
    print("=" * 60)
    
    hpa = HPADynamics(HPAConfig(
        k1_clearance=0.1,
        k2_production=0.2
    ))
    
    print(f"\n초기 상태:")
    print(f"  코르티솔: {hpa.state.cortisol:.3f}")
    print(f"  기저 수준: {hpa.state.baseline:.3f}")
    
    # 1. 급성 스트레스 (강도 0.8, 30스텝)
    print("\n📈 [ACUTE STRESS PHASE]")
    print("스트레스 입력: 0.8 (30 스텝)")
    print("-" * 40)
    
    for i in range(30):
        result = hpa.step(stress_input=0.8, dt=0.1)
        if i % 10 == 0:
            print(f"Step {i:3d}: C={result['cortisol']:.3f} "
                  f"(ΔC={result['delta_c']:+.4f}, "
                  f"sat={result['saturation_factor']:.3f})")
    
    print(f"\n스트레스 중 최종 코르티솔: {hpa.state.cortisol:.3f}")
    
    # 2. 회복 (스트레스 제거, 50스텝)
    print("\n📉 [RECOVERY PHASE]")
    print("스트레스 입력: 0.0 (50 스텝)")
    print("-" * 40)
    
    for i in range(50):
        result = hpa.step(stress_input=0.0, dt=0.1)
        if i % 10 == 0:
            print(f"Step {i:3d}: C={result['cortisol']:.3f} "
                  f"(ΔC={result['delta_c']:+.4f})")
    
    print(f"\n회복 후 코르티솔: {hpa.state.cortisol:.3f}")
    
    # 3. 상태 분류
    print("\n📊 [FINAL STATE]")
    print("-" * 40)
    summary = hpa.get_state_summary()
    print(f"코르티솔: {summary['cortisol']:.3f}")
    print(f"기저 수준: {summary['baseline']:.3f}")
    print(f"만성 스트레스: {summary['chronic_stress_load']:.3f}")
    print(f"반응 유형: {summary['response_type']}")
    
    # 4. 포화 효과 시연
    print("\n🧪 [SATURATION EFFECT]")
    print("이미 높은 코르티솔 상태에서 추가 스트레스")
    print("-" * 40)
    
    hpa.state.cortisol = 0.9  # 인위적으로 높임
    result = hpa.step(stress_input=1.0, dt=0.1)
    print(f"코르티솔 0.9에서 최대 스트레스(1.0) 적용:")
    print(f"  포화 계수: {result['saturation_factor']:.3f}")
    print(f"  생산 항: {result['production_term']:.4f}")
    print(f"  → 포화로 인해 추가 생산이 크게 억제됨")
    
    print("\n" + "=" * 60)
    print("이 시뮬레이션은 HPA 축의 음성 피드백 메커니즘을 보여준다.")
    print("실제 생리학적 반응은 더 복잡한 요인의 영향을 받는다.")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_hpa_dynamics()

