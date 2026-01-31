from dataclasses import dataclass


@dataclass
class PanoramaConfig:
    """Panorama Memory Engine 설정값.

    - time_gap_threshold: 에피소드 분할 시간 간격 임계값 (초)
    - recency_half_life: 중요도 지수 감쇠 반감기 (초)
    - max_events: 최대 이벤트 수 (메모리 관리용)
    """

    time_gap_threshold: float = 1800.0   # 30분
    recency_half_life: float = 86400.0   # 24시간
    max_events: int = 100000
