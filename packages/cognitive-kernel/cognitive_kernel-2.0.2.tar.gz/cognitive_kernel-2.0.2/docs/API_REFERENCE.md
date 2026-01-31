# 📚 API Reference

> **🇰🇷 한국어** | [🇺🇸 English](#english-version)

## CognitiveKernel

### 생성자

```python
CognitiveKernel(
    session_name: str = "default",
    config: Optional[CognitiveConfig] = None,
    auto_load: bool = True
)
```

| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `session_name` | str | "default" | 세션 이름 (저장 파일 이름) |
| `config` | CognitiveConfig | None | 설정 객체 |
| `auto_load` | bool | True | 기존 세션 자동 로드 |

---

### 메서드

#### `remember()`

기억 저장 (장기 기억)

```python
kernel.remember(
    event_type: str,
    content: Optional[Dict[str, Any]] = None,
    importance: float = 0.5,
    emotion: float = 0.0,
    related_to: Optional[List[str]] = None
) -> str
```

| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `event_type` | str | - | 이벤트 종류 |
| `content` | Dict | None | 이벤트 내용 |
| `importance` | float | 0.5 | 중요도 (0~1) |
| `emotion` | float | 0.0 | 감정 강도 (0~1) |
| `related_to` | List[str] | None | 연관 기억 ID |

**반환값:** 생성된 기억 ID (str)

---

#### `recall()`

중요한 기억 회상 (PageRank 기반)

```python
kernel.recall(k: int = 5) -> List[Dict[str, Any]]
```

| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `k` | int | 5 | 회상할 기억 수 |

**반환값:** 중요도 순 기억 리스트

```python
[
    {
        "id": "uuid",
        "event_type": "meeting",
        "content": {"topic": "project"},
        "importance": 0.35,
        "timestamp": 1234567890.0
    },
    ...
]
```

---

#### `decide()`

의사결정 (Softmax)

```python
kernel.decide(
    options: List[str],
    context: Optional[str] = None,
    use_habit: bool = True
) -> Dict[str, Any]
```

| 매개변수 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `options` | List[str] | - | 행동 후보 |
| `context` | str | None | 상황 컨텍스트 |
| `use_habit` | bool | True | 습관 학습 반영 |

**반환값:**

```python
{
    "action": "rest",           # 선택된 행동
    "utility": 0.25,            # 효용값
    "probability": 0.35,        # 선택 확률
    "habit_suggestion": "work", # 습관 제안
    "conflict": True            # 갈등 여부
}
```

---

#### `save()` / `load()`

수동 저장/로드

```python
kernel.save() -> Dict[str, int]
kernel.load() -> Dict[str, int]
```

**반환값:** 저장/로드 통계

```python
{"events": 10, "nodes": 10, "edges": 20}
```

---

#### `status()`

현재 상태 조회

```python
kernel.status() -> Dict[str, Any]
```

**반환값:**

```python
{
    "session_name": "my_brain",
    "storage_path": ".cognitive_kernel/my_brain",
    "event_count": 10,
    "edge_count": 20,
    "is_dirty": False,
    "auto_save": True
}
```

---

## CognitiveConfig

```python
@dataclass
class CognitiveConfig:
    storage_dir: str = ".cognitive_kernel"     # 저장 경로
    auto_save: bool = True                     # 자동 저장
    auto_save_interval: int = 100              # n개 이벤트마다 저장
    working_memory_capacity: int = 7           # Miller's Law
    recency_half_life: float = 3600.0          # 시간 감쇠 반감기 (초)
    damping: float = 0.85                      # PageRank 감쇠 계수
```

---

## 하위 엔진 직접 사용

### MemoryRankEngine

```python
from memoryrank import MemoryRankEngine, MemoryNodeAttributes

engine = MemoryRankEngine()

# 그래프 구축
edges = [("A", "B", 1.0), ("B", "C", 0.5)]
attrs = {"A": MemoryNodeAttributes(recency=1.0, emotion=0.8)}
engine.build_graph(edges, attrs)

# 중요도 계산
ranks = engine.calculate_importance()

# Top-k 조회
top = engine.get_top_memories(k=5)

# 저장/로드
engine.save_to_json("graph.json")
engine.load_from_json("graph.json")
```

### PanoramaMemoryEngine

```python
from panorama import PanoramaMemoryEngine

engine = PanoramaMemoryEngine()

# 이벤트 추가
event_id = engine.append_event(
    timestamp=time.time(),
    event_type="action",
    payload={"data": "value"},
    importance=0.8
)

# 시간 구간 쿼리
events = engine.query_range(t_start, t_end)

# 에피소드 분할
episodes = engine.segment_episodes(method="time_gap")

# 저장/로드
engine.save_to_json("memory.json")
engine.save_to_sqlite("memory.db")
```

---

---

# English Version

> [🇰🇷 한국어](#-api-reference) | **🇺🇸 English**

## CognitiveKernel

### Constructor

```python
CognitiveKernel(
    session_name: str = "default",
    config: Optional[CognitiveConfig] = None,
    auto_load: bool = True
)
```

### Methods

#### `remember()` - Store memory (long-term)
#### `recall()` - Recall important memories (PageRank-based)
#### `decide()` - Decision making (Softmax)
#### `save()` / `load()` - Manual save/load
#### `status()` - Get current status

See Korean version for detailed parameter descriptions.
