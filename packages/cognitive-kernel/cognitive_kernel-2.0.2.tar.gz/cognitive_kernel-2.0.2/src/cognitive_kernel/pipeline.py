"""
🔀 Decision Pipeline

의사결정 파이프라인 패턴 구현.
알고리즘 순서 변경 및 단계 추가/제거 용이.

Author: GNJz (Qquarts)
Version: 2.0.1+
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field


@dataclass
class PipelineContext:
    """파이프라인 컨텍스트 (단계 간 데이터 전달)"""
    options: List[str]
    memories: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Any] = field(default_factory=list)
    utilities: List[float] = field(default_factory=list)
    probabilities: List[float] = field(default_factory=list)
    entropy: float = 0.0
    core_strength: float = 0.0
    auto_torque: Dict[str, float] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PipelineStep(ABC):
    """파이프라인 단계 추상 클래스"""
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """단계 처리"""
        pass
    
    def __repr__(self) -> str:
        return self.__class__.__name__


class MemoryLoadStep(PipelineStep):
    """기억 로드 단계"""
    
    def __init__(self, memory_engine, working_memory_capacity: int = 7):
        self.memory_engine = memory_engine
        self.working_memory_capacity = working_memory_capacity
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """기억 로드"""
        context.memories = self.memory_engine.recall(k=self.working_memory_capacity)
        return context


class WorkingMemoryStep(PipelineStep):
    """Working Memory 로드 단계"""
    
    def __init__(self, pfc_engine):
        self.pfc_engine = pfc_engine
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """Working Memory에 기억 로드"""
        top_memories_tuples = [
            (m["id"], m["importance"]) for m in context.memories
        ]
        self.pfc_engine.load_from_memoryrank(top_memories_tuples)
        return context


class ActionCreationStep(PipelineStep):
    """Action 생성 단계"""
    
    def __init__(
        self,
        pfc_engine,
        calculate_relevance: Callable,
        extract_keywords: Callable,
        alpha: float = 0.5,
    ):
        self.pfc_engine = pfc_engine
        self.calculate_relevance = calculate_relevance
        self.extract_keywords = extract_keywords
        self.alpha = alpha
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """Action 생성"""
        from .engines.pfc import Action
        
        actions = []
        for i, opt in enumerate(context.options):
            opt_keywords = self.extract_keywords(opt)
            memory_relevance = self.calculate_relevance(opt_keywords, context.memories)
            expected_reward = 0.5 + self.alpha * memory_relevance
            
            actions.append(Action(
                id=f"action_{i}",
                name=opt,
                expected_reward=expected_reward,
                effort_cost=0.2,
                risk=0.1,
            ))
        
        context.actions = actions
        return context


class PFCDecisionStep(PipelineStep):
    """PFC 의사결정 단계"""
    
    def __init__(self, pfc_engine):
        self.pfc_engine = pfc_engine
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """PFC 결정"""
        pfc_result = self.pfc_engine.process(context.actions)
        context.utilities = [
            self.pfc_engine.evaluate_action(a) for a in context.actions
        ]
        context.probabilities = self.pfc_engine.softmax_probabilities(context.utilities)
        context.metadata["pfc_result"] = pfc_result
        return context


class EntropyCalculationStep(PipelineStep):
    """엔트로피 계산 단계"""
    
    def __init__(self, dynamics_engine):
        """
        Args:
            dynamics_engine: DynamicsEngine 인스턴스
        """
        self.dynamics_engine = dynamics_engine
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """엔트로피 계산"""
        context.entropy = self.dynamics_engine.calculate_entropy(
            context.probabilities
        )
        return context


class CoreStrengthStep(PipelineStep):
    """코어 강도 계산 단계 (Core Decay 포함)"""
    
    def __init__(self, dynamics_engine, kernel):
        """
        Args:
            dynamics_engine: DynamicsEngine 인스턴스
            kernel: CognitiveKernel 인스턴스 (mode_config 접근)
        """
        self.dynamics_engine = dynamics_engine
        self.kernel = kernel
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """코어 강도 계산 (Core Decay 동역학 적용)"""
        # DynamicsEngine을 사용하여 코어 강도 계산
        context.core_strength = self.dynamics_engine.calculate_core_strength(
            context.memories,
            memory_update_failure=self.kernel.mode_config.memory_update_failure,
            alpha=self.dynamics_engine.config.memory_alpha,
        )
        
        # 인지적 절규 확인
        distress, message = self.dynamics_engine.check_cognitive_distress(
            context.entropy,
            context.core_strength,
            len(context.options),
        )
        context.metadata["cognitive_distress"] = distress
        context.metadata["distress_message"] = message
        
        return context


class TorqueGenerationStep(PipelineStep):
    """회전 토크 생성 단계"""
    
    def __init__(self, dynamics_engine, mode):
        """
        Args:
            dynamics_engine: DynamicsEngine 인스턴스
            mode: 인지 모드 (CognitiveMode)
        """
        self.dynamics_engine = dynamics_engine
        self.mode = mode
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """회전 토크 생성"""
        # DynamicsEngine을 사용하여 회전 토크 생성
        context.auto_torque = self.dynamics_engine.generate_torque(
            context.options,
            context.entropy,
            self.mode,
        )
        
        # 위상 저장 (메타데이터에)
        context.metadata["precession_phi"] = self.dynamics_engine.state.precession_phi
        
        return context


class UtilityRecalculationStep(PipelineStep):
    """Utility 재계산 단계"""
    
    def __init__(
        self,
        pfc_engine,
        calculate_relevance: Callable,
        extract_keywords: Callable,
        alpha: float = 0.5,
    ):
        self.pfc_engine = pfc_engine
        self.calculate_relevance = calculate_relevance
        self.extract_keywords = extract_keywords
        self.alpha = alpha
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """Utility 재계산 (토크 반영)"""
        from .engines.pfc import Action
        
        if context.auto_torque:
            actions = []
            for i, opt in enumerate(context.options):
                opt_keywords = self.extract_keywords(opt)
                memory_relevance = self.calculate_relevance(opt_keywords, context.memories)
                expected_reward = 0.5 + self.alpha * memory_relevance
                
                # 토크 주입
                if opt in context.auto_torque:
                    expected_reward += context.auto_torque[opt]
                
                actions.append(Action(
                    id=f"action_{i}",
                    name=opt,
                    expected_reward=expected_reward,
                    effort_cost=0.2,
                    risk=0.1,
                ))
            
            context.actions = actions
            # PFC 재결정
            pfc_result = self.pfc_engine.process(actions)
            context.utilities = [
                self.pfc_engine.evaluate_action(a) for a in actions
            ]
            context.probabilities = self.pfc_engine.softmax_probabilities(context.utilities)
            context.metadata["pfc_result"] = pfc_result
        
        return context


class ResultAssemblyStep(PipelineStep):
    """결과 조립 단계"""
    
    def __init__(self, pfc_engine, basal_ganglia_engine=None):
        self.pfc_engine = pfc_engine
        self.basal_ganglia_engine = basal_ganglia_engine
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """최종 결과 조립"""
        pfc_result = context.metadata.get("pfc_result")
        
        probability_distribution = {
            opt: prob for opt, prob in zip(context.options, context.probabilities)
        }
        
        habit_action = None
        if self.basal_ganglia_engine and context.metadata.get("context"):
            habit_action = self.basal_ganglia_engine.select_action(
                context.metadata["context"],
                context.options,
            )
        
        # 인지적 절규 상태 확인
        cognitive_distress = context.metadata.get("cognitive_distress", False)
        distress_message = context.metadata.get("distress_message", "")
        
        context.result = {
            "action": pfc_result.action.name if pfc_result and pfc_result.action else None,
            "utility": pfc_result.utility if pfc_result else 0.0,
            "probability": pfc_result.selection_probability if pfc_result else 0.0,
            "probability_distribution": probability_distribution,
            "entropy": context.entropy,
            "core_strength": context.core_strength,
            "habit_suggestion": habit_action,
            "conflict": (
                pfc_result.action.name != habit_action
                if (pfc_result and pfc_result.action and habit_action)
                else False
            ),
            "cognitive_distress": cognitive_distress,  # 인지적 절규 상태
            "distress_message": distress_message,  # 절규 메시지
        }
        
        return context


class DecisionPipeline:
    """의사결정 파이프라인"""
    
    def __init__(self, steps: List[PipelineStep]):
        """
        Args:
            steps: 파이프라인 단계 리스트 (순서대로 실행)
        """
        self.steps = steps
    
    def execute(self, context: PipelineContext) -> PipelineContext:
        """파이프라인 실행"""
        for step in self.steps:
            context = step.process(context)
        return context
    
    def add_step(self, step: PipelineStep, index: Optional[int] = None):
        """단계 추가"""
        if index is None:
            self.steps.append(step)
        else:
            self.steps.insert(index, step)
    
    def remove_step(self, step: PipelineStep):
        """단계 제거"""
        if step in self.steps:
            self.steps.remove(step)
    
    def replace_step(self, old_step: PipelineStep, new_step: PipelineStep):
        """단계 교체"""
        index = self.steps.index(old_step)
        self.steps[index] = new_step
    
    def __repr__(self) -> str:
        step_names = [step.__class__.__name__ for step in self.steps]
        return f"DecisionPipeline([{', '.join(step_names)}])"

