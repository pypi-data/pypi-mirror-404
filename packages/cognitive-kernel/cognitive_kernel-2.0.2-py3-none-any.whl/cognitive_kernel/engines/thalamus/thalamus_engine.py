"""
Thalamus Engine
시상 엔진 - 산업용 센서 데이터 필터링 시스템 (소프트웨어 벤치마킹 단계)

⚠️ 현재 상태:
- 소프트웨어 시뮬레이션 및 벤치마킹 단계
- 물리적 하드웨어 테스트는 아직 완료되지 않음
- 계속 발전하는 구조 (테스트 과정과 계획된 업그레이드로 확장)

핵심 기능 (예상):
- 감각 입력 필터링
- 주의 게이팅 (에너지 기반)
- 동적 임계값 조절
- 채널 제한

수식:
    현저성 계산:
        S = base_salience × pattern_boost × intensity × arousal
        (위협 감지 시 boost × 2)
    
    주의 가중치:
        W = attention_weight[modality] × focus_boost × (1 + salience)
        (focus_boost = 1.5 if focused else 1.0)
    
    동적 게이팅 (에너지 기반):
        threshold = base_threshold × (1 + energy_deficit_factor)
        energy_deficit_factor = max(0, (0.5 - energy) / 0.5)
        (에너지 낮을수록 임계값 높아짐)
    
    게이팅 (임계값 기반):
        pass = (W ≥ threshold)
    
    채널 제한:
        output = top_k(passed_inputs, k=max_channels)

참고 논문:
    - Sherman & Guillery (2006): Thalamus
    - Crick (1984): Thalamus as gateway to consciousness

🔗 PHAM 블록체인 서명:
    이 파일은 PHAM (Proof of Authorship & Merit) 블록체인 시스템으로 서명되어 있습니다.
    - 블록체인 체인: blockchain/pham_chain_thalamus_engine.json
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
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, deque
from copy import deepcopy

from .config import ThalamusConfig
from .data_types import SensoryInput, FilteredOutput, ModalityType


class ThalamusEngine:
    """
    시상 엔진
    
    산업용 센서 데이터 필터링 시스템 (소프트웨어 벤치마킹 단계)
    
    ⚠️ 현재 상태:
    - 소프트웨어 시뮬레이션 단계
    - 물리적 하드웨어 테스트 미완
    - 계속 발전하는 구조
    
    예상 역할:
    1. 감각 입력 필터링: 중요 정보만 선별
    2. 주의 게이팅: 에너지 기반 동적 임계값 조절
    3. 채널 제한: 최대 N개만 통과
    4. 현저성 계산: 위협, 이름, 질문 등 자동 감지
    
    사용 예:
        from thalamus import ThalamusEngine, ThalamusConfig, SensoryInput, ModalityType
        
        config = ThalamusConfig(gate_threshold=0.3, max_channels=5)
        engine = ThalamusEngine(config)
        
        inputs = [
            SensoryInput("위험! 조심해!", ModalityType.SEMANTIC, intensity=0.9),
            SensoryInput("배경 음악", ModalityType.AUDITORY, intensity=0.3),
        ]
        
        outputs = engine.filter(inputs)
        for out in outputs:
            print(f"{out.content}: 가중치 {out.attention_weight:.2f}")
    """
    
    def __init__(
        self,
        config: Optional[ThalamusConfig] = None,
        energy_provider: Optional[Any] = None
    ):
        """
        시상 엔진 초기화
        
        Args:
            config: 설정 객체 (None이면 기본값 사용)
            energy_provider: 에너지 제공자 (선택적, energy 속성 필요)
                - energy 속성: float (0~1)
                - 예: hypothalamus.state.energy
        """
        # 설정
        if config is None:
            config = ThalamusConfig()
        config.validate()
        self.config = config
        
        # 에너지 제공자 (선택적)
        self.energy_provider = energy_provider
        
        # 주의 상태
        self.attention_focus: Optional[ModalityType] = None
        self.attention_weights: Dict[ModalityType, float] = {
            m: 0.5 for m in ModalityType
        }
        
        # 각성 상태
        self.arousal_level = 1.0
        self.consciousness_gate = True
        
        # 최근 입력 기록
        self.recent_inputs: deque = deque(maxlen=self.config.recent_inputs_maxlen)
        
        # 통계
        self.stats = {
            'total_inputs': 0,
            'passed_gate': 0,
            'blocked': 0,
            'attention_shifts': 0,
            'energy_based_gating': 0,
        }
    
    # ============================================
    # 핵심 기능: 필터링
    # ============================================
    
    def filter(self, inputs: List[SensoryInput]) -> List[FilteredOutput]:
        """
        감각 입력 필터링 (메인 메서드)
        
        Args:
            inputs: 감각 입력 목록
            
        Returns:
            필터링된 출력 목록 (게이트 통과한 것만)
        """
        if not self.consciousness_gate:
            return []
        
        self.stats['total_inputs'] += len(inputs)
        
        # 주의력 자연 감쇠
        self._auto_decay_attention()
        
        # 동적 게이트 임계값 계산 (에너지 기반)
        dynamic_threshold = self._compute_dynamic_threshold()
        
        # 입력 처리 (불변성 보장)
        processed_inputs = []
        for inp in inputs:
            computed_salience = self._calculate_salience(inp)
            processed_inputs.append((inp, computed_salience))
        
        # 주의 가중치 적용
        weighted_inputs = self._apply_attention(processed_inputs)
        
        # 게이팅 (동적 임계값 사용)
        outputs = self._gate(weighted_inputs, dynamic_threshold)
        
        # 우선순위 정렬
        outputs.sort(key=lambda x: x.priority)
        
        # 채널 제한
        outputs = outputs[:self.config.max_channels]
        
        # 기록
        self.recent_inputs.extend(inputs)
        
        return outputs
    
    def filter_single(
        self,
        content: Any,
        modality: ModalityType,
        intensity: float = 1.0,
        salience: float = 0.5
    ) -> Optional[FilteredOutput]:
        """
        단일 입력 필터링
        
        Args:
            content: 입력 내용
            modality: 감각 양식
            intensity: 강도 (0~1)
            salience: 현저성 (0~1)
            
        Returns:
            필터링된 출력 (게이트 통과 시) 또는 None
        """
        inp = SensoryInput(
            content=content,
            modality=modality,
            intensity=intensity,
            salience=salience
        )
        
        outputs = self.filter([inp])
        return outputs[0] if outputs else None
    
    # ============================================
    # 내부 메서드: 계산
    # ============================================
    
    def _compute_dynamic_threshold(self) -> float:
        """
        동적 게이트 임계값 계산 (에너지 기반)
        
        수식:
            threshold = base_threshold × (1 + energy_deficit_factor)
            energy_deficit_factor = max(0, (0.5 - energy) / 0.5)
        
        에너지가 낮을수록 임계값이 높아져 불필요한 감각 차단
        """
        base_threshold = self.config.gate_threshold
        
        if self.energy_provider is None:
            return base_threshold
        
        # 에너지 상태 가져오기
        try:
            energy = self.energy_provider.energy
            deficit_threshold = self.config.energy_deficit_threshold
            
            if energy < deficit_threshold:
                # 에너지 부족 시 임계값 증가
                deficit_factor = (deficit_threshold - energy) / deficit_threshold
                boost = self.config.energy_deficit_boost
                dynamic_threshold = base_threshold * (1 + deficit_factor * boost)
                
                self.stats['energy_based_gating'] += 1
                return min(1.0, dynamic_threshold)
        except AttributeError:
            pass
        
        return base_threshold
    
    def _calculate_salience(self, inp: SensoryInput) -> float:
        """
        현저성 계산
        
        수식:
            S = base_salience × boost × intensity × arousal
        
        Returns:
            계산된 현저성 (0~1)
        """
        base_salience = inp.salience  # prior
        
        # 텍스트인 경우 패턴 매칭
        if isinstance(inp.content, str):
            content_lower = inp.content.lower()
            
            for category, patterns in self.config.salient_patterns.items():
                for pattern in patterns:
                    if pattern in content_lower:
                        boost = self.config.salience_boost
                        if category == 'threat':
                            boost *= 2  # 위협은 2배 부스트
                        base_salience = min(1.0, base_salience * boost)
                        break
        
        # 강도 반영
        base_salience *= inp.intensity
        
        # 각성 수준 반영
        base_salience *= self.arousal_level
        
        # 신규성 보너스
        if self.config.novelty_bonus > 0:
            novelty = self._compute_novelty(inp)
            base_salience += novelty * self.config.novelty_bonus
        
        return min(1.0, base_salience)
    
    def _compute_novelty(self, inp: SensoryInput) -> float:
        """
        신규성 계산 (최근 입력과 비교)
        
        Returns:
            0.0 (익숙함) ~ 1.0 (완전히 새로운)
        """
        if not self.recent_inputs:
            return 1.0
        
        # 최근 입력과 유사도 계산
        similar_count = 0
        for recent in list(self.recent_inputs)[-10:]:  # 최근 10개만
            if isinstance(inp.content, str) and isinstance(recent.content, str):
                if inp.content.lower() == recent.content.lower():
                    similar_count += 1
        
        # 유사도가 높을수록 novelty 낮음
        novelty = 1.0 - (similar_count / min(10, len(self.recent_inputs)))
        return max(0.0, min(1.0, novelty))
    
    def _apply_attention(
        self,
        processed_inputs: List[Tuple[SensoryInput, float]]
    ) -> List[Tuple[SensoryInput, float, float]]:
        """
        주의 가중치 적용
        
        수식:
            W = attention_weight[modality] × focus_boost × (1 + salience)
        """
        weighted = []
        focus_boost = self.config.focus_boost
        
        for inp, computed_salience in processed_inputs:
            weight = self.attention_weights.get(inp.modality, 0.5)
            
            if self.attention_focus == inp.modality:
                weight *= focus_boost
            
            weight *= (1 + computed_salience)
            weighted.append((inp, computed_salience, min(1.0, weight)))
        
        return weighted
    
    def _gate(
        self,
        weighted_inputs: List[Tuple[SensoryInput, float, float]],
        threshold: float
    ) -> List[FilteredOutput]:
        """게이팅 (필터링)"""
        outputs = []
        
        for inp, computed_salience, weight in weighted_inputs:
            passed = weight >= threshold
            
            if passed:
                self.stats['passed_gate'] += 1
            else:
                self.stats['blocked'] += 1
            
            outputs.append(FilteredOutput(
                content=inp.content,
                modality=inp.modality,
                attention_weight=weight,
                passed_gate=passed,
                priority=int((1 - weight) * 10),
                computed_salience=computed_salience
            ))
        
        return [o for o in outputs if o.passed_gate]
    
    # ============================================
    # 주의 조절
    # ============================================
    
    def set_attention_focus(self, modality: ModalityType):
        """주의 포커스 설정"""
        if self.attention_focus != modality:
            self.attention_focus = modality
            self.stats['attention_shifts'] += 1
    
    def shift_attention(self, target: str):
        """
        주의 전환 (텍스트 기반 자동 감지)
        
        Args:
            target: 주의 대상
        """
        target_lower = target.lower()
        
        # 키워드 기반 양식 감지
        if any(w in target_lower for w in ['보', '시각', '이미지', 'see', 'look', 'image']):
            self.set_attention_focus(ModalityType.VISUAL)
        elif any(w in target_lower for w in ['듣', '소리', '음악', 'hear', 'sound', 'music']):
            self.set_attention_focus(ModalityType.AUDITORY)
        elif any(w in target_lower for w in ['느낌', '감정', '기분', 'feel', 'emotion']):
            self.set_attention_focus(ModalityType.EMOTIONAL)
        elif any(w in target_lower for w in ['기억', '예전', '과거', 'remember', 'past']):
            self.set_attention_focus(ModalityType.EPISODIC)
        else:
            self.set_attention_focus(ModalityType.SEMANTIC)
    
    def boost_attention(self, modality: ModalityType, amount: float = 0.2):
        """특정 양식 주의 부스트"""
        current = self.attention_weights.get(modality, 0.5)
        self.attention_weights[modality] = min(1.0, current + amount)
    
    def _auto_decay_attention(self):
        """주의력 자연 감쇠"""
        decay = self.config.attention_decay * self.config.auto_decay_scale
        
        for modality in self.attention_weights:
            current = self.attention_weights[modality]
            
            if abs(current - 0.5) > 0.01:
                self.attention_weights[modality] = current + decay * (0.5 - current)
            else:
                self.attention_weights[modality] = 0.5
                if modality == self.attention_focus:
                    self.attention_focus = None
    
    # ============================================
    # 각성 조절
    # ============================================
    
    def set_arousal(self, level: float):
        """각성 수준 설정 (0~1)"""
        self.arousal_level = max(0.0, min(1.0, level))
        
        # 낮은 각성 = 게이트 닫힘 (수면)
        if self.arousal_level < 0.2:
            self.consciousness_gate = False
        else:
            self.consciousness_gate = True
    
    def sleep_mode(self):
        """수면 모드 (감각 차단)"""
        self.arousal_level = 0.0
        self.consciousness_gate = False
    
    def wake_up(self):
        """각성"""
        self.arousal_level = 1.0
        self.consciousness_gate = True
    
    def alert(self, reason: str = ""):
        """경계 상태 (주의 최대화)"""
        self.arousal_level = 1.0
        self.consciousness_gate = True
        # 모든 감각 주의 증가
        for modality in self.attention_weights:
            self.attention_weights[modality] = min(1.0, self.attention_weights[modality] + 0.3)
    
    # ============================================
    # 상태 조회
    # ============================================
    
    def get_state(self) -> Dict[str, Any]:
        """전체 상태 반환"""
        return {
            'arousal_level': round(self.arousal_level, 2),
            'consciousness_gate': self.consciousness_gate,
            'attention_focus': self.attention_focus.value if self.attention_focus else None,
            'attention_weights': {k.value: round(v, 2) for k, v in self.attention_weights.items()},
            'recent_inputs': len(self.recent_inputs),
            'stats': self.stats.copy(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return self.stats.copy()
    
    def is_awake(self) -> bool:
        """각성 상태 확인"""
        return self.consciousness_gate and self.arousal_level > 0.2
    
    def reset(self):
        """상태 리셋"""
        self.attention_focus = None
        self.attention_weights = {m: 0.5 for m in ModalityType}
        self.arousal_level = 1.0
        self.consciousness_gate = True
        self.recent_inputs.clear()
        self.stats = {
            'total_inputs': 0,
            'passed_gate': 0,
            'blocked': 0,
            'attention_shifts': 0,
            'energy_based_gating': 0,
        }

