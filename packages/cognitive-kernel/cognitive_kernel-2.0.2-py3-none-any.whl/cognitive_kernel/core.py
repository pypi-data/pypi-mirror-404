"""
🧠 Cognitive Kernel - 통합 인지 엔진 (Complete Long-term Memory)

진짜 장기 기억 시스템:
- 자동 세션 관리 (with 문 지원)
- 자동 저장/로드
- 7개 엔진 통합 인터페이스
- Edge AI First 설계
- 파이프라인 패턴 지원 (알고리즘 순서 변경 용이)

사용 예시:
    # 기본 사용
    from cognitive_kernel import CognitiveKernel
    
    kernel = CognitiveKernel("my_brain")
    kernel.remember("meeting", {"topic": "project"}, importance=0.9)
    kernel.save()
    
    # 컨텍스트 매니저 (자동 저장)
    with CognitiveKernel("my_brain") as kernel:
        kernel.remember("idea", {"content": "great idea"})
        decision = kernel.decide(["rest", "work", "exercise"])
    # 자동 저장됨
    
    # 커스텀 파이프라인 사용
    from cognitive_kernel.pipeline import DecisionPipeline, MemoryLoadStep, ...
    pipeline = DecisionPipeline([...])
    kernel.set_pipeline(pipeline)

Author: GNJz (Qquarts)
Version: 2.0.1
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# 엔진 임포트
from .engines.panorama import PanoramaMemoryEngine, PanoramaConfig
from .engines.memoryrank import MemoryRankEngine, MemoryRankConfig, MemoryNodeAttributes
from .engines.pfc import PFCEngine, PFCConfig, Action
from .engines.basal_ganglia import BasalGangliaEngine, BasalGangliaConfig
from .engines.thalamus import ThalamusEngine, ThalamusConfig
from .engines.amygdala import AmygdalaEngine, AmygdalaConfig
from .engines.hypothalamus import HypothalamusEngine, HypothalamusConfig
from .engines.dynamics import DynamicsEngine, DynamicsConfig

# 모드 임포트
from .cognitive_modes import CognitiveMode, CognitiveModePresets, ModeConfig

# 파이프라인 임포트 (선택적)
try:
    from .pipeline import (
        DecisionPipeline,
        PipelineContext,
        MemoryLoadStep,
        WorkingMemoryStep,
        ActionCreationStep,
        PFCDecisionStep,
        EntropyCalculationStep,
        CoreStrengthStep,
        TorqueGenerationStep,
        UtilityRecalculationStep,
        ResultAssemblyStep,
    )
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    DecisionPipeline = None


@dataclass
class CognitiveConfig:
    """Cognitive Kernel 설정"""
    
    # 저장 경로
    storage_dir: str = ".cognitive_kernel"
    
    # 자동 저장 설정
    auto_save: bool = True
    auto_save_interval: int = 100  # n개 이벤트마다 자동 저장
    
    # 엔진 설정
    working_memory_capacity: int = 7  # Miller's Law
    recency_half_life: float = 3600.0  # 1시간
    
    # PageRank 설정
    damping: float = 0.85
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "storage_dir": self.storage_dir,
            "auto_save": self.auto_save,
            "auto_save_interval": self.auto_save_interval,
            "working_memory_capacity": self.working_memory_capacity,
            "recency_half_life": self.recency_half_life,
            "damping": self.damping,
        }


class CognitiveKernel:
    """
    🧠 Cognitive Kernel - 통합 인지 엔진
    
    7개 모듈 통합:
    - Panorama: 시간축 기억 (필름)
    - MemoryRank: 중요도 랭킹 (조광기)
    - PFC: 의사결정 (감독)
    - BasalGanglia: 습관 학습 (스태프)
    - Thalamus: 입력 필터링
    - Amygdala: 감정 처리
    - Hypothalamus: 에너지 관리
    
    진짜 장기 기억:
    - 자동 저장/로드
    - 세션 관리
    - 프로세스 종료 후에도 기억 유지
    
    파이프라인 패턴:
    - 알고리즘 순서 변경 용이
    - 커스텀 파이프라인 지원
    """
    
    def __init__(
        self,
        session_name: str = "default",
        config: Optional[CognitiveConfig] = None,
        auto_load: bool = True,
        mode: Optional[CognitiveMode] = None,
        pipeline: Optional[DecisionPipeline] = None,
    ):
        """
        Args:
            session_name: 세션 이름 (저장 파일 이름으로 사용)
            config: 설정 객체
            auto_load: True면 기존 세션 자동 로드
            mode: 인지 모드 (None이면 NORMAL)
            pipeline: 커스텀 파이프라인 (None이면 기본 파이프라인 사용)
        """
        self.session_name = session_name
        self.config = config or CognitiveConfig()
        
        # 모드 설정
        self.mode = mode or CognitiveMode.NORMAL
        self.mode_config = CognitiveModePresets.get_config(self.mode)
        
        # 저장 경로 설정
        self.storage_path = Path(self.config.storage_dir) / session_name
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 엔진 초기화
        self._init_engines()
        
        # 상태
        self._event_count = 0
        self._is_dirty = False
        self._edges: List[Tuple[str, str, float]] = []
        
        # 파이프라인 (선택적, None이면 기본 파이프라인 사용)
        self._pipeline: Optional[DecisionPipeline] = pipeline
        self._pipeline_available = PIPELINE_AVAILABLE
        
        # 동역학 상태는 이제 DynamicsEngine 내부로 이동됨
        # self._entropy_history → self.dynamics.state.entropy_history
        # self._precession_phi → self.dynamics.state.precession_phi
        # self._core_strength_history → self.dynamics.state.core_strength_history
        # self._persistent_core → self.dynamics.state.persistent_core
        # self._last_decay_time → self.dynamics.state.last_decay_time
        # self._cognitive_distress → self.dynamics.state.cognitive_distress
        
        # 자동 로드
        if auto_load and self._session_exists():
            self.load()
    
    def _init_engines(self):
        """엔진 초기화 (모드 설정 적용)"""
        # Panorama (시간축 기억)
        self.panorama = PanoramaMemoryEngine(PanoramaConfig(
            recency_half_life=self.config.recency_half_life,
        ))
        
        # MemoryRank (중요도 랭킹)
        self.memoryrank = MemoryRankEngine(MemoryRankConfig(
            damping=self.mode_config.damping,
            local_weight_boost=self.mode_config.local_weight_boost,
        ))
        
        # PFC (의사결정)
        self.pfc = PFCEngine(PFCConfig(
            working_memory_capacity=self.mode_config.working_memory_capacity,
            decision_temperature=self.mode_config.decision_temperature,
        ))
        
        # BasalGanglia (습관 학습)
        self.basal_ganglia = BasalGangliaEngine(BasalGangliaConfig(
            tau=self.mode_config.tau,
            impulsivity=self.mode_config.impulsivity,
            patience=self.mode_config.patience,
        ))
        
        # Thalamus (입력 필터링) - 모드에 따라 게이팅 조절
        self.thalamus = ThalamusEngine(ThalamusConfig(
            gate_threshold=self.mode_config.gate_threshold,
            max_channels=self.mode_config.max_channels,
        ))
        
        # Amygdala (감정/위협)
        # AmygdalaConfig는 novelty_sensitivity를 직접 지원하지 않음
        # 모드별 설정은 엔진 내부에서 처리
        self.amygdala = AmygdalaEngine(AmygdalaConfig())
        
        # Hypothalamus (에너지/스트레스)
        # HypothalamusConfig는 stress_baseline을 직접 지원하지 않음
        # 모드별 설정은 엔진 내부에서 처리
        self.hypothalamus = HypothalamusEngine(HypothalamusConfig())
        
        # Dynamics Engine (동역학 엔진)
        dynamics_config = DynamicsConfig(
            base_gamma=0.3,
            omega=0.05,
            core_decay_rate=self.mode_config.core_decay_rate,
            memory_update_failure=self.mode_config.memory_update_failure,
            loop_integrity_decay=self.mode_config.loop_integrity_decay,
            entropy_threshold_ratio=0.8,
            core_distress_threshold=0.3,
            history_size=100,
            memory_alpha=0.5,
            # 시간축 분리 (치매/알츠하이머)
            old_memory_decay_rate=self.mode_config.old_memory_decay_rate,
            new_memory_decay_rate=self.mode_config.new_memory_decay_rate,
            memory_age_threshold=self.mode_config.memory_age_threshold,
        )
        self.dynamics = DynamicsEngine(dynamics_config)
        
        # 클래스 참조 저장
        self._MemoryNodeAttributes = MemoryNodeAttributes
        self._Action = Action
    
    def set_mode(self, mode: CognitiveMode) -> None:
        """
        인지 모드 변경
        
        모드를 변경하면 엔진들이 자동으로 재초기화됩니다.
        """
        self.mode = mode
        self.mode_config = CognitiveModePresets.get_config(mode)
        
        # 엔진 재초기화
        self._init_engines()
    
    def set_pipeline(self, pipeline: DecisionPipeline) -> None:
        """
        커스텀 파이프라인 설정
        
        Args:
            pipeline: DecisionPipeline 인스턴스
        """
        if not PIPELINE_AVAILABLE:
            raise ImportError("Pipeline module not available")
        self._pipeline = pipeline
    
    def get_default_pipeline(self) -> DecisionPipeline:
        """기본 파이프라인 생성"""
        if not PIPELINE_AVAILABLE:
            raise ImportError("Pipeline module not available")
        
        return DecisionPipeline([
            MemoryLoadStep(self, self.config.working_memory_capacity),
            WorkingMemoryStep(self.pfc),
            ActionCreationStep(
                self.pfc,
                self._calculate_memory_relevance,
                self._extract_keywords,
                alpha=0.5,
            ),
            PFCDecisionStep(self.pfc),
            EntropyCalculationStep(self.dynamics),  # DynamicsEngine 사용
            CoreStrengthStep(self.dynamics, self),  # DynamicsEngine 사용
            TorqueGenerationStep(self.dynamics, self.mode),  # DynamicsEngine 사용
            UtilityRecalculationStep(
                self.pfc,
                self._calculate_memory_relevance,
                self._extract_keywords,
                alpha=0.5,
            ),
            ResultAssemblyStep(self.pfc, self.basal_ganglia),
        ])
    
    # ==================================================================
    # 핵심 인터페이스 - 간단하게 사용
    # ==================================================================
    
    def remember(
        self,
        event_type: str,
        content: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        emotion: float = 0.0,
        related_to: Optional[List[str]] = None,
    ) -> str:
        """
        기억 저장 (장기 기억)
        
        Args:
            event_type: 이벤트 종류 (예: "meeting", "idea", "conversation")
            content: 이벤트 내용
            importance: 중요도 (0~1)
            emotion: 감정 강도 (0~1)
            related_to: 연관된 기억 ID 리스트
            
        Returns:
            생성된 기억 ID
            
        Example:
            >>> kernel.remember("meeting", {"topic": "project"}, importance=0.9)
            >>> kernel.remember("idea", {"content": "new feature"}, related_to=[...])
        """
        timestamp = time.time()
        
        # Panorama에 이벤트 저장
        event_id = self.panorama.append_event(
            timestamp=timestamp,
            event_type=event_type,
            payload=content or {},
            importance=importance,
        )
        
        # 연관 관계 저장 (MemoryRank 그래프용)
        if related_to:
            for related_id in related_to:
                self._edges.append((related_id, event_id, importance))
                self._edges.append((event_id, related_id, importance * 0.5))  # 양방향 (비대칭)
        
        # 메타데이터 저장
        self._event_count += 1
        self._is_dirty = True
        
        # 자동 저장 체크
        if self.config.auto_save and self._event_count % self.config.auto_save_interval == 0:
            self.save()
        
        return event_id
    
    def recall(self, k: int = 5) -> List[Dict[str, Any]]:
        """
        중요한 기억 회상 (Top-k)
        
        Args:
            k: 회상할 기억 수
            
        Returns:
            중요도 순으로 정렬된 기억 리스트
            
        Example:
            >>> memories = kernel.recall(k=5)
            >>> for m in memories:
            ...     print(f"{m['event_type']}: {m['importance']:.2f}")
        """
        # MemoryRank 그래프 구축
        self._rebuild_graph()
        
        # Top-k 조회
        top_memories = self.memoryrank.get_top_memories(k)
        
        # 이벤트 정보 추가
        results = []
        for event_id, score in top_memories:
            event = self.panorama.get_event(event_id)
            if event:
                results.append({
                    "id": event.id,
                    "event_type": event.event_type,
                    "content": event.payload,
                    "importance": score,
                    "timestamp": event.timestamp,
                })
        
        return results
    
    def decide(
        self,
        options: List[str],
        context: Optional[str] = None,
        use_habit: bool = True,
        external_torque: Optional[Dict[str, float]] = None,
        use_pipeline: bool = True,
    ) -> Dict[str, Any]:
        """
        의사결정 (PFC + BasalGanglia)
        
        Args:
            options: 행동 후보 리스트
            context: 상황 컨텍스트
            use_habit: True면 습관 학습 결과도 반영
            external_torque: 외부 토크 값 (옵션별, 세차운동 등에 사용)
            use_pipeline: True면 파이프라인 패턴 사용 (False면 레거시 방식)
            
        Returns:
            결정 결과
            
        Example:
            >>> result = kernel.decide(["rest", "work", "exercise"])
            >>> print(f"Decision: {result['action']}")
            
            >>> # 세차운동을 위한 토크 주입
            >>> torque = {"choose_red": 0.3, "choose_blue": -0.1, "choose_green": -0.2}
            >>> result = kernel.decide(["choose_red", "choose_blue", "choose_green"], 
            ...                       external_torque=torque)
        """
        # 파이프라인 패턴 사용
        if use_pipeline and PIPELINE_AVAILABLE:
            return self._decide_with_pipeline(options, context, use_habit, external_torque)
        
        # 레거시 방식 (기존 코드)
        return self._decide_legacy(options, context, use_habit, external_torque)
    
    def _decide_with_pipeline(
        self,
        options: List[str],
        context: Optional[str] = None,
        use_habit: bool = True,
        external_torque: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """파이프라인 패턴을 사용한 의사결정"""
        from .pipeline import PipelineContext
        
        # 파이프라인 가져오기 (없으면 기본 파이프라인 생성)
        if self._pipeline is None:
            self._pipeline = self.get_default_pipeline()
        
        # 컨텍스트 생성
        pipeline_context = PipelineContext(
            options=options,
            metadata={"context": context, "use_habit": use_habit, "external_torque": external_torque},
        )
        
        # 파이프라인 실행
        pipeline_context = self._pipeline.execute(pipeline_context)
        
        # 위상 업데이트 (DynamicsEngine 내부에서 처리됨)
        # 히스토리 업데이트 (DynamicsEngine 내부에서 처리됨)
        self.dynamics.update_history(
            pipeline_context.entropy,
            pipeline_context.core_strength,
        )
        
        return pipeline_context.result or {}
    
    def _decide_legacy(
        self,
        options: List[str],
        context: Optional[str] = None,
        use_habit: bool = True,
        external_torque: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """레거시 방식 (기존 코드)"""
        # 기억 로드 → Working Memory
        memories = self.recall(k=self.config.working_memory_capacity)
        
        # MemoryRank 결과를 PFC Working Memory에 로드
        top_memories_tuples = [(m["id"], m["importance"]) for m in memories]
        self.pfc.load_from_memoryrank(top_memories_tuples)
        
        # Action 생성 (MemoryRank 결과를 utility에 반영)
        actions = []
        for i, opt in enumerate(options):
            # 옵션 이름에서 키워드 추출 (예: "choose_red" → ["red"])
            opt_keywords = self._extract_keywords(opt)
            
            # 기억과의 관련성(relevance) 계산
            memory_relevance = self._calculate_memory_relevance(opt_keywords, memories)
            
            # 기억 기반 보상 보정: U_i = U_base + α · r_i
            # α: 기억 영향 계수 (0.5 = 기억이 최대 50%까지 보상에 영향)
            alpha = 0.5
            expected_reward = 0.5 + alpha * memory_relevance
            
            # 외부 토크 주입 (세차운동 등)
            if external_torque and opt in external_torque:
                expected_reward += external_torque[opt]
            
            actions.append(self._Action(
                id=f"action_{i}",
                name=opt,
                expected_reward=expected_reward,
                effort_cost=0.2,
                risk=0.1,
            ))
        
        # PFC 결정
        pfc_result = self.pfc.process(actions)
        
        # 전체 확률 분포 계산 (엔트로피 계산용)
        utilities = [self.pfc.evaluate_action(a) for a in actions]
        probabilities = self.pfc.softmax_probabilities(utilities)
        probability_distribution = {
            opt: prob for opt, prob in zip(options, probabilities)
        }
        
        # 엔트로피 계산 (DynamicsEngine 사용)
        entropy = self.dynamics.calculate_entropy(probabilities)
        
        # 코어 강도 계산 (DynamicsEngine 사용)
        core_strength = self.dynamics.calculate_core_strength(
            memories,
            memory_update_failure=self.mode_config.memory_update_failure,
        )
        
        # 히스토리 업데이트
        self.dynamics.update_history(entropy, core_strength)
        
        # 엔트로피 기반 자동 회전 토크 생성
        # 엔트로피가 높을수록 회전 토크 증가 (ADHD: 궤도 커짐)
        # 엔트로피가 낮을수록 회전 토크 감소 (ASD: 고착)
        auto_torque = {}
        if len(options) > 1:
            # 이론적 최대 엔트로피 (균등 분포)
            max_entropy = math.log(len(options))
            # 정규화된 엔트로피 (0~1)
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
            
            # 회전 토크 세기: 엔트로피에 비례
            # 모드별 기본 회전 강도
            base_gamma = 0.3  # 기본 회전 토크 세기
            if self.mode == CognitiveMode.ADHD:
                gamma = base_gamma * 1.5  # ADHD: 더 강한 회전
            elif self.mode == CognitiveMode.ASD:
                gamma = base_gamma * 0.5  # ASD: 약한 회전
            else:
                gamma = base_gamma
            
            # 엔트로피 기반 토크 조절
            # 높은 엔트로피 → 강한 회전 (ADHD)
            # 낮은 엔트로피 → 약한 회전 (ASD)
            torque_strength = gamma * normalized_entropy
            
            # 세차 속도 (느린 시간척도)
            omega = 0.05
            
            # 옵션별 위상 (균등 분포)
            psi = {opt: i * 2 * math.pi / len(options) 
                   for i, opt in enumerate(options)}
            
            # 회전 토크 생성 (DynamicsEngine 사용)
            auto_torque = self.dynamics.generate_torque(
                options,
                entropy,
                self.mode,
                base_gamma=base_gamma,
                omega=omega,
            )
        
        # 자동 토크를 외부 토크에 병합
        if external_torque is None:
            external_torque = {}
        for opt, torque in auto_torque.items():
            external_torque[opt] = external_torque.get(opt, 0.0) + torque
        
        # 자동 토크가 있으면 utility 재계산
        if auto_torque:
            actions = []
            for i, opt in enumerate(options):
                opt_keywords = self._extract_keywords(opt)
                memory_relevance = self._calculate_memory_relevance(opt_keywords, memories)
                alpha = 0.5
                expected_reward = 0.5 + alpha * memory_relevance
                
                # 자동 토크 주입
                if opt in external_torque:
                    expected_reward += external_torque[opt]
                
                actions.append(self._Action(
                    id=f"action_{i}",
                    name=opt,
                    expected_reward=expected_reward,
                    effort_cost=0.2,
                    risk=0.1,
                ))
            
            # PFC 재결정
            pfc_result = self.pfc.process(actions)
            utilities = [self.pfc.evaluate_action(a) for a in actions]
            probabilities = self.pfc.softmax_probabilities(utilities)
            probability_distribution = {
                opt: prob for opt, prob in zip(options, probabilities)
            }
        
        # 습관 반영
        habit_action = None
        if use_habit and context:
            habit_action = self.basal_ganglia.select_action(context, options)
        
        return {
            "action": pfc_result.action.name if pfc_result.action else None,
            "utility": pfc_result.utility,
            "probability": pfc_result.selection_probability,
            "probability_distribution": probability_distribution,  # 전체 분포
            "entropy": entropy,  # 엔트로피
            "core_strength": core_strength,  # 코어 강도
            "habit_suggestion": habit_action,
            "conflict": pfc_result.action.name != habit_action if (pfc_result.action and habit_action) else False,
        }
    
    def _decide_with_pipeline(
        self,
        options: List[str],
        context: Optional[str] = None,
        use_habit: bool = True,
        external_torque: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """파이프라인 패턴을 사용한 의사결정"""
        from .pipeline import (
            DecisionPipeline,
            PipelineContext,
            MemoryLoadStep,
            WorkingMemoryStep,
            ActionCreationStep,
            PFCDecisionStep,
            EntropyCalculationStep,
            CoreStrengthStep,
            TorqueGenerationStep,
            UtilityRecalculationStep,
            ResultAssemblyStep,
        )
        
        # 파이프라인 가져오기 (없으면 기본 파이프라인 생성)
        if self._pipeline is None:
            self._pipeline = DecisionPipeline([
                MemoryLoadStep(self, self.config.working_memory_capacity),
                WorkingMemoryStep(self.pfc),
                ActionCreationStep(
                    self.pfc,
                    self._calculate_memory_relevance,
                    self._extract_keywords,
                    alpha=0.5,
                ),
                PFCDecisionStep(self.pfc),
                EntropyCalculationStep(self.dynamics),  # DynamicsEngine 사용
                CoreStrengthStep(self.dynamics, self),  # DynamicsEngine 사용
                TorqueGenerationStep(self.dynamics, self.mode),  # DynamicsEngine 사용
                UtilityRecalculationStep(
                    self.pfc,
                    self._calculate_memory_relevance,
                    self._extract_keywords,
                    alpha=0.5,
                ),
                ResultAssemblyStep(self.pfc, self.basal_ganglia),
            ])
        
        # 컨텍스트 생성
        pipeline_context = PipelineContext(
            options=options,
            metadata={"context": context, "use_habit": use_habit, "external_torque": external_torque},
        )
        
        # 파이프라인 실행
        pipeline_context = self._pipeline.execute(pipeline_context)
        
        # 위상 업데이트 (DynamicsEngine 내부에서 처리됨)
        # 히스토리 업데이트 (DynamicsEngine 내부에서 처리됨)
        self.dynamics.update_history(
            pipeline_context.entropy,
            pipeline_context.core_strength,
        )
        
        return pipeline_context.result or {}
    
    def set_pipeline(self, pipeline: Any) -> None:
        """
        커스텀 파이프라인 설정
        
        Args:
            pipeline: DecisionPipeline 인스턴스
        """
        if not self._pipeline_available:
            raise ImportError("Pipeline module not available. Install required dependencies.")
        self._pipeline = pipeline
    
    def get_default_pipeline(self) -> Any:
        """기본 파이프라인 생성"""
        if not self._pipeline_available:
            raise ImportError("Pipeline module not available. Install required dependencies.")
        
        from .pipeline import (
            DecisionPipeline,
            MemoryLoadStep,
            WorkingMemoryStep,
            ActionCreationStep,
            PFCDecisionStep,
            EntropyCalculationStep,
            CoreStrengthStep,
            TorqueGenerationStep,
            UtilityRecalculationStep,
            ResultAssemblyStep,
        )
        
        return DecisionPipeline([
            MemoryLoadStep(self, self.config.working_memory_capacity),
            WorkingMemoryStep(self.pfc),
            ActionCreationStep(
                self.pfc,
                self._calculate_memory_relevance,
                self._extract_keywords,
                alpha=0.5,
            ),
            PFCDecisionStep(self.pfc),
            EntropyCalculationStep(self.dynamics),  # DynamicsEngine 사용
            CoreStrengthStep(self.dynamics, self),  # DynamicsEngine 사용
            TorqueGenerationStep(self.dynamics, self.mode),  # DynamicsEngine 사용
            UtilityRecalculationStep(
                self.pfc,
                self._calculate_memory_relevance,
                self._extract_keywords,
                alpha=0.5,
            ),
            ResultAssemblyStep(self.pfc, self.basal_ganglia),
        ])
    
    def learn_from_reward(
        self,
        context: str,
        action: str,
        reward: float,
    ):
        """
        보상 학습 (습관 형성)
        
        Args:
            context: 상황
            action: 수행한 행동
            reward: 보상 값 (0~1)
            
        Example:
            >>> kernel.learn_from_reward("tired", "rest", reward=0.8)
        """
        self.basal_ganglia.update(context, action, reward)
        self._is_dirty = True
    
    def _extract_keywords(self, option_name: str) -> List[str]:
        """
        옵션 이름에서 키워드 추출
        
        예: "choose_red" → ["red"]
            "work_on_project" → ["work", "project"]
        """
        # 언더스코어/하이픈으로 분리
        keywords = []
        for part in option_name.replace("_", " ").replace("-", " ").split():
            # "choose", "select", "do" 같은 동사 제거
            if part.lower() not in ["choose", "select", "do", "pick", "take", "make"]:
                keywords.append(part.lower())
        return keywords if keywords else [option_name.lower()]
    
    def _calculate_memory_relevance(
        self,
        option_keywords: List[str],
        memories: List[Dict[str, Any]],
    ) -> float:
        """
        옵션과 기억의 관련성 계산
        
        수식: relevance = Σ (importance_i × match_score_i)
        - importance_i: MemoryRank 중요도
        - match_score_i: 키워드 매칭 점수 (0~1)
        
        Returns:
            관련성 점수 (0~1)
        """
        if not memories or not option_keywords:
            return 0.0
        
        total_relevance = 0.0
        
        for mem in memories:
            # 기억 내용을 문자열로 변환
            content = mem.get("content", {})
            if isinstance(content, dict):
                # 딕셔너리면 모든 값들을 문자열로 합침
                content_text = " ".join(str(v) for v in content.values()).lower()
            else:
                content_text = str(content).lower()
            
            # 키워드 매칭 점수 계산
            match_score = 0.0
            for keyword in option_keywords:
                if keyword in content_text:
                    # 키워드가 포함되어 있으면 점수 증가
                    match_score += 1.0 / len(option_keywords)
            
            # 관련성 = 중요도 × 매칭 점수
            importance = mem.get("importance", 0.0)
            total_relevance += importance * match_score
        
        # 정규화 (0~1 범위로)
        return min(1.0, total_relevance)
    
    def _rebuild_graph(self):
        """MemoryRank 그래프 재구축"""
        events = self.panorama.get_all_events()
        
        # 이벤트가 없으면 종료
        if not events:
            return
        
        # 엣지가 없으면 시간 순서로 연결
        if not self._edges:
            if len(events) > 1:
                for i in range(len(events) - 1):
                    self._edges.append((events[i].id, events[i+1].id, 0.5))
            elif len(events) == 1:
                # 이벤트가 1개뿐이면 자기 자신으로 연결
                self._edges.append((events[0].id, events[0].id, 0.5))
        
        # 노드 속성 생성
        recency_scores = self.panorama.get_recency_scores()
        node_attrs = {}
        
        for event in events:
            node_attrs[event.id] = self._MemoryNodeAttributes(
                recency=recency_scores.get(event.id, 0.5),
                emotion=event.payload.get("emotion", 0.0) if event.payload else 0.0,
                frequency=1.0,
                base_importance=event.importance,
            )
        
        # 그래프 구축
        # local_weight_boost는 MemoryRankConfig에서 처리됨
        
        # Loop Integrity Decay (알츠하이머: 엣지 소실)
        edges_to_use = self._edges
        if self.mode_config.loop_integrity_decay > 0:
            import random
            # 엣지 소실 확률 적용
            edges_to_use = [
                edge for edge in self._edges
                if random.random() > self.mode_config.loop_integrity_decay
            ]
        
        if edges_to_use and node_attrs:
            self.memoryrank.build_graph(edges_to_use, node_attrs)
            self.memoryrank.calculate_importance()
    
    # ==================================================================
    # 영속성 (장기 기억의 핵심)
    # ==================================================================
    
    def save(self) -> Dict[str, int]:
        """
        세션 저장 (장기 기억)
        
        Returns:
            저장 통계
        """
        stats = {}
        
        # Panorama 저장
        panorama_path = self.storage_path / "panorama.json"
        stats["events"] = self.panorama.save_to_json(str(panorama_path))
        
        # MemoryRank 저장
        if self.memoryrank._M is not None:
            memoryrank_path = self.storage_path / "memoryrank.json"
            result = self.memoryrank.save_to_json(str(memoryrank_path))
            stats["nodes"] = result["nodes"]
        
        # Edges 저장
        edges_path = self.storage_path / "edges.json"
        edges_path.write_text(json.dumps(self._edges, indent=2))
        stats["edges"] = len(self._edges)
        
        # BasalGanglia Q-values 저장
        q_path = self.storage_path / "q_values.json"
        q_data = {}
        if hasattr(self.basal_ganglia, '_q_table'):
            q_data = {k: dict(v) for k, v in self.basal_ganglia._q_table.items()}
        q_path.write_text(json.dumps(q_data, indent=2))
        
        # 메타데이터 저장
        meta_path = self.storage_path / "meta.json"
        meta_path.write_text(json.dumps({
            "session_name": self.session_name,
            "event_count": self._event_count,
            "last_saved": time.time(),
            "config": self.config.to_dict(),
            "mode": self.mode.value,
        }, indent=2))
        
        self._is_dirty = False
        return stats
    
    def load(self) -> Dict[str, int]:
        """
        세션 로드 (장기 기억 복구)
        
        Returns:
            로드 통계
        """
        stats = {}
        
        # Panorama 로드
        panorama_path = self.storage_path / "panorama.json"
        if panorama_path.exists():
            stats["events"] = self.panorama.load_from_json(str(panorama_path))
        
        # MemoryRank 로드
        memoryrank_path = self.storage_path / "memoryrank.json"
        if memoryrank_path.exists():
            result = self.memoryrank.load_from_json(str(memoryrank_path))
            stats["nodes"] = result["nodes"]
        
        # Edges 로드
        edges_path = self.storage_path / "edges.json"
        if edges_path.exists():
            self._edges = json.loads(edges_path.read_text())
            stats["edges"] = len(self._edges)
        
        # BasalGanglia Q-values 로드
        q_path = self.storage_path / "q_values.json"
        if q_path.exists():
            q_data = json.loads(q_path.read_text())
            if hasattr(self.basal_ganglia, '_q_table'):
                from collections import defaultdict
                self.basal_ganglia._q_table = defaultdict(
                    lambda: defaultdict(float),
                    {k: defaultdict(float, v) for k, v in q_data.items()}
                )
        
        # 메타데이터 로드
        meta_path = self.storage_path / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            self._event_count = meta.get("event_count", 0)
            # 모드 복구 (선택적)
            if "mode" in meta:
                try:
                    self.mode = CognitiveMode(meta["mode"])
                    self.mode_config = CognitiveModePresets.get_config(self.mode)
                except ValueError:
                    pass
        
        self._is_dirty = False
        return stats
    
    def _session_exists(self) -> bool:
        """세션 파일 존재 여부"""
        return (self.storage_path / "meta.json").exists()
    
    # ==================================================================
    # 컨텍스트 매니저 (자동 저장)
    # ==================================================================
    
    def __enter__(self) -> "CognitiveKernel":
        """with 문 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with 문 종료 - 자동 저장"""
        if self._is_dirty:
            self.save()
        return False
    
    # ==================================================================
    # 유틸리티
    # ==================================================================
    
    def status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        status_dict = {
            "session_name": self.session_name,
            "storage_path": str(self.storage_path),
            "event_count": len(self.panorama),
            "edge_count": len(self._edges),
            "is_dirty": self._is_dirty,
            "auto_save": self.config.auto_save,
            "mode": self.mode.value,
            "pipeline_enabled": self._pipeline is not None,
        }
        
        # Dynamics Engine 상태 추가
        dynamics_status = self.dynamics.get_status()
        status_dict["dynamics"] = {
            **dynamics_status,
            "core_decay_rate": self.mode_config.core_decay_rate,
            "memory_update_failure": self.mode_config.memory_update_failure,
            "loop_integrity_decay": self.mode_config.loop_integrity_decay,
        }
        
        return status_dict
    
    def clear(self):
        """모든 기억 삭제 (주의!)"""
        self.panorama.clear()
        self._edges.clear()
        self._event_count = 0
        self._is_dirty = True
    
    def __repr__(self) -> str:
        return f"CognitiveKernel(session='{self.session_name}', events={len(self.panorama)}, mode={self.mode.value})"
    
    def __len__(self) -> int:
        """이벤트 수 반환"""
        return len(self.panorama)


# ==================================================================
# 편의 함수
# ==================================================================

def create_kernel(session_name: str = "default", **kwargs) -> CognitiveKernel:
    """CognitiveKernel 생성 편의 함수"""
    config = CognitiveConfig(**kwargs)
    return CognitiveKernel(session_name, config)
