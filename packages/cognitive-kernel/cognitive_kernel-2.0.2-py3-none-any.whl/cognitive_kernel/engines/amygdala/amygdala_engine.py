"""
Amygdala Engine
편도체 엔진 - 산업용 감정/위협 분석 시스템 (소프트웨어 벤치마킹 단계)

핵심 기능:
- 감정 분석 (Valence-Arousal 모델)
- 위협 레벨 평가
- 중요도 가중치 계산
- 수면 소거 (Contextual Extinction)

수식:
    위협 점수:
        T = Σ(weight_i) / 2.0, clamped to [0, 1]
    
    감정 강도:
        E = √(V² + A²)
    
    기억 중요도 가중치:
        importance_weight = 1 + α·E·(1 - e^(-β·T))
        α = 0.5, β = 2.0
    
    수면 소거:
        Δstrength = -extinction_rate × (1 - co_occurrence_factor)
        co_occurrence_factor = 1 if (stimulus + threat) occurred recently else 0

참고 논문:
    - Russell's Circumplex Model (감정 2D 모델)
    - Pavlovian Conditioning (공포 학습)
    - Extinction Learning (소거 학습)

🔗 PHAM 블록체인 서명:
    이 파일은 PHAM (Proof of Authorship & Merit) 블록체인 시스템으로 서명되어 있습니다.
    - 블록체인 체인: blockchain/pham_chain_amygdala_engine.json
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
import re
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

from .config import AmygdalaConfig
from .data_types import EmotionState, ThreatSignal, FearMemory


class AmygdalaEngine:
    """
    편도체 엔진
    
    산업용 감정/위협 분석 시스템 (소프트웨어 벤치마킹 단계)
    
    ⚠️ 현재 상태:
    - 소프트웨어 시뮬레이션 단계
    - 물리적 하드웨어 테스트 미완
    - 계속 발전하는 구조
    
    예상 역할:
    1. 위협 감지: 텍스트에서 위협 신호 자동 감지
    2. 감정 분석: Valence-Arousal 모델 기반 감정 분석
    3. 기억 강화: 감정과 위협에 따른 기억 중요도 가중치 계산
    4. 공포 조건화: Pavlovian 조건화를 통한 학습
    
    사용 예:
        from amygdala import AmygdalaEngine, AmygdalaConfig
        
        config = AmygdalaConfig(threat_threshold=0.4)
        engine = AmygdalaEngine(config)
        
        # 위협 감지
        threat = engine.detect_threat("위험! 조심해!")
        
        # 감정 분석
        emotion = engine.process_emotion("오늘 정말 기쁘다!")
        
        # 기억 강화
        enhancement = engine.calculate_memory_enhancement(emotion, threat)
    """
    
    def __init__(self, config: Optional[AmygdalaConfig] = None):
        """
        편도체 엔진 초기화
        
        Args:
            config: 설정 객체 (None이면 기본값 사용)
        """
        # 설정
        if config is None:
            config = AmygdalaConfig()
        config.validate()
        self.config = config
        
        # 공포 조건화 메모리
        self.fear_memories: Dict[str, FearMemory] = {}
        
        # 동시 발생 기록 (맥락적 소거용)
        self.stimulus_threat_cooccurrence: Dict[str, Dict[str, float]] = {}
        
        # 현재 상태
        self.current_emotion = EmotionState()
        self.recent_threats: List[ThreatSignal] = []
        
        # 통계
        self.stats = {
            'threats_detected': 0,
            'emotions_processed': 0,
            'fear_conditionings': 0,
            'memories_enhanced': 0,
        }
    
    # ============================================
    # 핵심 기능: 위협 감지
    # ============================================
    
    def detect_threat(self, input_text: str) -> Optional[ThreatSignal]:
        """
        위협 감지
        
        수식:
            T = Σ(weight_i) / 2.0, clamped to [0, 1]
        
        Args:
            input_text: 입력 텍스트
            
        Returns:
            ThreatSignal if threat detected, None otherwise
        """
        text_lower = input_text.lower()
        text_no_space = text_lower.replace(' ', '')
        
        # 부정어 패턴
        negations_strict = [
            '안 ', '않아', '않는', '않다', '않을', '않고', '않겠',
            '못 ', '못하', '아니', '아닌', '없어', '없다',
            '싶지 않', '싶지않', '하지 않', '하지않', '안 할', '안할',
            'not ', "don't", "doesn't", "didn't", "won't", "wouldn't",
            'never ', 'no ', "isn't", "aren't", "can't", "cannot",
        ]
        
        threat_scores = defaultdict(float)
        detected_words = []
        
        for category, info in self.config.threat_keywords.items():
            for word in info['words']:
                word_no_space = word.replace(' ', '')
                if word in text_lower or word_no_space in text_no_space:
                    # 부정어 체크
                    idx = text_lower.find(word)
                    if idx == -1:
                        idx = text_no_space.find(word_no_space)
                        context_pre = text_no_space[max(0, idx-5):idx]
                        context_post = text_no_space[idx:idx+len(word_no_space)+8]
                    else:
                        context_pre = text_lower[max(0, idx-5):idx]
                        context_post = text_lower[idx:idx+len(word)+8]
                    
                    has_negation_pre = any(neg in context_pre for neg in negations_strict)
                    has_negation_post = any(neg in context_post for neg in negations_strict)
                    
                    if (has_negation_pre or has_negation_post) and category != 'self_harm':
                        continue  # 부정문이므로 위협 아님
                    
                    score = info['weight']
                    threat_scores[info['type']] += score
                    if word not in detected_words:
                        detected_words.append(word)
        
        # 총 위협 점수
        total_threat = sum(threat_scores.values())
        normalized_threat = min(1.0, total_threat / 2.0)
        
        # 임계값 체크
        if normalized_threat >= self.config.threat_threshold:
            main_threat_type = max(threat_scores, key=threat_scores.get) if threat_scores else 'unknown'
            response = self._determine_response(normalized_threat, main_threat_type)
            
            signal = ThreatSignal(
                source=', '.join(detected_words[:3]),
                threat_level=normalized_threat,
                threat_type=main_threat_type,
                response=response
            )
            
            self.recent_threats.append(signal)
            self.recent_threats = self.recent_threats[-10:]
            self.stats['threats_detected'] += 1
            
            return signal
        
        return None
    
    def _determine_response(self, threat_level: float, threat_type: str) -> str:
        """위협에 대한 반응 결정"""
        if threat_type == 'self_harm':
            return "URGENT_SUPPORT"
        elif threat_level >= 0.8:
            return "FIGHT_OR_FLIGHT"
        elif threat_level >= 0.6:
            return "HIGH_ALERT"
        elif threat_level >= 0.4:
            return "CAUTIOUS"
        else:
            return "MONITOR"
    
    # ============================================
    # 핵심 기능: 감정 분석
    # ============================================
    
    def process_emotion(self, input_text: str) -> EmotionState:
        """
        감정 분석 및 처리
        
        수식:
            E = √(V² + A²)
        
        감정 관성:
            V_new = (1-α)·V_input + α·V_current
            α = emotion_inertia
        
        Args:
            input_text: 입력 텍스트
            
        Returns:
            EmotionState
        """
        text_lower = input_text.lower()
        
        detected_emotions = []
        total_valence = 0.0
        total_arousal = 0.0
        count = 0
        
        for emotion_name, info in self.config.emotion_map.items():
            for word in info['words']:
                if word in text_lower:
                    detected_emotions.append(emotion_name)
                    total_valence += info['valence']
                    total_arousal += info['arousal']
                    count += 1
        
        if count > 0:
            input_valence = total_valence / count
            input_arousal = total_arousal / count
            dominant = max(set(detected_emotions), key=detected_emotions.count) if detected_emotions else 'neutral'
        else:
            input_valence = 0.0
            input_arousal = 0.3
            dominant = 'neutral'
        
        # 감정 관성 적용
        inertia = self.config.emotion_inertia
        final_valence = input_valence * (1 - inertia) + self.current_emotion.valence * inertia
        final_arousal = input_arousal * (1 - inertia) + self.current_emotion.arousal * inertia
        
        self.current_emotion = EmotionState(
            valence=final_valence,
            arousal=final_arousal,
            dominant=dominant
        )
        
        self.stats['emotions_processed'] += 1
        
        return self.current_emotion
    
    # ============================================
    # 핵심 기능: 기억 강화
    # ============================================
    
    def calculate_memory_enhancement(
        self,
        emotion: Optional[EmotionState] = None,
        threat: Optional[ThreatSignal] = None
    ) -> float:
        """
        기억 강화 계수 계산
        
        수식:
            M = 1 + α·E·(1 - e^(-β·T))
        
        Args:
            emotion: 감정 상태 (None이면 현재 감정 사용)
            threat: 위협 신호 (None이면 위협 없음)
            
        Returns:
            기억 강화 계수 (1.0 ~ 2.0)
        """
        emotion = emotion or self.current_emotion
        
        E = emotion.intensity
        T = threat.threat_level if threat else 0.0
        
        # M = 1 + α·E·(1 - e^(-β·T))
        enhancement = 1.0 + self.config.alpha * E * (1 - math.exp(-self.config.beta * T))
        
        # 감정만 있어도 약간의 강화
        if T == 0 and E > 0.3:
            enhancement = 1.0 + self.config.alpha * E * 0.5
        
        self.stats['memories_enhanced'] += 1
        
        return min(2.0, enhancement)
    
    def enhance_memory(self, content: str, base_importance: float = 0.5) -> Dict[str, Any]:
        """
        입력에 대해 감정 분석 후 기억 강화
        
        Args:
            content: 기억할 내용
            base_importance: 기본 중요도
            
        Returns:
            강화된 기억 정보
        """
        threat = self.detect_threat(content)
        emotion = self.process_emotion(content)
        enhancement = self.calculate_memory_enhancement(emotion, threat)
        enhanced_importance = min(1.0, base_importance * enhancement)
        
        return {
            'content': content,
            'base_importance': base_importance,
            'enhanced_importance': enhanced_importance,
            'enhancement_factor': enhancement,
            'emotion': {
                'dominant': emotion.dominant,
                'valence': emotion.valence,
                'arousal': emotion.arousal,
                'intensity': emotion.intensity,
            },
            'threat': {
                'detected': threat is not None,
                'level': threat.threat_level if threat else 0.0,
                'type': threat.threat_type if threat else None,
                'response': threat.response if threat else None,
            }
        }
    
    # ============================================
    # 공포 조건화
    # ============================================
    
    def condition_fear(self, stimulus: str, threat: str, strength: float = 0.5):
        """
        공포 조건화 (연합 학습)
        
        CS (조건 자극) + US (무조건 자극) → 연합
        
        수식 (STDP 유사):
            Δw = A_+ · e^(-Δt/τ)
        
        Args:
            stimulus: 조건 자극 (CS)
            threat: 연결할 위협 (US)
            strength: 초기 연합 강도
        """
        key = f"{stimulus}:{threat}"
        current_time = time.time()
        
        if key in self.fear_memories:
            memory = self.fear_memories[key]
            dt = current_time - memory.last_activated
            delta_w = self.config.A_plus * math.exp(-dt / self.config.tau)
            memory.strength = min(1.0, memory.strength + delta_w)
            memory.last_activated = current_time
            memory.activation_count += 1
        else:
            self.fear_memories[key] = FearMemory(
                stimulus=stimulus,
                threat=threat,
                strength=strength
            )
        
        if stimulus not in self.stimulus_threat_cooccurrence:
            self.stimulus_threat_cooccurrence[stimulus] = {}
        self.stimulus_threat_cooccurrence[stimulus][threat] = current_time
        
        self.stats['fear_conditionings'] += 1
    
    def check_fear(self, stimulus: str) -> Optional[FearMemory]:
        """
        공포 기억 확인
        
        Args:
            stimulus: 확인할 자극
            
        Returns:
            연관된 공포 기억 (있으면)
        """
        for key, memory in self.fear_memories.items():
            if stimulus.lower() in memory.stimulus.lower():
                memory.last_activated = time.time()
                memory.activation_count += 1
                return memory
        return None
    
    def extinguish_fear(self, stimulus: str, rate: float = 0.1):
        """
        공포 소거 (안전 경험)
        
        Args:
            stimulus: 소거할 자극
            rate: 소거율
        """
        delete_key = None
        
        for key, memory in list(self.fear_memories.items()):
            if stimulus.lower() in memory.stimulus.lower():
                memory.strength = max(0, memory.strength - rate)
                if memory.strength < 0.1:
                    delete_key = key
                break
        
        if delete_key:
            del self.fear_memories[delete_key]
    
    def contextual_extinction(self, current_time: Optional[float] = None):
        """
        맥락적 소거 (수면 중 자동 실행)
        
        최근 일정 시간 동안 자극과 위협이 동시에 발생하지 않았다면
        연합 강도를 자동 약화
        
        수식:
            co_occurrence_factor = 1 if (stimulus + threat) occurred in time_window else 0
            Δstrength = -extinction_rate × (1 - co_occurrence_factor)
        
        Args:
            current_time: 현재 시간 (None이면 time.time() 사용)
        """
        if current_time is None:
            current_time = time.time()
        
        delete_keys = []
        
        for key, memory in list(self.fear_memories.items()):
            stimulus = memory.stimulus
            threat = memory.threat
            
            # 최근 동시 발생 확인
            co_occurred = False
            if stimulus in self.stimulus_threat_cooccurrence:
                if threat in self.stimulus_threat_cooccurrence[stimulus]:
                    last_cooccurrence = self.stimulus_threat_cooccurrence[stimulus][threat]
                    if current_time - last_cooccurrence < self.config.extinction_time_window:
                        co_occurred = True
            
            # 동시 발생하지 않았으면 약화
            if not co_occurred:
                co_occurrence_factor = 0.0
                delta_strength = -self.config.extinction_rate * (1 - co_occurrence_factor)
                memory.strength = max(0.0, memory.strength + delta_strength)
                
                if memory.strength < 0.1:
                    delete_keys.append(key)
        
        # 완전 소거된 기억 삭제
        for key in delete_keys:
            del self.fear_memories[key]
    
    # ============================================
    # 상태 조회
    # ============================================
    
    def get_state(self) -> Dict[str, Any]:
        """전체 상태 반환"""
        return {
            'current_emotion': {
                'dominant': self.current_emotion.dominant,
                'valence': round(self.current_emotion.valence, 2),
                'arousal': round(self.current_emotion.arousal, 2),
                'intensity': round(self.current_emotion.intensity, 2),
            },
            'fear_memories_count': len(self.fear_memories),
            'recent_threats_count': len(self.recent_threats),
            'stats': self.stats.copy(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return self.stats.copy()
    
    def reset(self):
        """상태 리셋"""
        self.current_emotion = EmotionState()
        self.recent_threats.clear()
        self.fear_memories.clear()
        self.stimulus_threat_cooccurrence.clear()
        self.stats = {
            'threats_detected': 0,
            'emotions_processed': 0,
            'fear_conditionings': 0,
            'memories_enhanced': 0,
        }

