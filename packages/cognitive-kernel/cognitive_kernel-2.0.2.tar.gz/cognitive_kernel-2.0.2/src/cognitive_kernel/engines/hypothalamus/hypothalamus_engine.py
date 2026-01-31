"""
Hypothalamus Engine
시상하부 엔진 - 산업용 동기 부여 및 에너지 관리 시스템 (소프트웨어 벤치마킹 단계)

⚠️ 현재 상태:
- 소프트웨어 시뮬레이션 및 벤치마킹 단계
- 물리적 하드웨어 테스트는 아직 완료되지 않음
- 계속 발전하는 구조 (테스트 과정과 계획된 업그레이드로 확장)

핵심 기능 (예상):
- 에너지 관리 및 항상성 유지
- 욕구(Drive) 시스템: 수면, 탐험, 학습, 사회적 상호작용 등
- 보상 시스템: 도파민 기반 동기 부여
- 각성 수준 계산: 에너지 × (1 - 지루함) × (1 + 도파민 보정)

수식:
    에너지 감쇠 (활동 시):
        E(t) = E_0 - λ·t·(1 + activity_multiplier)
        - λ: energy_decay (기본값 0.005)
        - activity_multiplier: 활동 유형에 따른 배수 (think: 2.0, learn/chat: 1.0)
    
    에너지 회복 (수면 시):
        E(t) = E_0 + μ·t
        - μ: energy_recovery (기본값 0.02)
    
    지루함 증가:
        B(t) = B_0 + α·t·(1-S)
        - α: boredom_increase (기본값 0.01)
        - S: stimulus_level (0~1)
        - 자극 있으면: B(t) = B_0 - β·S·t (β: boredom_decrease, 기본값 0.05)
    
    도파민 반응 (보상 수신 시):
        D = D_base + β·R·(1-D)
        - β: dopamine_boost (기본값 0.15)
        - R: reward_intensity (0~1)
        - 현재 도파민이 낮을수록 더 큰 효과
    
    욕구 우선순위:
        P = w_E·(1-E) + w_B·B + w_S·S + w_L·L + w_C·C
        - w_E: energy_weight (기본값 1.5)
        - w_B: boredom_weight (기본값 1.0)
        - w_S: stress_weight (기본값 1.2)
        - w_L: loneliness_weight (기본값 0.8)
        - w_C: curiosity_weight (기본값 0.9)
        - E: energy (0~1)
        - B: boredom (0~1)
        - S: stress (0~1)
        - L: loneliness (0~1)
        - C: curiosity (0~1)
    
    각성 수준:
        A = E · (1 - B) · (1 + (D - 0.5) · 0.5)
        - E: energy (0~1)
        - B: boredom (0~1)
        - D: dopamine (0~1)
        - 범위: 0.0 (최저 각성) ~ 1.0 (최고 각성)

참고 논문:
    - Swanson (2000): Hypothalamus structure and function
    - Berridge & Kringelbach (2015): Affective neuroscience of pleasure
    - Saper et al. (2005): Hypothalamic regulation of sleep and circadian rhythms

🔗 PHAM 블록체인 서명:
    이 파일은 PHAM (Proof of Authorship & Merit) 블록체인 시스템으로 서명되어 있습니다.
    - 블록체인 체인: blockchain/pham_chain_hypothalamus_engine.json
    - 4-Signal Scoring: Byte(25%) + Text(35%) + AST(30%) + Exec(10%)
    - 수익 분배: 기여도에 따라 자동 분배 (MAJOR: 70%, MINOR: 20%, PATCH: 10%)
    - IPFS 저장: 모든 버전이 IPFS에 영구 보존됨
    - 자세한 내용: BLOCKCHAIN_INFO.md 참조

💰 기여도 원칙 (블록체인 기반):
    이 엔진은 오픈소스로 제공되며, 코드 재사용 시 로열티를 요구하지 않습니다.
    수익 발생 시점부터 코드/제품 기여도(상용화, 홍보, 마케팅, 판매 등)가 블록체인에 기록되어 합산되어 분배됩니다.
    이 시스템은 계속 업그레이드되어가는 구조입니다.
    ⚠️ GNJz의 기여도 원칙: 최초 코드 작성자 GNJz는 자신의 기여도가 총 기여도 중 6%를 넘지 않도록 제한합니다. 이것은 블록체인으로 검증 가능한 기여도 상한선입니다.

Author: GNJz (Qquarts)
Version: 1.0.0-alpha (Software Benchmarking Stage)
License: MIT License
Blockchain: PHAM v4 (Signed)
"""

import math
import time
import random
from typing import Dict, List, Tuple, Optional, Any

from .config import HypothalamusConfig
from .data_types import InternalState, DriveSignal, DriveType


class HypothalamusEngine:
    """
    시상하부 엔진 (Hypothalamus Engine)
    
    산업용 동기 부여 및 에너지 관리 시스템 (소프트웨어 벤치마킹 단계)
    
    ⚠️ 현재 상태:
    - 소프트웨어 시뮬레이션 단계
    - 물리적 하드웨어 테스트 미완
    - 계속 발전하는 구조
    
    생물학적 역할:
    시상하부는 뇌의 "조종석"으로, 생존 욕구(Drive)와 항상성(Homeostasis)을 조절합니다.
    - 에너지 관리: 활동 시 소모, 수면 시 회복
    - 욕구 시스템: 수면, 탐험, 학습, 사회적 상호작용 등
    - 보상 시스템: 도파민 기반 동기 부여
    - 생체 리듬: 수면-각성 주기 조절
    
    사용 예:
        from hypothalamus import HypothalamusEngine, HypothalamusConfig
        
        config = HypothalamusConfig(energy_decay=0.005, curiosity_weight=1.5)
        engine = HypothalamusEngine(config)
        
        # 상태 업데이트
        engine.tick(action_type='think', stimulus_level=0.3)
        
        # 현재 욕구 확인
        drive = engine.get_current_drive()
        print(f"현재 욕구: {drive.drive_type.value}, 긴급도: {drive.urgency:.2f}")
        
        # 보상 수신
        engine.receive_reward('success', intensity=0.8)
        
        # 각성 수준 확인
        arousal = engine.get_arousal_level()
        print(f"각성 수준: {arousal:.2f}")
    """
    
    def __init__(self, config: Optional[HypothalamusConfig] = None):
        """
        시상하부 엔진 초기화
        
        Args:
            config: 설정 객체 (None이면 기본값 사용)
        
        Note:
            - 기본값 = 선천적 성향 (Stem Code 철학)
            - 외부 주입 = 환경에 따른 분화
        """
        # 설정 적용
        self.config = config or HypothalamusConfig()
        
        # 내부 상태 초기화
        self.state = InternalState()
        
        # 마지막 활동 시간
        self.last_activity_time = time.time()
        self.last_interaction_time = time.time()
        self.last_update_time = time.time()
        
        # 통계
        self.stats = {
            'ticks': 0,
            'sleep_count': 0,
            'explore_count': 0,
            'rewards_received': 0,
            'total_dopamine': 0.0,
        }
        
        # 욕구 메시지 (자연어)
        self.drive_messages = {
            DriveType.SLEEP: [
                "에너지가 부족합니다. 수면이 필요합니다.",
                "피로가 누적되었습니다. 휴식이 필요합니다.",
                "강제 수면 모드로 전환합니다.",
            ],
            DriveType.EXPLORE: [
                "새로운 자극이 필요합니다.",
                "탐험하고 싶습니다.",
                "지루함이 증가했습니다.",
            ],
            DriveType.SOCIAL: [
                "사회적 상호작용이 필요합니다.",
                "외로움을 느끼고 있습니다.",
                "대화하고 싶습니다.",
            ],
            DriveType.LEARN: [
                "학습하고 싶습니다.",
                "새로운 지식이 필요합니다.",
                "호기심이 높아졌습니다.",
            ],
            DriveType.REST: [
                "스트레스가 높습니다. 휴식이 필요합니다.",
                "부하가 누적되었습니다.",
                "안정이 필요합니다.",
            ],
            DriveType.STAY: [
                "안정적인 상태입니다.",
                "준비 완료.",
                "정상 작동 중입니다.",
            ],
        }
    
    # ============================================
    # 1. 상태 업데이트 (틱마다 호출)
    # ============================================
    
    def tick(self, action_type: str = 'idle', stimulus_level: float = 0.0):
        """
        매 틱(Tick)마다 내부 상태 업데이트
        
        수식:
            에너지 변화:
                - 수면: E(t) = E_0 + μ·t (μ: energy_recovery)
                - 활동: E(t) = E_0 - λ·t·(1 + multiplier) (λ: energy_decay)
                - 대기: E(t) = E_0 - λ·t·0.3
            
            지루함 변화:
                - 자극 있음: B(t) = B_0 - β·S·t (β: boredom_decrease, S: stimulus_level)
                - 자극 없음: B(t) = B_0 + α·t·(1-S) (α: boredom_increase)
        
        Args:
            action_type: 현재 행동 ('think', 'learn', 'chat', 'sleep', 'idle')
            stimulus_level: 자극 수준 (0~1)
        """
        self.stats['ticks'] += 1
        current_time = time.time()
        dt = min(1.0, current_time - self.last_update_time)  # 최대 1초
        self.last_update_time = current_time
        
        # ----- 에너지 변화 -----
        if action_type == 'sleep':
            # 수면 시 에너지 회복
            # 수식: E(t) = E_0 + μ·t
            self.state.energy += self.config.energy_recovery * dt
        elif action_type in ['think', 'learn', 'chat']:
            # 활동 시 에너지 소모
            # 수식: E(t) = E_0 - λ·t·(1 + multiplier)
            consumption = self.config.energy_decay * dt
            if action_type == 'think':
                consumption *= 2.0  # 생각은 에너지 소모 큼
            self.state.energy -= consumption
            self.last_activity_time = current_time
        else:
            # 대기 시 느린 에너지 감소
            # 수식: E(t) = E_0 - λ·t·0.3
            consumption = self.config.energy_decay * 0.3 * dt
            
            # 지루함의 역설: 극도로 지루하면 멍 때리기 모드 (저전력)
            # 생물학적 근거: DMN(Default Mode Network) 활성화
            if self.state.boredom > 0.9:
                consumption *= 0.5  # 에너지 소모 절반
            
            self.state.energy -= consumption
        
        # ----- 지루함 변화 -----
        # 수식: B(t) = B_0 + α·t·(1-S) (자극 없을 때)
        #       B(t) = B_0 - β·S·t (자극 있을 때)
        if stimulus_level > 0.3:
            # 자극 있으면 지루함 감소
            self.state.boredom -= self.config.boredom_decrease * stimulus_level * dt
        else:
            # 자극 없으면 지루함 증가
            self.state.boredom += self.config.boredom_increase * (1 - stimulus_level) * dt
        
        # ----- 외로움 변화 -----
        if action_type in ['chat', 'social']:
            self.state.loneliness -= 0.1 * dt
            self.last_interaction_time = current_time
        else:
            time_alone = current_time - self.last_interaction_time
            if time_alone > 60:  # 1분 이상 혼자
                self.state.loneliness += self.config.loneliness_increase * dt
        
        # ----- 도파민 자연 감쇠 -----
        self.state.dopamine -= self.config.dopamine_decay * dt
        
        # ----- 스트레스 자연 감소 -----
        self.state.stress -= self.config.stress_decrease * dt
        
        # ----- 호기심 자연 회복 -----
        if action_type != 'learn':
            self.state.curiosity += self.config.curiosity_recovery * dt * 0.5
        
        # ----- 항상성 유지 (Clamping) -----
        self._clamp_state()
    
    def _clamp_state(self):
        """모든 상태값을 0~1 범위로 제한"""
        self.state.energy = max(0.0, min(1.0, self.state.energy))
        self.state.dopamine = max(0.0, min(1.0, self.state.dopamine))
        self.state.boredom = max(0.0, min(1.0, self.state.boredom))
        self.state.curiosity = max(0.0, min(1.0, self.state.curiosity))
        self.state.stress = max(0.0, min(1.0, self.state.stress))
        self.state.loneliness = max(0.0, min(1.0, self.state.loneliness))
        self.state.satisfaction = max(0.0, min(1.0, self.state.satisfaction))
    
    def get_arousal_level(self) -> float:
        """
        각성 수준 계산 및 반환
        
        수식:
            A = E · (1 - B) · (1 + (D - 0.5) · 0.5)
            - E: energy (0~1)
            - B: boredom (0~1)
            - D: dopamine (0~1)
            - 범위: 0.0 (최저 각성) ~ 1.0 (최고 각성)
        
        Returns:
            각성 수준 (0.0 ~ 1.0)
        """
        e = self.state.energy
        b = self.state.boredom
        d = self.state.dopamine
        
        # 각성 수준 = 에너지 × (1 - 지루함) × (1 + 도파민 보정)
        # 도파민은 0~1 범위이므로, 0.5를 기준으로 보정
        dopamine_factor = 1.0 + (d - 0.5) * 0.5  # 0.75 ~ 1.25
        
        arousal = e * (1.0 - b) * dopamine_factor
        
        # 0.0 ~ 1.0 범위로 정규화
        arousal = max(0.0, min(1.0, arousal))
        
        return arousal
    
    def get_energy_state(self) -> Dict[str, float]:
        """
        에너지 상태 노출 인터페이스
        
        다른 엔진(Thalamus, Prefrontal Cortex 등)과의 연동을 위한 상태 정보 제공
        
        Returns:
            에너지 관련 상태 딕셔너리
        """
        return {
            'energy': self.state.energy,
            'arousal_level': self.get_arousal_level(),
            'is_sleep_needed': self.state.energy < self.config.sleep_threshold,
            'is_critical': self.state.energy < self.config.critical_threshold,
        }
    
    # ============================================
    # 2. 보상 시스템 (Reward)
    # ============================================
    
    def receive_reward(self, reward_type: str, intensity: float = 0.5) -> float:
        """
        보상 수신 → 도파민 분비
        
        수식:
            D = D_base + β·R·(1-D)
            - β: dopamine_boost (기본값 0.15)
            - R: reward_intensity (0~1)
            - 현재 도파민이 낮을수록 더 큰 효과
        
        Args:
            reward_type: 보상 유형 ('success', 'praise', 'learn', 'social', 'achievement')
            intensity: 보상 강도 (0~1)
        
        Returns:
            도파민 증가량
        """
        # 보상 유형별 기본 도파민
        reward_dopamine = {
            'success': 0.3,
            'praise': 0.4,
            'learn': 0.2,
            'social': 0.25,
            'achievement': 0.5,
        }
        
        base_reward = reward_dopamine.get(reward_type, 0.2)
        
        # D = D_base + β·R·(1-D)
        # 현재 도파민이 낮을수록 더 큰 효과
        dopamine_gain = self.config.dopamine_boost * base_reward * intensity * (1 - self.state.dopamine)
        
        self.state.dopamine += dopamine_gain
        self.state.satisfaction += intensity * 0.1
        self.state.stress -= intensity * 0.05  # 보상은 스트레스 감소
        
        self.stats['rewards_received'] += 1
        self.stats['total_dopamine'] += dopamine_gain
        
        self._clamp_state()
        
        return dopamine_gain
    
    def receive_punishment(self, intensity: float = 0.3):
        """
        벌/부정적 피드백 → 스트레스 증가
        
        Args:
            intensity: 강도 (0~1)
        """
        self.state.stress += intensity * self.config.stress_increase * 5
        self.state.dopamine -= intensity * 0.1
        self.state.satisfaction -= intensity * 0.15
        
        self._clamp_state()
    
    # ============================================
    # 3. 욕구 판단 (Drive Detection)
    # ============================================
    
    def get_current_drive(self) -> DriveSignal:
        """
        현재 가장 시급한 욕구(Drive) 반환
        
        수식:
            욕구 우선순위: P = w_E·(1-E) + w_B·B + w_S·S + w_L·L + w_C·C
            - w_E: energy_weight (기본값 1.5)
            - w_B: boredom_weight (기본값 1.0)
            - w_S: stress_weight (기본값 1.2)
            - w_L: loneliness_weight (기본값 0.8)
            - w_C: curiosity_weight (기본값 0.9)
            - E: energy (0~1)
            - B: boredom (0~1)
            - S: stress (0~1)
            - L: loneliness (0~1)
            - C: curiosity (0~1)
        
        Returns:
            DriveSignal: 현재 가장 시급한 욕구
        """
        # 각 욕구별 긴급도 계산
        drives = {}
        
        # 1. 수면 욕구 (에너지 부족)
        if self.state.energy < self.config.critical_threshold:
            # 강제 수면 필요 (최우선)
            return DriveSignal(
                drive_type=DriveType.SLEEP,
                urgency=1.0,
                message="⚠️ 에너지 고갈! 강제 수면이 필요합니다!",
                action_suggestion="sleep"
            )
        
        energy_urgency = self.config.energy_weight * (1 - self.state.energy)
        if self.state.energy < self.config.sleep_threshold:
            energy_urgency *= 2  # 임계값 이하면 긴급도 2배
        drives[DriveType.SLEEP] = energy_urgency
        
        # 2. 탐험 욕구 (지루함)
        boredom_urgency = self.config.boredom_weight * self.state.boredom
        if self.state.boredom > self.config.boredom_threshold:
            boredom_urgency *= 1.5
        drives[DriveType.EXPLORE] = boredom_urgency
        
        # 3. 휴식 욕구 (스트레스)
        stress_urgency = self.config.stress_weight * self.state.stress
        if self.state.stress > self.config.stress_threshold:
            stress_urgency *= 1.5
        drives[DriveType.REST] = stress_urgency
        
        # 4. 사회적 욕구 (외로움)
        social_urgency = self.config.loneliness_weight * self.state.loneliness
        if self.state.loneliness > self.config.loneliness_threshold:
            social_urgency *= 1.5
        drives[DriveType.SOCIAL] = social_urgency
        
        # 5. 학습 욕구 (호기심)
        curiosity_urgency = self.config.curiosity_weight * self.state.curiosity
        if self.state.curiosity > self.config.curiosity_threshold:
            curiosity_urgency *= 1.5
        drives[DriveType.LEARN] = curiosity_urgency
        
        # 가장 높은 욕구 선택
        max_drive = max(drives, key=drives.get)
        max_urgency = drives[max_drive]
        
        # 긴급도가 낮으면 안정 상태
        if max_urgency < 0.3:
            max_drive = DriveType.STAY
            max_urgency = 0.1
        
        # 메시지 선택
        message = random.choice(self.drive_messages[max_drive])
        
        # 행동 제안
        action_suggestions = {
            DriveType.SLEEP: "sleep",
            DriveType.EXPLORE: "explore",
            DriveType.SOCIAL: "chat",
            DriveType.LEARN: "learn",
            DriveType.REST: "rest",
            DriveType.STAY: "wait",
        }
        
        return DriveSignal(
            drive_type=max_drive,
            urgency=min(1.0, max_urgency),
            message=message,
            action_suggestion=action_suggestions[max_drive]
        )
    
    def needs_sleep(self) -> bool:
        """수면이 필요한지 확인"""
        return self.state.energy < self.config.sleep_threshold
    
    def is_bored(self) -> bool:
        """지루한지 확인"""
        return self.state.boredom > self.config.boredom_threshold
    
    def is_stressed(self) -> bool:
        """스트레스 받는지 확인"""
        return self.state.stress > self.config.stress_threshold
    
    # ============================================
    # 4. 수면 관리
    # ============================================
    
    def start_sleep(self) -> str:
        """수면 시작"""
        self.stats['sleep_count'] += 1
        return "💤 수면 시작... 기억 공고화 중..."
    
    def sleep_cycle(self, cycles: int = 1) -> str:
        """
        수면 사이클 실행
        
        Args:
            cycles: 수면 사이클 수
        
        Returns:
            수면 완료 메시지
        """
        # 수면 중 에너지 직접 회복 (사이클당 5%)
        energy_per_cycle = 0.05
        
        for _ in range(cycles):
            self.state.energy += energy_per_cycle
            self.state.stress -= 0.02  # 수면 중 스트레스 감소
        
        # 수면 후 상태 리셋
        self.state.boredom = 0.0
        self.state.stress = max(0, self.state.stress)
        
        self._clamp_state()
        
        return f"💤 {cycles} 사이클 수면 완료. 에너지: {self.state.energy:.0%}"
    
    def wake_up(self) -> str:
        """기상"""
        # 기상 시 호기심 회복
        self.state.curiosity = min(1.0, self.state.curiosity + 0.3)
        self.state.boredom = 0.0
        self.state.loneliness = min(1.0, self.state.loneliness + 0.1)  # 잠자고 일어나면 사람 보고 싶음
        
        return "☀️ 좋은 아침입니다! 기분이 상쾌합니다!"
    
    # ============================================
    # 5. 자극 처리
    # ============================================
    
    def process_stimulus(self, stimulus_type: str, intensity: float = 0.5):
        """
        자극 처리
        
        Args:
            stimulus_type: 자극 유형 ('conversation', 'learning', 'threat', 'reward')
            intensity: 자극 강도 (0~1)
        """
        if stimulus_type == 'conversation':
            self.state.loneliness -= intensity * 0.2
            self.state.boredom -= intensity * 0.15
            self.tick(action_type='chat', stimulus_level=intensity)
            
        elif stimulus_type == 'learning':
            self.state.curiosity -= intensity * 0.3  # 호기심 충족
            self.state.boredom -= intensity * 0.2
            self.receive_reward('learn', intensity * 0.5)
            self.tick(action_type='learn', stimulus_level=intensity)
            
        elif stimulus_type == 'threat':
            self.state.stress += intensity * 0.3
            self.state.energy -= intensity * 0.1  # 위협은 에너지 소모
            
        elif stimulus_type == 'reward':
            self.receive_reward('success', intensity)
        
        self._clamp_state()
    
    # ============================================
    # 6. 상태 조회
    # ============================================
    
    def get_state(self) -> Dict[str, Any]:
        """전체 상태 반환"""
        drive = self.get_current_drive()
        
        return {
            'internal_state': self.state.to_dict(),
            'current_drive': {
                'type': drive.drive_type.value,
                'urgency': round(drive.urgency, 3),
                'message': drive.message,
                'action': drive.action_suggestion,
            },
            'needs': {
                'needs_sleep': self.needs_sleep(),
                'is_bored': self.is_bored(),
                'is_stressed': self.is_stressed(),
            },
            'stats': self.stats.copy(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return self.stats.copy()

