# 🔧 기술 작업 로드맵 (개발 위주)

> **Last Updated**: 2026-01-30  
> **Status**: PyPI 배포 완료, LangChain 통합 완료

---

## ✅ 완료된 작업

- [x] PyPI 패키지 구조 (`src/cognitive_kernel/`)
- [x] `pyproject.toml` + `MANIFEST.in`
- [x] LangChain 통합 예제 (`examples/langchain_memory.py`)
- [x] 7개 엔진 통합 (Panorama, MemoryRank, PFC, BasalGanglia, Amygdala, Hypothalamus, Thalamus)
- [x] 장기 기억 영속성 (JSON/SQLite/NPZ)

---

## 🔴 1순위: Vector DB 연동

**목표**: "Cognitive Kernel = Vector DB 위의 인지 레이어" 포지션 확정

### 작업 목록

| 작업 | 파일 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| **Chroma 연동 예제** | `examples/vector_db_chroma.py` | 중 | 2시간 |
| **FAISS 연동 예제** | `examples/vector_db_faiss.py` | 중 | 2시간 |
| **통합 클래스** | `src/cognitive_kernel/vector_integration.py` | 중 | 3시간 |
| **README 업데이트** | Vector DB 섹션 | 하 | 30분 |

### 구현 구조

```python
# 예상 API
from cognitive_kernel import CognitiveKernel
from cognitive_kernel.vector_integration import VectorDBBackend

# Vector DB를 백엔드로 사용
kernel = CognitiveKernel(
    "my_agent",
    vector_backend=VectorDBBackend("chroma", path="./chroma_db")
)

# Embedding → Vector DB 저장
kernel.remember("event", {"text": "..."}, embed=True)

# Vector 검색 → MemoryRank 재랭킹
memories = kernel.recall(query="user preference", k=5)
```

### 아키텍처

```
[Embedding Model] → [Vector DB (Chroma/FAISS)]  ← 저장
                            ↓
                    [MemoryRank]                  ← 중요도 재정렬
                            ↓
                    [PFC]                         ← 행동/응답 선택
```

### 의존성 추가

```toml
# pyproject.toml
[project.optional-dependencies]
vector = [
    "chromadb>=0.4.0",
    "faiss-cpu>=1.7.4",
    "sentence-transformers>=2.2.0",
]
```

---

## 🟡 2순위: LlamaIndex 통합

**목표**: LangChain 다음으로 큰 LLM 프레임워크 지원

### 작업 목록

| 작업 | 파일 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| **LlamaIndex Memory** | `examples/llamaindex_memory.py` | 중 | 2시간 |
| **README 업데이트** | LlamaIndex 섹션 | 하 | 30분 |

### 구현 구조

```python
from llama_index.core.memory import ChatMemoryBuffer
from cognitive_kernel import CognitiveKernel

class CognitiveKernelMemory(ChatMemoryBuffer):
    """LlamaIndex-compatible memory using Cognitive Kernel."""
    def __init__(self, session_name: str):
        self.kernel = CognitiveKernel(session_name)
        # ... LlamaIndex 인터페이스 구현
```

---

## 🟢 3순위: ADHD/PTSD 시뮬레이션 문서화

**목표**: "단순 기억 저장이 아니라 상태 붕괴/편향을 재현할 수 있다" 증명

### 작업 목록

| 작업 | 파일 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| **COGNITIVE_DYSFUNCTION.md** | `docs/COGNITIVE_DYSFUNCTION.md` | 중 | 3시간 |
| **그래프 시각화** | `examples/dysfunction_visualization.py` | 중 | 2시간 |
| **PTSD 데모** | `examples/ptsd_simulation.py` | 하 | 1시간 |
| **ADHD 데모** | `examples/adhd_simulation.py` | 하 | 1시간 |

### 기존 파일 확인

- ✅ `examples/full_brain_simulation.py` - 이미 PTSD 시뮬레이션 포함
- ✅ `MemoryRank/examples/ptsd_flashback_demo.py` - PTSD 데모 존재

### 작업 내용

1. **문서화**:
   - PTSD 시뮬레이션 메커니즘 설명
   - ADHD 시뮬레이션 메커니즘 설명
   - 수학적 모델 (Rescorla-Wagner, HPA Dynamics 등)
   - 테스트 결과 그래프

2. **시각화**:
   - Stress/Arousal/Decision 궤적 그래프
   - Before/After 비교 (Normal vs PTSD)
   - 시간에 따른 상태 변화 애니메이션

3. **데모 스크립트**:
   - 독립 실행 가능한 PTSD 시뮬레이션
   - 독립 실행 가능한 ADHD 시뮬레이션

---

## 🔵 4순위: 엔진 확장 (후순위)

**⚠️ 주의**: 지금 이걸 먼저 하면 "뭔가 많긴 한데 왜 쓰지?" 상태가 됨

### 작업 목록

| 작업 | 설명 | 난이도 | 예상 시간 |
|------|------|--------|----------|
| **Hippocampus 엔진** | 공간/맥락 기억 | 높음 | 1주 |
| **Cerebellum 엔진** | 시퀀스 최적화 | 높음 | 1주 |

### 구현 계획

**Hippocampus**:
- 공간 기억 (Spatial Memory)
- 맥락 기억 (Contextual Memory)
- 기억 통합 (Memory Consolidation)

**Cerebellum**:
- 시퀀스 학습 (Sequence Learning)
- 모터 제어 (Motor Control)
- 시간 예측 (Temporal Prediction)

---

## 📊 우선순위 요약

```
🔴 1순위: Vector DB 연동 (Chroma/FAISS)
   → 가장 임팩트 큼, 사용자 확보에 직접적

🟡 2순위: LlamaIndex 통합
   → LangChain 다음으로 큰 프레임워크

🟢 3순위: ADHD/PTSD 문서화
   → 연구/학술 포지션 강화

🔵 4순위: 엔진 확장
   → 기능 확장 (후순위)
```

---

## 🎯 추천 시작 작업

**Vector DB 연동 (Chroma)**부터 시작:

1. `examples/vector_db_chroma.py` 작성
2. `src/cognitive_kernel/vector_integration.py` 모듈 생성
3. README에 Vector DB 섹션 추가
4. 테스트 및 커밋

**예상 소요 시간**: 4-5시간

---

**Author**: GNJz (Qquarts)  
**License**: MIT

