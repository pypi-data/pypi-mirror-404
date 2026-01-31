"""
🔌 Cognitive Engine Interfaces

Edge AI를 위한 엔진 인터페이스 정의.
각 엔진이 구현해야 하는 표준 인터페이스.

Author: GNJz (Qquarts)
Version: 2.0.1+
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple


class MemoryEngine(ABC):
    """기억 엔진 인터페이스"""
    
    @abstractmethod
    def remember(
        self,
        event_type: str,
        content: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
    ) -> str:
        """기억 저장"""
        pass
    
    @abstractmethod
    def recall(self, k: int = 5) -> List[Dict[str, Any]]:
        """기억 회상"""
        pass


class RankingEngine(ABC):
    """랭킹 엔진 인터페이스"""
    
    @abstractmethod
    def build_graph(
        self,
        edges: List[Tuple[str, str, float]],
        node_attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """그래프 구축"""
        pass
    
    @abstractmethod
    def calculate_importance(self) -> None:
        """중요도 계산"""
        pass
    
    @abstractmethod
    def get_top_memories(self, k: int) -> List[Tuple[str, float]]:
        """상위 k개 기억 반환"""
        pass


class DecisionEngine(ABC):
    """의사결정 엔진 인터페이스"""
    
    @abstractmethod
    def process(self, actions: List[Any]) -> Any:
        """의사결정 처리"""
        pass
    
    @abstractmethod
    def evaluate_action(self, action: Any) -> float:
        """행동 평가"""
        pass


class HabitEngine(ABC):
    """습관 학습 엔진 인터페이스"""
    
    @abstractmethod
    def select_action(
        self,
        context: str,
        options: List[str],
    ) -> Optional[str]:
        """습관 기반 행동 선택"""
        pass
    
    @abstractmethod
    def update(
        self,
        context: str,
        action: str,
        reward: float,
    ) -> None:
        """보상 학습"""
        pass


class FilteringEngine(ABC):
    """필터링 엔진 인터페이스"""
    
    @abstractmethod
    def filter_single(
        self,
        event_type: str,
        importance: float,
        threshold: float,
    ) -> Any:
        """단일 입력 필터링"""
        pass


class EmotionEngine(ABC):
    """감정 엔진 인터페이스"""
    
    @abstractmethod
    def process_emotion(
        self,
        stimulus: Dict[str, Any],
    ) -> float:
        """감정 처리"""
        pass


class EnergyEngine(ABC):
    """에너지 관리 엔진 인터페이스"""
    
    @abstractmethod
    def get_energy(self) -> float:
        """에너지 상태 조회"""
        pass
    
    @abstractmethod
    def get_stress(self) -> float:
        """스트레스 상태 조회"""
        pass

