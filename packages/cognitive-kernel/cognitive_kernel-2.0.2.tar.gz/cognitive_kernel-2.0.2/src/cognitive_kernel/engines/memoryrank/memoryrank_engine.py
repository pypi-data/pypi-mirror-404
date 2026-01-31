from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Iterable

import numpy as np

from .config import MemoryRankConfig


@dataclass
class MemoryNodeAttributes:
    """각 메모리 노드의 베이스 중요도 구성 요소.

    recency      : 최근성 (0~1, 최근일수록 1에 가까움)
    emotion      : 정서 강도 (0~1, 강렬할수록 높음)
    frequency    : 등장/재생 빈도 (0~1, 자주 등장할수록 높음)
    base_importance: 외부에서 직접 주는 기본 가중치 (선택)
    """

    recency: float = 0.0
    emotion: float = 0.0
    frequency: float = 0.0
    base_importance: float = 0.0


class MemoryRankEngine:
    """MemoryRankEngine v1.0

    - 입력:
        * 메모리 노드 id (str 등 hashable)
        * directed edges: (src_id, dst_id, weight)
        * 선택적으로 노드 속성 (recency, emotion, frequency, base_importance)

    - 내부 표현:
        * 노드 id ↔ index 매핑
        * 열 정규화된 전이 행렬 M (N x N)
        * personalization vector v (N)

    - 출력:
        * {node_id: rank_score} 딕셔너리
        * get_top_memories(n) 로 상위 n개 조회
    """

    def __init__(self, config: Optional[MemoryRankConfig] = None):
        self.config = config or MemoryRankConfig()
        self._id_to_index: Dict[str, int] = {}
        self._index_to_id: List[str] = []
        self._M: Optional[np.ndarray] = None  # transition matrix
        self._v: Optional[np.ndarray] = None  # personalization vector
        self._r: Optional[np.ndarray] = None  # latest rank vector

    # ------------------------------------------------------------------
    # 그래프 구성
    # ------------------------------------------------------------------
    def build_graph(
        self,
        edges: Iterable[Tuple[str, str, float]],
        node_attributes: Optional[Dict[str, MemoryNodeAttributes]] = None,
    ) -> None:
        """메모리 그래프를 구성한다.

        edges:
            (src_id, dst_id, weight) 이터러블
            "src 기억을 떠올리면 dst로 전이될 가능성이 있다"는 의미

        node_attributes:
            각 노드별 MemoryNodeAttributes
            없으면 균등한 베이스 중요도를 사용
        """
        # 노드 수집
        node_ids: Dict[str, None] = {}
        for s, d, _ in edges:
            node_ids[s] = None
            node_ids[d] = None

        self._index_to_id = sorted(node_ids.keys())
        self._id_to_index = {nid: i for i, nid in enumerate(self._index_to_id)}
        n = len(self._index_to_id)
        if n == 0:
            self._M = None
            self._v = None
            self._r = None
            return

        # 가중치 행렬 W[i, j] = j -> i 로의 weight
        W = np.zeros((n, n), dtype=float)
        for src, dst, w in edges:
            if w <= 0:
                continue
            if src not in self._id_to_index or dst not in self._id_to_index:
                continue
            i = self._id_to_index[dst]
            j = self._id_to_index[src]
            
            base_weight = float(w)
            
            # 로컬 연결 강화 (local_weight_boost)
            if self.config.local_weight_boost > 1.0:
                if self._is_local_connection(src, dst, node_attributes):
                    base_weight *= self.config.local_weight_boost
            
            W[i, j] += base_weight

        # 열 정규화 → 전이 행렬 M
        col_sums = W.sum(axis=0)
        M = np.zeros_like(W)
        for j in range(n):
            if col_sums[j] > 0:
                M[:, j] = W[:, j] / col_sums[j]
            else:
                # out-degree 0이면 모든 노드로 균등 분포
                M[:, j] = 1.0 / n
        self._M = M

        # personalization vector v 생성
        self._v = self._build_personalization_vector(node_attributes)

        # 기존 rank는 무효화
        self._r = None
    
    def _is_local_connection(
        self,
        node1_id: str,
        node2_id: str,
        node_attributes: Optional[Dict[str, MemoryNodeAttributes]],
    ) -> bool:
        """
        로컬 연결 여부 판단
        
        정의:
        - 시간적 근접성: 같은 세션, 비슷한 시간대에 저장된 기억
        - 같은 이벤트 타입: 같은 event_type을 가진 기억
        - 직접 연결: 엣지로 직접 연결된 노드
        
        현재 구현:
        - 직접 연결된 엣지는 모두 로컬로 간주
        - 향후: Panorama 이벤트 정보를 활용해 더 정교하게 판단 가능
        
        Args:
            node1_id: 노드 1 ID
            node2_id: 노드 2 ID
            node_attributes: 노드 속성 (선택적)
            
        Returns:
            로컬 연결 여부
        """
        # 간단한 구현: 직접 연결된 엣지는 로컬로 간주
        # 향후 개선: Panorama 이벤트 타입, 타임스탬프 비교
        return True  # 현재는 모든 연결을 로컬로 간주

    def _build_personalization_vector(
        self,
        node_attributes: Optional[Dict[str, MemoryNodeAttributes]],
    ) -> np.ndarray:
        """노드 속성을 이용해 personalization vector v 를 만든다."""
        n = len(self._index_to_id)
        if n == 0:
            return np.zeros(0, dtype=float)

        if node_attributes is None:
            return np.ones(n, dtype=float) / float(n)

        cfg = self.config
        raw = np.zeros(n, dtype=float)

        for idx, nid in enumerate(self._index_to_id):
            attrs = node_attributes.get(nid)
            if attrs is None:
                raw[idx] = 1.0
                continue

            score = (
                cfg.recency_weight * max(attrs.recency, 0.0)
                + cfg.emotion_weight * max(attrs.emotion, 0.0)
                + cfg.frequency_weight * max(attrs.frequency, 0.0)
                + max(attrs.base_importance, 0.0)
            )
            raw[idx] = score if score > 0.0 else 1.0

        total = float(raw.sum())
        if total == 0.0:
            return np.ones(n, dtype=float) / float(n)
        return raw / total

    # ------------------------------------------------------------------
    # 랭크 계산
    # ------------------------------------------------------------------
    def calculate_importance(self) -> Dict[str, float]:
        """PageRank 반복을 통해 메모리 중요도 점수를 계산한다.

        반환:
            {node_id: rank_score} (합 ≈ 1.0)
        """
        if self._M is None or self._v is None:
            raise RuntimeError("Graph is not built. call build_graph() first.")

        n = self._M.shape[0]
        if n == 0:
            return {}

        r = np.ones(n, dtype=float) / float(n)
        alpha = float(self.config.damping)

        for _ in range(self.config.max_iter):
            r_next = alpha * (self._M @ r) + (1.0 - alpha) * self._v
            if np.linalg.norm(r_next - r, 1) < self.config.tol:
                r = r_next
                break
            r = r_next

        r_sum = float(r.sum())
        if r_sum > 0.0:
            r = r / r_sum

        self._r = r
        return {nid: float(score) for nid, score in zip(self._index_to_id, r)}

    def get_top_memories(self, k: int = 10) -> List[Tuple[str, float]]:
        """중요도 상위 k개의 (node_id, score) 리스트를 내림차순으로 반환."""
        if self._r is None:
            self.calculate_importance()

        assert self._r is not None
        n = len(self._r)
        k = max(0, min(k, n))
        if k == 0:
            return []

        idx_sorted = np.argsort(-self._r)[:k]
        return [
            (self._index_to_id[i], float(self._r[i]))
            for i in idx_sorted
        ]

    def get_rank_vector(self) -> Dict[str, float]:
        """마지막으로 계산된 랭크 벡터를 그대로 반환."""
        if self._r is None:
            self.calculate_importance()

        assert self._r is not None
        return {nid: float(score) for nid, score in zip(self._index_to_id, self._r)}

    # ------------------------------------------------------------------
    # 영속성 (Persistence) - 장기 기억의 핵심
    # ------------------------------------------------------------------
    def save_to_json(self, path: str, indent: int = 2) -> Dict[str, int]:
        """그래프와 랭크 벡터를 JSON으로 저장 (장기 기억)
        
        Args:
            path: 저장 경로
            indent: JSON 들여쓰기
            
        Returns:
            {"nodes": 노드 수, "edges": 엣지 수}
        """
        from .persistence import save_to_json as _save
        return _save(self, path, indent)
    
    def load_from_json(self, path: str) -> Dict[str, int]:
        """JSON에서 그래프와 랭크 벡터 로드
        
        Args:
            path: 파일 경로
            
        Returns:
            {"nodes": 노드 수, "edges": 엣지 수}
        """
        from .persistence import load_from_json as _load
        return _load(self, path)
    
    def save_to_npz(self, path: str) -> Dict[str, int]:
        """그래프와 랭크 벡터를 NumPy 압축 파일로 저장
        
        대용량 그래프에 적합 (JSON보다 빠름)
        
        Args:
            path: 저장 경로 (.npz)
            
        Returns:
            {"nodes": 노드 수}
        """
        from .persistence import save_to_npz as _save
        return _save(self, path)
    
    def load_from_npz(self, path: str) -> Dict[str, int]:
        """NumPy 압축 파일에서 그래프와 랭크 벡터 로드
        
        Args:
            path: 파일 경로 (.npz)
            
        Returns:
            {"nodes": 노드 수}
        """
        from .persistence import load_from_npz as _load
        return _load(self, path)
