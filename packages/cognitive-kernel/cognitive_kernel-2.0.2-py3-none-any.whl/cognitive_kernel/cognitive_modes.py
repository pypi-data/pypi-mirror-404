"""
🧠 Cognitive Modes - 인지 성향 모드

ADHD와 ASD를 "탐색(Exploration) vs 착취(Exploitation)"의 극단으로 모델링:

- ADHD: 고엔트로피 (High Entropy) - 계속 시도하고 싶은 욕망 (+)
- ASD: 저엔트로피 (Low Entropy) - 패턴을 유지하고 싶은 욕망 (-)

개념적 수식 (비율 표현):
    Entropy_Control = Exploration(ADHD) / Exploitation(ASD)
    
    주의: 이는 개념적 비율 표현이며, 실제 계산되는 수치가 아닙니다.
    실제 구현은 각 모드의 파라미터 조합으로 동작합니다.

Author: GNJz (Qquarts)
Version: 2.0.0
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class CognitiveMode(Enum):
    """인지 모드"""
    NORMAL = "normal"
    ADHD = "adhd"  # 고엔트로피: 과도한 탐색
    ASD = "asd"    # 저엔트로피: 과도한 착취
    PTSD = "ptsd"  # 트라우마 고착
    
    # ADHD(+) ↔ ASD(-) 극 사이 질환들
    PANIC = "panic"           # 공황장애: 과각성, 높은 불안
    EPILEPSY = "epilepsy"     # 간질: 불안정, 발작
    OCD = "ocd"               # 강박: 고착, 반복 행동
    IED = "ied"               # 분노조절장애: 충동, 폭발적 분노
    DEPRESSION = "depression" # 우울증: 무기력, 부정적 편향
    BIPOLAR = "bipolar"       # 양극성 장애: 조증 ↔ 우울
    
    # 중력 붕괴 질환 (Core Decay)
    DEMENTIA = "dementia"     # 치매: 코어 약화 + 루프 잔존 (느린 붕괴)
    ALZHEIMER = "alzheimer"   # 알츠하이머: 코어 소실 + 루프 붕괴 (빠른 붕괴)


@dataclass
class ModeConfig:
    """모드별 파라미터 설정"""
    
    # Thalamus (입력 필터링)
    gate_threshold: float = 0.3  # 게이트 임계값 θ (0~1, 낮을수록 모든 입력 허용, 높을수록 필터링 강화)
    max_channels: int = 3  # 최대 통과 채널 수 (주의 자원 제한)
    
    # PFC (의사결정)
    decision_temperature: float = 1.0  # Softmax inverse-temperature β (P(i) = exp(β×U_i) / Σexp(β×U_j))
                                       # β ↑ (temperature ↓) → 효용 차이 강조 (결정론적, 루틴 고착)
                                       # β ↓ (temperature ↑) → 무작위성 증가 (탐색 강화)
    working_memory_capacity: int = 7
    
    # BasalGanglia (탐색 vs 착취)
    tau: float = 0.5  # Softmax 온도 τ (P(a) = exp(Q(s,a)/τ) / Σexp(Q(s,a')/τ))
                     # 낮을수록 높은 Q값 강조 (착취 강화), 높을수록 균등 선택 (탐색 강화)
    impulsivity: Optional[float] = None  # 충동성 (0~1, 높을수록 탐색↑, 습관 형성↑)
    patience: Optional[float] = None  # 인내심 (0~1, 높을수록 미래 보상 중시, gamma↑)
    
    # MemoryRank (패턴 연결)
    damping: float = 0.85
    local_weight_boost: float = 1.0  # 로컬 연결 가중치 부스트 (개념적 파라미터, 향후 구현)
    
    # Amygdala (감정/위협)
    novelty_sensitivity: float = 1.0  # 신규성 민감도
    
    # Hypothalamus (에너지/스트레스)
    stress_baseline: float = 0.3
    
    # Core Decay (중력 붕괴 동역학)
    core_decay_rate: float = 0.0  # λ: 코어 감쇠율 (초당, 0이면 정상, 클수록 빠르게 붕괴)
                                  # 수식: C(t) = C(0) * exp(-λ * Δt)
    memory_update_failure: float = 0.0  # 새 기억의 중요도 반영 실패율 (0~1)
                                        # 0 = 정상, 1 = 새 기억이 코어에 전혀 기여하지 못함
    loop_integrity_decay: float = 0.0  # 루프 무결성 감쇠율 (MemoryRank 엣지 소실)
                                       # 0 = 정상, 1 = 모든 연결 단절
    
    # 시간축 분리 (오래된 기억 vs 새 기억)
    old_memory_decay_rate: float = 0.0  # 오래된 기억 감쇠율 (초당, 치매 특성: 최근 기억부터 지워짐)
    new_memory_decay_rate: float = 0.0  # 새 기억 감쇠율 (초당, 알츠하이머 특성: 새 기억이 전혀 저장되지 않음)
    memory_age_threshold: float = 3600.0  # 기억 나이 임계값 (초, 이보다 오래되면 "오래된 기억")
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "thalamus": {
                "gate_threshold": self.gate_threshold,
                "max_channels": self.max_channels,
            },
            "pfc": {
                "decision_temperature": self.decision_temperature,
                "working_memory_capacity": self.working_memory_capacity,
            },
            "basal_ganglia": {
                "tau": self.tau,
                "impulsivity": self.impulsivity,
                "patience": self.patience,
            },
            "memoryrank": {
                "damping": self.damping,
                "local_weight_boost": self.local_weight_boost,
            },
            "amygdala": {
                "novelty_sensitivity": self.novelty_sensitivity,
            },
            "hypothalamus": {
                "stress_baseline": self.stress_baseline,
            },
            "core_decay": {
                "core_decay_rate": self.core_decay_rate,
                "memory_update_failure": self.memory_update_failure,
                "loop_integrity_decay": self.loop_integrity_decay,
            },
        }


class CognitiveModePresets:
    """인지 모드 프리셋"""
    
    @staticmethod
    def normal() -> ModeConfig:
        """정상 모드 (균형)"""
        return ModeConfig(
            gate_threshold=0.3,
            max_channels=3,
            decision_temperature=1.0,
            working_memory_capacity=7,
            tau=0.5,
            impulsivity=None,
            patience=None,
            damping=0.85,
            local_weight_boost=1.0,
            novelty_sensitivity=1.0,
            stress_baseline=0.3,
        )
    
    @staticmethod
    def adhd() -> ModeConfig:
        """
        ADHD 모드: 고엔트로피 (High Entropy)
        
        특징:
        - 계속 시도하고 싶은 욕망 (+)
        - 과도한 탐색 (Over-Exploration)
        - 게이팅 임계값 낮음 (산만함) - 낮은 임계값으로 모든 입력 통과
        - decision_temperature 낮음 (β↓) → 무작위성 증가 (탐색 강화)
        """
        return ModeConfig(
            gate_threshold=0.1,  # 낮은 임계값 → 모든 입력 통과 (산만)
            max_channels=10,  # 많은 채널 동시 처리
            decision_temperature=0.5,  # β↓ (temperature↑) → 무작위성 증가 (탐색 강화)
            working_memory_capacity=5,  # 낮은 용량 (집중력 부족)
            tau=1.5,  # 높은 tau → 탐색 강화 (Q값 차이 덜 중요)
            impulsivity=0.8,  # 높은 충동성
            patience=0.2,  # 낮은 인내심
            damping=0.85,
            local_weight_boost=0.8,  # 글로벌 연결 선호 (개념적, 향후 구현)
            novelty_sensitivity=2.0,  # 높은 신규성 민감도
            stress_baseline=0.4,
        )
    
    @staticmethod
    def asd() -> ModeConfig:
        """
        ASD 모드: 저엔트로피 (Low Entropy)
        
        특징:
        - 패턴을 유지하고 싶은 욕망 (-)
        - 과도한 착취 (Over-Exploitation)
        - 게이팅 임계값 낮음 (감각 과부하)
        - decision_temperature 높음 (β↑, temperature↓) → 효용 차이 강조 (결정론적, 루틴 고착)
        - 로컬 연결 강화 (패턴 고착)
        """
        return ModeConfig(
            gate_threshold=0.0,  # 모든 미세 자극 통과 (감각 과부하)
            max_channels=1,  # 단일 채널 집중
            decision_temperature=5.0,  # β↑ (temperature↓) → 효용 차이 강조 (결정론적, 루틴 고착)
            working_memory_capacity=7,
            tau=0.1,  # 매우 낮은 탐색 온도 → 착취 강화
            impulsivity=0.1,  # 낮은 충동성
            patience=0.9,  # 높은 인내심 (루틴 유지)
            damping=0.85,
            local_weight_boost=3.0,  # 로컬 연결 강화 (패턴 고착, 개념적, 향후 구현)
            novelty_sensitivity=3.0,  # 높은 신규성 민감도 (낯선 상황 공포)
            stress_baseline=0.5,  # 높은 스트레스 기준선
        )
    
    @staticmethod
    def ptsd() -> ModeConfig:
        """
        PTSD 모드: 트라우마 고착
        
        특징:
        - 특정 기억에 비정상적으로 높은 가중치
        - 과각성 (Hyperarousal)
        - 예측 실패에 대한 높은 공포
        """
        return ModeConfig(
            gate_threshold=0.2,  # 낮은 임계값 (과각성)
            max_channels=5,
            decision_temperature=0.8,
            working_memory_capacity=5,
            tau=0.3,
            impulsivity=0.6,
            patience=0.3,
            damping=0.9,  # 높은 감쇠 (트라우마 기억 지속)
            local_weight_boost=2.0,  # 트라우마 노드 연결 강화 (개념적, 향후 구현)
            novelty_sensitivity=2.5,  # 매우 높은 신규성 민감도
            stress_baseline=0.7,  # 높은 스트레스 기준선
        )
    
    @staticmethod
    def panic() -> ModeConfig:
        """
        공황장애 모드: 과각성, 높은 불안
        
        특징:
        - 갑작스러운 공황 발작
        - 과각성 (Hyperarousal)
        - 높은 불안/스트레스
        - ADHD 쪽에 가깝지만 불안 차원이 높음
        """
        return ModeConfig(
            gate_threshold=0.15,  # 낮은 임계값 (과각성)
            max_channels=8,  # 많은 채널 (불안으로 인한 산만)
            decision_temperature=0.6,  # 중간 (불안정)
            working_memory_capacity=4,  # 낮은 용량 (공황 시 집중력 저하)
            tau=1.2,  # 높은 탐색
            impulsivity=0.7,  # 높은 충동성
            patience=0.2,  # 낮은 인내심
            damping=0.85,
            local_weight_boost=1.0,
            novelty_sensitivity=3.5,  # 매우 높은 신규성 민감도 (공포)
            stress_baseline=0.8,  # 매우 높은 스트레스
        )
    
    @staticmethod
    def epilepsy() -> ModeConfig:
        """
        간질 모드: 불안정, 발작
        
        특징:
        - 뇌 전기 활동 이상
        - 발작 (Seizure)
        - 극도의 불안정성
        - ADHD 쪽 (불안정, 탐색)
        """
        return ModeConfig(
            gate_threshold=0.2,  # 낮은 임계값 (불안정)
            max_channels=6,  # 중간
            decision_temperature=0.4,  # 낮음 (매우 불안정)
            working_memory_capacity=5,  # 낮음
            tau=2.0,  # 매우 높은 탐색 (불안정)
            impulsivity=0.9,  # 매우 높은 충동성
            patience=0.1,  # 매우 낮은 인내심
            damping=0.85,
            local_weight_boost=0.8,  # 글로벌 연결 선호
            novelty_sensitivity=2.0,  # 높은 민감도
            stress_baseline=0.6,  # 높은 스트레스
        )
    
    @staticmethod
    def ocd() -> ModeConfig:
        """
        강박 모드: 고착, 반복 행동
        
        특징:
        - 반복 행동 (Compulsion)
        - 고착 (Obsession)
        - 불안 완화를 위한 의식
        - ASD 쪽에 가깝지만 불안 차원이 높음
        """
        return ModeConfig(
            gate_threshold=0.1,  # 낮은 임계값 (과각성)
            max_channels=2,  # 적은 채널 (집중)
            decision_temperature=6.0,  # 매우 높음 (강한 고착)
            working_memory_capacity=7,
            tau=0.05,  # 매우 낮음 (극도의 착취)
            impulsivity=0.2,  # 낮은 충동성
            patience=0.95,  # 매우 높은 인내심 (루틴 유지)
            damping=0.95,  # 매우 높은 감쇠 (기억 지속)
            local_weight_boost=4.0,  # 매우 높은 로컬 연결 (패턴 고착)
            novelty_sensitivity=4.0,  # 매우 높은 민감도 (변화 공포)
            stress_baseline=0.7,  # 높은 스트레스
        )
    
    @staticmethod
    def ied() -> ModeConfig:
        """
        분노조절장애 모드: 충동, 폭발적 분노
        
        특징:
        - 폭발적 분노
        - 극도의 충동성
        - 감정 조절 실패
        - ADHD 쪽 (높은 충동성)
        """
        return ModeConfig(
            gate_threshold=0.1,  # 낮은 임계값
            max_channels=10,  # 많은 채널
            decision_temperature=0.3,  # 매우 낮음 (충동적)
            working_memory_capacity=4,  # 낮음
            tau=2.5,  # 매우 높은 탐색
            impulsivity=0.95,  # 극도의 충동성
            patience=0.05,  # 극도로 낮은 인내심
            damping=0.85,
            local_weight_boost=0.8,  # 글로벌 연결 선호
            novelty_sensitivity=2.5,  # 높은 민감도
            stress_baseline=0.8,  # 매우 높은 스트레스
        )
    
    @staticmethod
    def depression() -> ModeConfig:
        """
        우울증 모드: 무기력, 부정적 편향
        
        특징:
        - 에너지 저하
        - 무기력
        - 부정적 인지 편향
        - ASD 쪽 (착취, 고착)
        """
        return ModeConfig(
            gate_threshold=0.4,  # 높은 임계값 (무기력)
            max_channels=2,  # 적은 채널
            decision_temperature=2.0,  # 높음 (고착)
            working_memory_capacity=5,
            tau=0.3,  # 낮음 (착취)
            impulsivity=0.2,  # 낮은 충동성
            patience=0.8,  # 높은 인내심 (하지만 부정적)
            damping=0.9,  # 높은 감쇠
            local_weight_boost=2.5,  # 로컬 연결 강화
            novelty_sensitivity=0.5,  # 낮은 민감도 (무기력)
            stress_baseline=0.6,  # 높은 스트레스
        )
    
    @staticmethod
    def bipolar_mania() -> ModeConfig:
        """
        양극성 장애 - 조증 상태
        
        특징:
        - 과도한 에너지
        - 높은 탐색
        - 충동성
        - ADHD 쪽
        """
        return ModeConfig(
            gate_threshold=0.05,  # 매우 낮음
            max_channels=15,  # 매우 많은 채널
            decision_temperature=0.3,  # 매우 낮음
            working_memory_capacity=5,
            tau=3.0,  # 극도의 탐색
            impulsivity=0.9,  # 높은 충동성
            patience=0.1,  # 낮은 인내심
            damping=0.85,
            local_weight_boost=0.5,  # 글로벌 연결 선호
            novelty_sensitivity=3.0,  # 높은 민감도
            stress_baseline=0.3,  # 낮은 스트레스 (조증)
        )
    
    @staticmethod
    def bipolar_depression() -> ModeConfig:
        """
        양극성 장애 - 우울 상태
        
        특징:
        - 에너지 저하
        - 낮은 탐색
        - 고착
        - ASD 쪽
        """
        return ModeConfig(
            gate_threshold=0.5,  # 높음
            max_channels=2,  # 적음
            decision_temperature=3.0,  # 높음
            working_memory_capacity=5,
            tau=0.2,  # 낮음
            impulsivity=0.2,  # 낮은 충동성
            patience=0.7,  # 높은 인내심
            damping=0.9,  # 높은 감쇠
            local_weight_boost=3.0,  # 로컬 연결 강화
            novelty_sensitivity=0.5,  # 낮은 민감도
            stress_baseline=0.7,  # 높은 스트레스
        )
    
    @staticmethod
    def dementia() -> ModeConfig:
        """
        치매 모드: 코어 약화 + 루프 잔존 (느린 붕괴)
        
        동역학 정의:
        - E: 증가 (엔트로피 증가)
        - T: 있음 (회전은 유지)
        - C: ↓ (느리게 감소) - C(t) = C(0) * exp(-λ_d * t), λ_d 작음
        - L: 부분 유지 (루프는 남아 있음)
        
        특징:
        - 중력은 약해지지만 완전히 사라지지는 않음
        - 오래된 기억은 남아 있음
        - 새 기억은 축적되지 않음
        - 판단은 느려지지만 '나'는 아직 있음
        """
        config = ModeConfig(
            gate_threshold=0.0,  # 필터링 능력 상실
            max_channels=5,
            decision_temperature=0.5,  # 판단력 저하
            working_memory_capacity=2,  # Miller's Law 붕괴
            tau=1.5,  # 의미 없는 배회 강화
            impulsivity=0.6,
            patience=0.3,
            damping=0.5,  # 기억 전파력 약화
            local_weight_boost=0.1,  # 연결 고리 약화
            novelty_sensitivity=0.3,  # 낮은 신규성 민감도
            stress_baseline=0.5,
            # Core Decay 파라미터
            core_decay_rate=0.001,  # λ_d: 느린 붕괴 (초당 0.1% 감소)
            memory_update_failure=0.3,  # 새 기억 30% 실패
            loop_integrity_decay=0.0005,  # 루프 느린 감쇠
        )
        # 시간축 분리: 오래된 기억 감쇠 (치매 특성)
        config.old_memory_decay_rate = 0.0001  # 오래된 기억 감쇠율 (느림)
        config.new_memory_decay_rate = 0.0  # 새 기억은 정상
        config.memory_age_threshold = 3600.0  # 1시간 이상 = 오래된 기억
        return config
    
    @staticmethod
    def alzheimer() -> ModeConfig:
        """
        알츠하이머 모드: 코어 소실 + 루프 붕괴 (빠른 붕괴)
        
        동역학 정의:
        - E: 최대 (엔트로피 최대)
        - T: 있음 (중요! 생각은 계속 돈다)
        - C: → 0 (중력 소실)
        - L: 붕괴 (루프 무결성 완전 파괴)
        
        붕괴 순서:
        ① Core Strength 붕괴: C(t) = C(0) * exp(-λ_a * t), λ_a 큼
        ② Loop Integrity 붕괴: MemoryRank 엣지 소실
        ③ 시간축 붕괴: "방금 전"이 사라짐, 현재가 매 순간 초기화
        
        특징:
        - 생각은 계속 발생하지만 귀환력이 없음
        - 새 기억이 코어에 기여하지 못함
        - 시간이 연결되지 않음
        - '생각은 있는데, 나로 돌아오지 않는다'
        """
        config = ModeConfig(
            gate_threshold=0.0,  # 필터링 능력 완전 상실
            max_channels=10,  # 모든 자극이 고통으로 다가옴
            decision_temperature=0.1,  # β → 0: 논리적 판단 불가, 무작위 행동
            working_memory_capacity=1,  # Miller's Law 완전 붕괴
            tau=2.0,  # 탐색 과다 (의미 없는 배회)
            impulsivity=0.8,
            patience=0.1,
            damping=0.3,  # 기억 연결 완전 파괴
            local_weight_boost=0.0,  # 연결 고리 완전 단절
            novelty_sensitivity=0.1,  # 신규성 인식 불가
            stress_baseline=0.8,  # 높은 스트레스
            # Core Decay 파라미터
            core_decay_rate=0.01,  # λ_a: 빠른 붕괴 (초당 1% 감소)
            memory_update_failure=0.8,  # 새 기억 80% 실패 (코어에 기여하지 못함)
            loop_integrity_decay=0.01,  # 루프 빠른 감쇠 (엣지 급격히 소실)
        )
        # 시간축 분리: 새 기억 즉시 소실 (알츠하이머 특성)
        config.old_memory_decay_rate = 0.0001  # 오래된 기억은 느리게 감쇠
        config.new_memory_decay_rate = 0.1  # 새 기억은 매우 빠르게 감쇠 (거의 즉시 소실)
        config.memory_age_threshold = 3600.0  # 1시간 이상 = 오래된 기억
        return config
    
    @staticmethod
    def get_config(mode: CognitiveMode) -> ModeConfig:
        """모드에 따른 설정 반환"""
        if mode == CognitiveMode.NORMAL:
            return CognitiveModePresets.normal()
        elif mode == CognitiveMode.ADHD:
            return CognitiveModePresets.adhd()
        elif mode == CognitiveMode.ASD:
            return CognitiveModePresets.asd()
        elif mode == CognitiveMode.PTSD:
            return CognitiveModePresets.ptsd()
        elif mode == CognitiveMode.PANIC:
            return CognitiveModePresets.panic()
        elif mode == CognitiveMode.EPILEPSY:
            return CognitiveModePresets.epilepsy()
        elif mode == CognitiveMode.OCD:
            return CognitiveModePresets.ocd()
        elif mode == CognitiveMode.IED:
            return CognitiveModePresets.ied()
        elif mode == CognitiveMode.DEPRESSION:
            return CognitiveModePresets.depression()
        elif mode == CognitiveMode.BIPOLAR:
            return CognitiveModePresets.bipolar_mania()  # 기본값은 조증
        elif mode == CognitiveMode.DEMENTIA:
            return CognitiveModePresets.dementia()
        elif mode == CognitiveMode.ALZHEIMER:
            return CognitiveModePresets.alzheimer()
        else:
            raise ValueError(f"Unknown mode: {mode}")

