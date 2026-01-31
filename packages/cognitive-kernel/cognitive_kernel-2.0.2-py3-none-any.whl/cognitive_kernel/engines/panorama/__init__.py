"""Panorama Memory Engine Package

시간축 기반 에피소드 기억 엔진.
- 이벤트 기록 및 시간 구간 쿼리
- 에피소드 자동 분할
- 지수 감쇠 기반 중요도 계산
- 영속성 레이어 (JSON, SQLite)

🔗 장기 기억 지원:
    save_to_json() / load_from_json()
    save_to_sqlite() / load_from_sqlite()
"""

from .config import PanoramaConfig
from .panorama_engine import PanoramaMemoryEngine, Event, Episode
from .persistence import PanoramaPersistence

__all__ = [
    "PanoramaConfig",
    "PanoramaMemoryEngine",
    "Event",
    "Episode",
    "PanoramaPersistence",
]

__version__ = "1.1.0"
