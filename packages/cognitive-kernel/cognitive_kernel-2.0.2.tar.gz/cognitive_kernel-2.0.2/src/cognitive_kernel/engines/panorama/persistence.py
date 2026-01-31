"""Panorama Persistence Layer v1.0

영속성 레이어 - 이벤트와 에피소드를 영구 저장합니다.
지원 포맷: JSON, SQLite

이 레이어가 있어야 "장기 기억"이라는 표현이 정확해집니다.
- 프로세스가 종료되어도 기억이 유지됨
- 전원이 꺼져도 복구 가능
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from .panorama_engine import PanoramaMemoryEngine, Event


class PanoramaPersistence:
    """Panorama 엔진의 영속성 관리자
    
    사용 예시:
        >>> engine = PanoramaMemoryEngine()
        >>> engine.append_event(...)
        >>> 
        >>> # 저장
        >>> persistence = PanoramaPersistence(engine)
        >>> persistence.save_json("memory.json")
        >>> 
        >>> # 불러오기
        >>> new_engine = PanoramaMemoryEngine()
        >>> persistence = PanoramaPersistence(new_engine)
        >>> persistence.load_json("memory.json")
    """
    
    def __init__(self, engine: "PanoramaMemoryEngine"):
        self.engine = engine
    
    # ------------------------------------------------------------------
    # JSON 저장/로드
    # ------------------------------------------------------------------
    def save_json(self, path: str, indent: int = 2) -> int:
        """모든 이벤트를 JSON 파일로 저장
        
        Args:
            path: 저장 경로
            indent: JSON 들여쓰기 (None이면 압축)
            
        Returns:
            저장된 이벤트 수
        """
        events_data = []
        for event in self.engine._events:
            events_data.append({
                "id": event.id,
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "payload": event.payload,
                "episode_id": event.episode_id,
                "importance": event.importance,
            })
        
        data = {
            "version": "1.0.0",
            "engine": "PanoramaMemoryEngine",
            "event_count": len(events_data),
            "events": events_data,
        }
        
        Path(path).write_text(json.dumps(data, indent=indent, ensure_ascii=False))
        return len(events_data)
    
    def load_json(self, path: str, clear_existing: bool = True) -> int:
        """JSON 파일에서 이벤트 로드
        
        Args:
            path: 파일 경로
            clear_existing: True면 기존 이벤트 삭제 후 로드
            
        Returns:
            로드된 이벤트 수
        """
        data = json.loads(Path(path).read_text())
        
        if clear_existing:
            self.engine.clear()
        
        events = data.get("events", [])
        for event_data in events:
            self.engine.append_event(
                timestamp=event_data["timestamp"],
                event_type=event_data["event_type"],
                payload=event_data.get("payload", {}),
                episode_id=event_data.get("episode_id"),
                importance=event_data.get("importance", 0.5),
                event_id=event_data["id"],
            )
        
        return len(events)
    
    # ------------------------------------------------------------------
    # SQLite 저장/로드
    # ------------------------------------------------------------------
    def save_sqlite(self, db_path: str) -> int:
        """모든 이벤트를 SQLite DB로 저장
        
        Args:
            db_path: SQLite 파일 경로
            
        Returns:
            저장된 이벤트 수
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS panorama_events (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT,
                episode_id TEXT,
                importance REAL DEFAULT 0.5
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON panorama_events(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_episode ON panorama_events(episode_id)
        """)
        
        # 기존 데이터 삭제 후 삽입
        cursor.execute("DELETE FROM panorama_events")
        
        count = 0
        for event in self.engine._events:
            cursor.execute("""
                INSERT INTO panorama_events (id, timestamp, event_type, payload, episode_id, importance)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.timestamp,
                event.event_type,
                json.dumps(event.payload, ensure_ascii=False),
                event.episode_id,
                event.importance,
            ))
            count += 1
        
        conn.commit()
        conn.close()
        return count
    
    def load_sqlite(self, db_path: str, clear_existing: bool = True) -> int:
        """SQLite DB에서 이벤트 로드
        
        Args:
            db_path: SQLite 파일 경로
            clear_existing: True면 기존 이벤트 삭제 후 로드
            
        Returns:
            로드된 이벤트 수
        """
        if clear_existing:
            self.engine.clear()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, event_type, payload, episode_id, importance
            FROM panorama_events
            ORDER BY timestamp ASC
        """)
        
        count = 0
        for row in cursor.fetchall():
            event_id, timestamp, event_type, payload_str, episode_id, importance = row
            payload = json.loads(payload_str) if payload_str else {}
            
            self.engine.append_event(
                timestamp=timestamp,
                event_type=event_type,
                payload=payload,
                episode_id=episode_id,
                importance=importance or 0.5,
                event_id=event_id,
            )
            count += 1
        
        conn.close()
        return count


# ------------------------------------------------------------------
# 엔진 확장 메서드 (Mixin 스타일)
# ------------------------------------------------------------------
def save_to_json(engine: "PanoramaMemoryEngine", path: str, indent: int = 2) -> int:
    """PanoramaMemoryEngine의 편의 메서드"""
    return PanoramaPersistence(engine).save_json(path, indent)


def load_from_json(engine: "PanoramaMemoryEngine", path: str, clear_existing: bool = True) -> int:
    """PanoramaMemoryEngine의 편의 메서드"""
    return PanoramaPersistence(engine).load_json(path, clear_existing)


def save_to_sqlite(engine: "PanoramaMemoryEngine", path: str) -> int:
    """PanoramaMemoryEngine의 편의 메서드"""
    return PanoramaPersistence(engine).save_sqlite(path)


def load_from_sqlite(engine: "PanoramaMemoryEngine", path: str, clear_existing: bool = True) -> int:
    """PanoramaMemoryEngine의 편의 메서드"""
    return PanoramaPersistence(engine).load_sqlite(path, clear_existing)
