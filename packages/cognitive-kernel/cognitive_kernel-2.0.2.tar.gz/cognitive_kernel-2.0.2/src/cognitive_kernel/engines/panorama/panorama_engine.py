from __future__ import annotations

import bisect
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


from .config import PanoramaConfig


@dataclass(frozen=True)
class Event:
    """불변(Immutable) 이벤트 객체.

    - id: 고유 식별자
    - timestamp: Unix timestamp (초 단위, float)
    - event_type: 이벤트 종류 (예: "memory_recall", "state_change")
    - payload: 이벤트 데이터 (자유 형식)
    - episode_id: 소속 에피소드 ID (선택)
    - importance: 베이스 중요도 (0~1)
    """

    id: str
    timestamp: float
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    episode_id: Optional[str] = None
    importance: float = 0.5


@dataclass
class Episode:
    """에피소드 (연속된 이벤트의 의미 단위 묶음).

    - id: 에피소드 고유 식별자
    - event_ids: 포함된 이벤트 ID 리스트
    - start_time: 첫 이벤트 시간
    - end_time: 마지막 이벤트 시간
    """

    id: str
    event_ids: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class PanoramaMemoryEngine:
    """Panorama Memory Engine v1.0

    시간축 기반 에피소드 기억 엔진.
    - 이벤트를 시간 순으로 저장
    - 시간 구간 쿼리 (Range Query)
    - 에피소드 자동 분할
    - 지수 감쇠 기반 중요도 계산 (MemoryRank 연동용)
    """

    def __init__(self, config: Optional[PanoramaConfig] = None):
        self.config = config or PanoramaConfig()
        self._events: List[Event] = []              # 시간 순 정렬
        self._timestamps: List[float] = []          # 이진 검색용 타임스탬프 리스트
        self._event_map: Dict[str, Event] = {}      # id → Event
        self._episode_index: Dict[str, List[str]] = {}  # episode_id → [event_ids]

    # ------------------------------------------------------------------
    # 이벤트 추가
    # ------------------------------------------------------------------
    def append_event(
        self,
        timestamp: float,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        episode_id: Optional[str] = None,
        importance: float = 0.5,
        event_id: Optional[str] = None,
    ) -> str:
        """새 이벤트를 타임라인에 추가.

        Args:
            timestamp: Unix timestamp (초 단위)
            event_type: 이벤트 종류
            payload: 이벤트 데이터
            episode_id: 소속 에피소드 ID (선택)
            importance: 베이스 중요도 (0~1)
            event_id: 고유 ID (없으면 자동 생성)

        Returns:
            생성된 이벤트 ID
        """
        if event_id is None:
            event_id = str(uuid.uuid4())

        event = Event(
            id=event_id,
            timestamp=float(timestamp),
            event_type=event_type,
            payload=payload or {},
            episode_id=episode_id,
            importance=max(0.0, min(1.0, float(importance))),
        )

        # 이진 삽입으로 정렬 유지
        idx = bisect.bisect_right(self._timestamps, event.timestamp)
        self._events.insert(idx, event)
        self._timestamps.insert(idx, event.timestamp)
        self._event_map[event.id] = event

        # 에피소드 인덱스 업데이트
        if episode_id:
            if episode_id not in self._episode_index:
                self._episode_index[episode_id] = []
            self._episode_index[episode_id].append(event.id)

        # 최대 이벤트 수 초과 시 가장 오래된 이벤트 제거
        while len(self._events) > self.config.max_events:
            oldest = self._events.pop(0)
            self._timestamps.pop(0)
            del self._event_map[oldest.id]
            if oldest.episode_id and oldest.episode_id in self._episode_index:
                self._episode_index[oldest.episode_id].remove(oldest.id)
                if not self._episode_index[oldest.episode_id]:
                    del self._episode_index[oldest.episode_id]

        return event.id

    # ------------------------------------------------------------------
    # 시간 구간 쿼리
    # ------------------------------------------------------------------
    def query_range(self, t_start: float, t_end: float) -> List[Event]:
        """시간 범위 [t_start, t_end] 내의 모든 이벤트 조회.

        Args:
            t_start: 시작 시간 (포함)
            t_end: 종료 시간 (포함)

        Returns:
            시간 순 정렬된 이벤트 리스트
        """
        i_start = bisect.bisect_left(self._timestamps, t_start)
        i_end = bisect.bisect_right(self._timestamps, t_end)
        return self._events[i_start:i_end]

    # ------------------------------------------------------------------
    # 에피소드 조회
    # ------------------------------------------------------------------
    def get_episode(self, episode_id: str) -> List[Event]:
        """특정 에피소드의 모든 이벤트를 시간 순으로 반환.

        Args:
            episode_id: 에피소드 ID

        Returns:
            시간 순 정렬된 이벤트 리스트
        """
        event_ids = self._episode_index.get(episode_id, [])
        events = [self._event_map[eid] for eid in event_ids if eid in self._event_map]
        return sorted(events, key=lambda e: e.timestamp)

    def get_episode_ids(self) -> List[str]:
        """모든 에피소드 ID 반환."""
        return list(self._episode_index.keys())

    # ------------------------------------------------------------------
    # 최근 이벤트 조회
    # ------------------------------------------------------------------
    def get_recent(self, n: int = 10) -> List[Event]:
        """가장 최근 n개 이벤트 반환.

        Args:
            n: 반환할 이벤트 수

        Returns:
            최근 이벤트 리스트 (가장 오래된 것부터)
        """
        return self._events[-n:] if n > 0 else []

    # ------------------------------------------------------------------
    # 에피소드 자동 분할
    # ------------------------------------------------------------------
    def segment_episodes(
        self,
        method: str = "time_gap",
        threshold: Optional[float] = None,
        marker_types: Optional[List[str]] = None,
    ) -> List[Episode]:
        """이벤트들을 에피소드로 자동 분할.

        Args:
            method: 분할 방법 ("time_gap" 또는 "marker")
            threshold: 시간 갭 임계값 (time_gap 방식, 기본값: config.time_gap_threshold)
            marker_types: 경계 마커 이벤트 타입 (marker 방식)

        Returns:
            생성된 에피소드 리스트
        """
        if not self._events:
            return []

        if method == "time_gap":
            return self._segment_by_time_gap(threshold)
        elif method == "marker":
            return self._segment_by_marker(marker_types or [])
        else:
            raise ValueError(f"Unknown segmentation method: {method}")

    def _segment_by_time_gap(self, threshold: Optional[float]) -> List[Episode]:
        """시간 갭 기반 에피소드 분할."""
        tau = threshold if threshold is not None else self.config.time_gap_threshold
        episodes: List[Episode] = []
        current_ids: List[str] = [self._events[0].id]

        for i in range(1, len(self._events)):
            gap = self._events[i].timestamp - self._events[i - 1].timestamp
            if gap > tau:
                # 현재 에피소드 완료
                episode = self._create_episode(current_ids)
                episodes.append(episode)
                current_ids = []
            current_ids.append(self._events[i].id)

        # 마지막 에피소드
        if current_ids:
            episode = self._create_episode(current_ids)
            episodes.append(episode)

        return episodes

    def _segment_by_marker(self, marker_types: List[str]) -> List[Episode]:
        """이벤트 마커 기반 에피소드 분할."""
        episodes: List[Episode] = []
        current_ids: List[str] = []

        for event in self._events:
            if event.event_type in marker_types and current_ids:
                episode = self._create_episode(current_ids)
                episodes.append(episode)
                current_ids = []
            current_ids.append(event.id)

        if current_ids:
            episode = self._create_episode(current_ids)
            episodes.append(episode)

        return episodes

    def _create_episode(self, event_ids: List[str]) -> Episode:
        """이벤트 ID 리스트로부터 Episode 객체 생성."""
        episode_id = str(uuid.uuid4())
        events = [self._event_map[eid] for eid in event_ids]
        return Episode(
            id=episode_id,
            event_ids=event_ids,
            start_time=events[0].timestamp if events else None,
            end_time=events[-1].timestamp if events else None,
        )

    # ------------------------------------------------------------------
    # 중요도 계산 (MemoryRank 연동용)
    # ------------------------------------------------------------------
    def get_importance_scores(
        self,
        t_now: Optional[float] = None,
    ) -> Dict[str, float]:
        """지수 감쇠 적용된 중요도 점수 반환.

        Args:
            t_now: 현재 시간 (기본값: time.time())

        Returns:
            {event_id: importance_score} 딕셔너리
        """
        if t_now is None:
            t_now = time.time()

        # λ = ln(2) / half_life
        half_life = self.config.recency_half_life
        lambda_decay = math.log(2) / half_life if half_life > 0 else 0.0

        scores: Dict[str, float] = {}
        for event in self._events:
            delta_t = max(0.0, t_now - event.timestamp)
            decay = math.exp(-lambda_decay * delta_t)
            scores[event.id] = event.importance * decay

        return scores

    def get_recency_scores(self, t_now: Optional[float] = None) -> Dict[str, float]:
        """최근성 점수만 반환 (0~1, 지수 감쇠).

        MemoryRank의 recency 속성으로 바로 사용 가능.
        """
        if t_now is None:
            t_now = time.time()

        half_life = self.config.recency_half_life
        lambda_decay = math.log(2) / half_life if half_life > 0 else 0.0

        scores: Dict[str, float] = {}
        for event in self._events:
            delta_t = max(0.0, t_now - event.timestamp)
            scores[event.id] = math.exp(-lambda_decay * delta_t)

        return scores

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------
    def get_event(self, event_id: str) -> Optional[Event]:
        """ID로 이벤트 조회."""
        return self._event_map.get(event_id)

    def get_all_events(self) -> List[Event]:
        """모든 이벤트 반환 (시간 순)."""
        return list(self._events)

    def __len__(self) -> int:
        """저장된 이벤트 수."""
        return len(self._events)

    def clear(self) -> None:
        """모든 이벤트 삭제."""
        self._events.clear()
        self._timestamps.clear()
        self._event_map.clear()
        self._episode_index.clear()

    # ------------------------------------------------------------------
    # 영속성 (Persistence) - 장기 기억의 핵심
    # ------------------------------------------------------------------
    def save_to_json(self, path: str, indent: int = 2) -> int:
        """이벤트를 JSON 파일로 저장 (장기 기억)
        
        Args:
            path: 저장 경로
            indent: JSON 들여쓰기 (None이면 압축)
            
        Returns:
            저장된 이벤트 수
        """
        from .persistence import save_to_json as _save
        return _save(self, path, indent)
    
    def load_from_json(self, path: str, clear_existing: bool = True) -> int:
        """JSON 파일에서 이벤트 로드
        
        Args:
            path: 파일 경로
            clear_existing: True면 기존 이벤트 삭제 후 로드
            
        Returns:
            로드된 이벤트 수
        """
        from .persistence import load_from_json as _load
        return _load(self, path, clear_existing)
    
    def save_to_sqlite(self, path: str) -> int:
        """이벤트를 SQLite DB로 저장 (장기 기억)
        
        대용량 이벤트에 적합.
        
        Args:
            path: SQLite 파일 경로
            
        Returns:
            저장된 이벤트 수
        """
        from .persistence import save_to_sqlite as _save
        return _save(self, path)
    
    def load_from_sqlite(self, path: str, clear_existing: bool = True) -> int:
        """SQLite DB에서 이벤트 로드
        
        Args:
            path: SQLite 파일 경로
            clear_existing: True면 기존 이벤트 삭제 후 로드
            
        Returns:
            로드된 이벤트 수
        """
        from .persistence import load_from_sqlite as _load
        return _load(self, path, clear_existing)
