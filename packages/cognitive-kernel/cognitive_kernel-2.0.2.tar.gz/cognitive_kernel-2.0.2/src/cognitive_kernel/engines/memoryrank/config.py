from dataclasses import dataclass


@dataclass
class MemoryRankConfig:
    """MemoryRank 엔진 설정값.

    - damping: Google PageRank 감쇠 계수 α (0~1)
    - max_iter: 최대 반복 횟수
    - tol: 수렴 판단 기준 (L1 norm)
    - recency_weight / emotion_weight / frequency_weight:
      personalization 벡터를 만들 때 각 feature에 곱해지는 가중치
    - local_weight_boost: 로컬 연결 가중치 부스트 (1.0 = 부스트 없음, >1.0 = 로컬 연결 강화)
    """

    damping: float = 0.85
    max_iter: int = 100
    tol: float = 1e-6

    recency_weight: float = 1.0
    emotion_weight: float = 1.0
    frequency_weight: float = 1.0
    
    local_weight_boost: float = 1.0  # 로컬 연결 가중치 부스트
