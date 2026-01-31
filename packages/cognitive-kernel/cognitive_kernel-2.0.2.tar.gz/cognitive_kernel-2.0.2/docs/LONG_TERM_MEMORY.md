# 💾 Long-term Memory Technical Documentation

> **🇰🇷 한국어** | [🇺🇸 English](#english-version)

## 장기 기억이란?

### 컴퓨터 공학적 정의

**영속성(Persistence)**:
- 프로세스 종료 후에도 데이터가 유지됨
- 전원이 꺼져도 복구 가능
- 다른 세션에서 접근 가능

### 기존 방식의 문제점

```python
# 기존 방식: 인메모리만
memories = []
memories.append({"event": "meeting"})
# 프로세스 종료 → 데이터 소멸!
```

### Cognitive Kernel의 해결책

```python
# Cognitive Kernel: 자동 영속성
with CognitiveKernel("my_brain") as kernel:
    kernel.remember("meeting", {"topic": "project"})
# 프로세스 종료 → 자동 저장 → 다음 세션에서 복구!
```

---

## 아키텍처

### 계층 구조

```
┌─────────────────────────────────────────┐
│         CognitiveKernel (통합 API)       │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │Panorama │  │MemoryRank│  │  PFC   │  │
│  │(시간축) │  │(중요도)  │  │(결정)  │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  │
├───────┼────────────┼────────────┼───────┤
│       │   Persistence Layer      │       │
│       └────────────┼─────────────┘       │
├─────────────────────────────────────────┤
│              File System                 │
│   (JSON / SQLite / NumPy NPZ)           │
└─────────────────────────────────────────┘
```

### 저장 포맷

| 모듈 | 파일 | 포맷 | 용도 |
|------|------|------|------|
| Panorama | `panorama.json` | JSON | 시간축 이벤트 |
| MemoryRank | `memoryrank.json` | JSON | 그래프 + 랭크 |
| MemoryRank | `*.npz` | NumPy | 대용량 그래프 |
| Panorama | `*.db` | SQLite | 대용량 이벤트 |
| BasalGanglia | `q_values.json` | JSON | Q-Learning 테이블 |
| Meta | `meta.json` | JSON | 세션 정보 |

---

## 핵심 수식

### 1. 시간 감쇠 (Panorama)

**Ebbinghaus 망각 곡선 기반 지수 감쇠**:

$$
S(t) = S_0 \cdot e^{-\lambda \cdot \Delta t}
$$

여기서:
- $S_0$: 초기 중요도
- $\Delta t$: 경과 시간
- $\lambda = \frac{\ln 2}{t_{1/2}}$: 감쇠율
- $t_{1/2}$: 반감기 (기본값: 3600초)

**코드 구현:**

```python
# Panorama/package/panorama/panorama_engine.py
half_life = self.config.recency_half_life
lambda_decay = math.log(2) / half_life if half_life > 0 else 0.0

for event in self._events:
    delta_t = max(0.0, t_now - event.timestamp)
    decay = math.exp(-lambda_decay * delta_t)
    scores[event.id] = event.importance * decay
```

### 2. 기억 중요도 (MemoryRank)

**Personalized PageRank**:

$$
\mathbf{r}^{(t+1)} = \alpha \cdot M \cdot \mathbf{r}^{(t)} + (1-\alpha) \cdot \mathbf{v}
$$

여기서:
- $M_{ij} = \frac{W_{ij}}{\sum_k W_{kj}}$ (열 정규화 전이 행렬)
- $\mathbf{v}_i = w_r \cdot \text{recency}_i + w_e \cdot \text{emotion}_i + w_f \cdot \text{frequency}_i$

**코드 구현:**

```python
# MemoryRank/package/memoryrank/memoryrank_engine.py
r = np.ones(n, dtype=float) / float(n)
alpha = float(self.config.damping)

for _ in range(self.config.max_iter):
    r_next = alpha * (self._M @ r) + (1.0 - alpha) * self._v
    if np.linalg.norm(r_next - r, 1) < self.config.tol:
        r = r_next
        break
    r = r_next
```

---

## API 사용법

### 기본 사용

```python
from cognitive_kernel import CognitiveKernel

# 세션 생성 (자동 로드)
kernel = CognitiveKernel("my_brain")

# 기억 저장
event_id = kernel.remember(
    event_type="meeting",
    content={"topic": "project", "participants": ["Alice", "Bob"]},
    importance=0.9,
    emotion=0.5,
    related_to=["previous_meeting_id"]
)

# 기억 회상 (PageRank 기반)
memories = kernel.recall(k=5)

# 의사결정
result = kernel.decide(
    options=["rest", "work", "exercise"],
    context="tired_after_work"
)

# 수동 저장
kernel.save()
```

### 컨텍스트 매니저 (권장)

```python
with CognitiveKernel("my_brain") as kernel:
    kernel.remember("idea", {"content": "great idea"})
    # ... 작업 ...
# 자동 저장됨
```

### 설정

```python
from cognitive_kernel import CognitiveKernel, CognitiveConfig

config = CognitiveConfig(
    storage_dir=".my_memories",      # 저장 경로
    auto_save=True,                  # 자동 저장
    auto_save_interval=100,          # n개 이벤트마다 저장
    working_memory_capacity=7,       # Miller's Law
    recency_half_life=3600.0,        # 시간 감쇠 반감기
    damping=0.85,                    # PageRank 감쇠
)

kernel = CognitiveKernel("my_brain", config)
```

---

## 테스트 검증

### 증명 테스트

```python
# 세션 A: 기억 저장
with CognitiveKernel("proof_session") as kernel:
    kernel.remember("first_memory", {"content": "데이터"}, importance=0.9)
    print(f"저장된 이벤트: {len(kernel.panorama)}개")
# 프로세스 종료

# 세션 B: 기억 복구 (새 프로세스)
kernel2 = CognitiveKernel("proof_session")
print(f"복구된 이벤트: {len(kernel2.panorama)}개")  # 동일함!
```

### 파일 검증

```bash
ls -la .cognitive_kernel/proof_session/
# edges.json, memoryrank.json, meta.json, panorama.json, q_values.json

cat .cognitive_kernel/proof_session/panorama.json
# {"events": [{"id": "...", "event_type": "first_memory", ...}]}
```

---

## 활용 가치

### 1. AI 에이전트

```python
class MyAgent:
    def __init__(self):
        self.brain = CognitiveKernel("agent_memory")
    
    def process_message(self, message):
        # 중요한 대화 기억
        self.brain.remember("conversation", {"message": message})
        
        # 관련 기억 회상
        context = self.brain.recall(k=3)
        
        # 의사결정
        action = self.brain.decide(["respond", "ask", "ignore"])
        return action
```

### 2. RAG 강화

```python
def enhanced_rag(query, documents):
    kernel = CognitiveKernel("rag_memory")
    
    # 검색 결과를 기억으로 저장
    for doc in documents:
        kernel.remember("search_result", {"doc": doc}, importance=doc.score)
    
    # PageRank로 재랭킹
    ranked_memories = kernel.recall(k=5)
    
    return [m["content"]["doc"] for m in ranked_memories]
```

### 3. 게임 NPC

```python
class NPC:
    def __init__(self):
        self.memory = CognitiveKernel(f"npc_{self.id}")
    
    def interact(self, player, event):
        # 플레이어와의 상호작용 기억
        self.memory.remember(
            "interaction",
            {"player": player.id, "event": event},
            emotion=event.emotional_intensity
        )
        
        # 과거 기억 기반 반응
        memories = self.memory.recall(k=3)
        return self.generate_response(memories)
```

---

---

# English Version

> [🇰🇷 한국어](#-long-term-memory-technical-documentation) | **🇺🇸 English**

## What is Long-term Memory?

### Computer Science Definition

**Persistence**:
- Data survives process termination
- Recoverable after power off
- Accessible from different sessions

### Problem with Existing Approaches

```python
# Existing: In-memory only
memories = []
memories.append({"event": "meeting"})
# Process terminates → Data lost!
```

### Cognitive Kernel Solution

```python
# Cognitive Kernel: Auto-persistence
with CognitiveKernel("my_brain") as kernel:
    kernel.remember("meeting", {"topic": "project"})
# Process terminates → Auto-saved → Recovered in next session!
```

---

## Architecture

### Layer Structure

```
┌─────────────────────────────────────────┐
│         CognitiveKernel (Unified API)    │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │Panorama │  │MemoryRank│  │  PFC   │  │
│  │(Timeline)│ │(Importance)│ │(Decision)│ │
│  └────┬────┘  └────┬────┘  └────┬────┘  │
├───────┼────────────┼────────────┼───────┤
│       │   Persistence Layer      │       │
│       └────────────┼─────────────┘       │
├─────────────────────────────────────────┤
│              File System                 │
│   (JSON / SQLite / NumPy NPZ)           │
└─────────────────────────────────────────┘
```

---

## Core Formulas

### 1. Temporal Decay (Panorama)

**Exponential decay based on Ebbinghaus forgetting curve**:

$$
S(t) = S_0 \cdot e^{-\lambda \cdot \Delta t}
$$

Where:
- $S_0$: Initial importance
- $\Delta t$: Elapsed time
- $\lambda = \frac{\ln 2}{t_{1/2}}$: Decay rate
- $t_{1/2}$: Half-life (default: 3600 seconds)

### 2. Memory Importance (MemoryRank)

**Personalized PageRank**:

$$
\mathbf{r}^{(t+1)} = \alpha \cdot M \cdot \mathbf{r}^{(t)} + (1-\alpha) \cdot \mathbf{v}
$$

Where:
- $M_{ij} = \frac{W_{ij}}{\sum_k W_{kj}}$ (column-normalized transition matrix)
- $\mathbf{v}_i = w_r \cdot \text{recency}_i + w_e \cdot \text{emotion}_i + w_f \cdot \text{frequency}_i$

---

## Use Cases

### 1. AI Agent Memory
### 2. RAG Enhancement
### 3. Game NPC Behavior

See Korean version above for detailed code examples.

---

## References

- Page, L., et al. (1999). The PageRank Citation Ranking: Bringing Order to the Web.
- Ebbinghaus, H. (1885). Über das Gedächtnis.
- Miller, G. A. (1956). The magical number seven, plus or minus two.
