"""
🔗 Vector DB Integration for Cognitive Kernel

Vector DB (Chroma/FAISS)를 백엔드로 사용하여 의미 기억(Semantic Memory)을 저장하고,
Cognitive Kernel의 MemoryRank로 중요도 재랭킹하는 통합 모듈.

구조:
    [Embedding Model] → [Vector DB] → [MemoryRank] → [PFC]

Author: GNJz (Qquarts)
Version: 2.0.0
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False


class VectorDBBackend:
    """
    Vector DB 백엔드 추상 클래스
    
    Cognitive Kernel의 remember() 메서드에서 텍스트를 embedding하여
    Vector DB에 저장하고, recall()에서 semantic search를 수행합니다.
    """
    
    def __init__(self, backend_type: str = "chroma", **kwargs):
        """
        Args:
            backend_type: "chroma" or "faiss"
            **kwargs: 백엔드별 설정
        """
        self.backend_type = backend_type
        self.embedding_model = None
        self._init_backend(**kwargs)
    
    def _init_backend(self, **kwargs):
        """백엔드 초기화"""
        if self.backend_type == "chroma":
            if not CHROMA_AVAILABLE:
                raise ImportError("chromadb not installed. pip install chromadb")
            self._init_chroma(**kwargs)
        elif self.backend_type == "faiss":
            if not FAISS_AVAILABLE:
                raise ImportError("faiss-cpu not installed. pip install faiss-cpu")
            self._init_faiss(**kwargs)
        else:
            raise ValueError(f"Unknown backend: {self.backend_type}")
        
        # Embedding 모델 초기화
        if EMBEDDING_AVAILABLE:
            model_name = kwargs.get("embedding_model", "all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)
        else:
            raise ImportError("sentence-transformers not installed. pip install sentence-transformers")
    
    def _init_chroma(self, path: str = "./chroma_db", collection_name: str = "cognitive_memory"):
        """Chroma DB 초기화"""
        self.client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Cognitive Kernel semantic memory"}
        )
        self.path = path
    
    def _init_faiss(self, dimension: int = 384, path: str = "./faiss_index"):
        """FAISS 인덱스 초기화"""
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.ids = []  # ID 리스트
        self.metadata = []  # 메타데이터 리스트
        self.path = path
    
    def embed(self, text: str) -> List[float]:
        """텍스트를 embedding 벡터로 변환"""
        if self.embedding_model is None:
            raise RuntimeError("Embedding model not initialized")
        return self.embedding_model.encode(text).tolist()
    
    def add_memory(
        self,
        memory_id: str,
        text: str,
        metadata: Dict[str, Any],
        importance: float = 0.5
    ) -> None:
        """기억을 Vector DB에 추가"""
        embedding = self.embed(text)
        
        if self.backend_type == "chroma":
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    **metadata,
                    "importance": importance,
                    "text": text
                }]
            )
        elif self.backend_type == "faiss":
            # FAISS는 numpy array 필요
            embedding_array = np.array([embedding], dtype=np.float32)
            self.index.add(embedding_array)
            self.ids.append(memory_id)
            self.metadata.append({
                **metadata,
                "importance": importance,
                "text": text
            })
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search 수행
        
        Returns:
            List of {id, text, metadata, distance, importance}
        """
        query_embedding = self.embed(query)
        
        if self.backend_type == "chroma":
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_metadata
            )
            
            memories = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    memories.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None,
                        "importance": results["metadatas"][0][i].get("importance", 0.5)
                    })
            return memories
        
        elif self.backend_type == "faiss":
            query_array = np.array([query_embedding], dtype=np.float32)
            distances, indices = self.index.search(query_array, k)
            
            memories = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.ids):
                    memories.append({
                        "id": self.ids[idx],
                        "text": self.metadata[idx].get("text", ""),
                        "metadata": self.metadata[idx],
                        "distance": float(dist),
                        "importance": self.metadata[idx].get("importance", 0.5)
                    })
            return memories
    
    def save(self, path: Optional[Path] = None):
        """Vector DB 상태 저장 (FAISS만 필요)"""
        if self.backend_type == "faiss":
            if path is None:
                path = Path(self.path)
            path.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(path / "index.faiss"))
            
            # 메타데이터 저장
            with open(path / "metadata.json", "w") as f:
                json.dump({
                    "ids": self.ids,
                    "metadata": self.metadata,
                    "dimension": self.dimension
                }, f, ensure_ascii=False, indent=2)
    
    def load(self, path: Optional[Path] = None):
        """Vector DB 상태 로드 (FAISS만 필요)"""
        if self.backend_type == "faiss":
            if path is None:
                path = Path(self.path)
            
            # 인덱스 로드
            self.index = faiss.read_index(str(path / "index.faiss"))
            
            # 메타데이터 로드
            with open(path / "metadata.json", "r") as f:
                data = json.load(f)
                self.ids = data["ids"]
                self.metadata = data["metadata"]
                self.dimension = data["dimension"]

