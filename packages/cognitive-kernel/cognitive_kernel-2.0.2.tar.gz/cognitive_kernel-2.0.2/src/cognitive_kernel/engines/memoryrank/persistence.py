"""MemoryRank Persistence Layer v1.0

영속성 레이어 - 기억 그래프와 랭크 벡터를 영구 저장합니다.
지원 포맷: JSON, NumPy (.npz)

이 레이어가 있어야 "장기 기억"이라는 표현이 정확해집니다.
- 학습된 기억 중요도가 영구 보존됨
- 그래프 구조가 프로세스 종료 후에도 유지됨
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional, Any

import numpy as np

if TYPE_CHECKING:
    from .memoryrank_engine import MemoryRankEngine, MemoryNodeAttributes


class MemoryRankPersistence:
    """MemoryRank 엔진의 영속성 관리자
    
    사용 예시:
        >>> engine = MemoryRankEngine()
        >>> engine.build_graph(edges, attributes)
        >>> engine.calculate_importance()
        >>> 
        >>> # 저장
        >>> persistence = MemoryRankPersistence(engine)
        >>> persistence.save_json("memory_graph.json")
        >>> 
        >>> # 불러오기
        >>> new_engine = MemoryRankEngine()
        >>> persistence = MemoryRankPersistence(new_engine)
        >>> persistence.load_json("memory_graph.json")
    """
    
    def __init__(self, engine: "MemoryRankEngine"):
        self.engine = engine
    
    # ------------------------------------------------------------------
    # JSON 저장/로드 (이식성 우선)
    # ------------------------------------------------------------------
    def save_json(self, path: str, indent: int = 2) -> Dict[str, int]:
        """그래프와 랭크 벡터를 JSON으로 저장
        
        Args:
            path: 저장 경로
            indent: JSON 들여쓰기
            
        Returns:
            {"nodes": 노드 수, "edges": 엣지 수}
        """
        engine = self.engine
        
        # 노드 목록
        nodes = list(engine._index_to_id)
        
        # 전이 행렬에서 엣지 추출
        edges = []
        if engine._M is not None:
            n = engine._M.shape[0]
            for j in range(n):  # src
                for i in range(n):  # dst
                    weight = engine._M[i, j]
                    if weight > 0:
                        edges.append({
                            "src": engine._index_to_id[j],
                            "dst": engine._index_to_id[i],
                            "weight": float(weight),
                        })
        
        # personalization vector
        personalization = None
        if engine._v is not None:
            personalization = {
                nid: float(engine._v[i])
                for i, nid in enumerate(engine._index_to_id)
            }
        
        # rank vector
        ranks = None
        if engine._r is not None:
            ranks = {
                nid: float(engine._r[i])
                for i, nid in enumerate(engine._index_to_id)
            }
        
        data = {
            "version": "1.0.0",
            "engine": "MemoryRankEngine",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "personalization": personalization,
            "ranks": ranks,
        }
        
        Path(path).write_text(json.dumps(data, indent=indent, ensure_ascii=False))
        return {"nodes": len(nodes), "edges": len(edges)}
    
    def load_json(self, path: str) -> Dict[str, int]:
        """JSON에서 그래프와 랭크 벡터 로드
        
        Args:
            path: 파일 경로
            
        Returns:
            {"nodes": 노드 수, "edges": 엣지 수}
        """
        data = json.loads(Path(path).read_text())
        engine = self.engine
        
        nodes = data.get("nodes", [])
        edges_data = data.get("edges", [])
        personalization = data.get("personalization")
        ranks = data.get("ranks")
        
        n = len(nodes)
        
        # 노드 매핑 복원
        engine._index_to_id = list(nodes)
        engine._id_to_index = {nid: i for i, nid in enumerate(nodes)}
        
        # 전이 행렬 복원
        if n > 0:
            engine._M = np.zeros((n, n), dtype=float)
            for edge in edges_data:
                src, dst, w = edge["src"], edge["dst"], edge["weight"]
                if src in engine._id_to_index and dst in engine._id_to_index:
                    j = engine._id_to_index[src]
                    i = engine._id_to_index[dst]
                    engine._M[i, j] = w
        else:
            engine._M = None
        
        # personalization vector 복원
        if personalization and n > 0:
            engine._v = np.zeros(n, dtype=float)
            for nid, val in personalization.items():
                if nid in engine._id_to_index:
                    engine._v[engine._id_to_index[nid]] = val
        else:
            engine._v = np.ones(n, dtype=float) / n if n > 0 else None
        
        # rank vector 복원
        if ranks and n > 0:
            engine._r = np.zeros(n, dtype=float)
            for nid, val in ranks.items():
                if nid in engine._id_to_index:
                    engine._r[engine._id_to_index[nid]] = val
        else:
            engine._r = None
        
        return {"nodes": n, "edges": len(edges_data)}
    
    # ------------------------------------------------------------------
    # NumPy 저장/로드 (성능 우선)
    # ------------------------------------------------------------------
    def save_npz(self, path: str) -> Dict[str, int]:
        """그래프와 랭크 벡터를 NumPy 압축 파일로 저장
        
        대용량 그래프에 적합 (JSON보다 빠름)
        
        Args:
            path: 저장 경로 (.npz)
            
        Returns:
            {"nodes": 노드 수}
        """
        engine = self.engine
        
        # 노드 목록을 JSON 문자열로
        nodes_json = json.dumps(engine._index_to_id, ensure_ascii=False)
        
        save_dict = {
            "nodes_json": np.array([nodes_json]),
        }
        
        if engine._M is not None:
            save_dict["M"] = engine._M
        if engine._v is not None:
            save_dict["v"] = engine._v
        if engine._r is not None:
            save_dict["r"] = engine._r
        
        np.savez_compressed(path, **save_dict)
        return {"nodes": len(engine._index_to_id)}
    
    def load_npz(self, path: str) -> Dict[str, int]:
        """NumPy 압축 파일에서 그래프와 랭크 벡터 로드
        
        Args:
            path: 파일 경로 (.npz)
            
        Returns:
            {"nodes": 노드 수}
        """
        engine = self.engine
        data = np.load(path, allow_pickle=False)
        
        # 노드 목록 복원
        nodes_json = str(data["nodes_json"][0])
        nodes = json.loads(nodes_json)
        
        engine._index_to_id = nodes
        engine._id_to_index = {nid: i for i, nid in enumerate(nodes)}
        
        # 행렬/벡터 복원
        engine._M = data["M"] if "M" in data else None
        engine._v = data["v"] if "v" in data else None
        engine._r = data["r"] if "r" in data else None
        
        return {"nodes": len(nodes)}


# ------------------------------------------------------------------
# 엔진 확장 메서드 (Mixin 스타일)
# ------------------------------------------------------------------
def save_to_json(engine: "MemoryRankEngine", path: str, indent: int = 2) -> Dict[str, int]:
    """MemoryRankEngine의 편의 메서드"""
    return MemoryRankPersistence(engine).save_json(path, indent)


def load_from_json(engine: "MemoryRankEngine", path: str) -> Dict[str, int]:
    """MemoryRankEngine의 편의 메서드"""
    return MemoryRankPersistence(engine).load_json(path)


def save_to_npz(engine: "MemoryRankEngine", path: str) -> Dict[str, int]:
    """MemoryRankEngine의 편의 메서드"""
    return MemoryRankPersistence(engine).save_npz(path)


def load_from_npz(engine: "MemoryRankEngine", path: str) -> Dict[str, int]:
    """MemoryRankEngine의 편의 메서드"""
    return MemoryRankPersistence(engine).load_npz(path)
