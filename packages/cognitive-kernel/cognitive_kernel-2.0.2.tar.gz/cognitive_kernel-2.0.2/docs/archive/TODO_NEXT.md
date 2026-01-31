# 🎯 다음 작업 우선순위 (2026-01-30)

## ✅ 완료된 것

- [x] PyPI 배포 (`pip install cognitive-kernel`)
- [x] GitHub 릴리즈 v2.0.0
- [x] LangChain 통합 예제 (`examples/langchain_memory.py`)
- [x] README 업데이트 (LangChain 섹션 추가)

---

## 🔴 1순위: 확산 (이번 주)

### 📢 홍보 (즉시 실행 가능)

**목표**: "사람들이 발견하고 써보게 만들기"

| 작업 | 예상 시간 | 임팩트 |
|------|----------|--------|
| **Twitter/X 포스트** | 10분 | ⭐⭐⭐⭐⭐ |
| **Reddit r/Python** | 15분 | ⭐⭐⭐⭐ |
| **Reddit r/LocalLLaMA** | 15분 | ⭐⭐⭐⭐ |
| **Hacker News "Show HN"** | 15분 | ⭐⭐⭐⭐⭐ |

**홍보 문구 (복사용)**:
```
🧠 Built a persistent memory system for AI agents.

pip install cognitive-kernel

Your LLM agent forgets everything on restart?
Not anymore. 3 lines of code:

with CognitiveKernel("my_agent") as memory:
    memory.remember("preference", {"likes": "coffee"})
    # Next day → still remembers!

✅ Persistence (survives restart)
✅ PageRank importance ranking  
✅ Time decay (Ebbinghaus curve)

GitHub: github.com/qquartsco-svg/Cognitive_Kernel
PyPI: pypi.org/project/cognitive-kernel/
```

**실행 방법**:
1. Twitter/X: 위 문구 + 스크린샷 (Before/After 비교)
2. Reddit: 제목 "Show HN: Persistent memory for LLM agents (pip install cognitive-kernel)"
3. HN: "Show HN" 섹션에 동일 내용

---

## 🟡 2순위: 기술 확장 (다음 주)

### 🔗 Vector DB 연동

**목표**: "Cognitive Kernel = Vector DB 위의 인지 레이어" 포지션 확정

| 작업 | 설명 | 난이도 |
|------|------|--------|
| **Chroma 연동** | `examples/vector_db_chroma.py` | 중 |
| **FAISS 연동** | `examples/vector_db_faiss.py` | 중 |
| **README 업데이트** | Vector DB 섹션 추가 | 하 |

**구조**:
```
[Embedding / Vector DB]  ← 저장
        ↓
[MemoryRank]            ← 중요도 재정렬
        ↓
[PFC]                   ← 행동/응답 선택
```

**효과**:
- "대체재"가 아니라 "보완재" 포지션
- 기존 스택에 끼워 넣기 쉬워짐

---

## 🟢 3순위: 연구/차별화 (그 다음)

### 🧠 ADHD/PTSD 시뮬레이션 문서화

**목표**: "이건 단순 기억 저장이 아니라 상태 붕괴/편향을 재현할 수 있다"

| 작업 | 설명 | 난이도 |
|------|------|--------|
| **COGNITIVE_DYSFUNCTION.md** | 시뮬레이션 문서 | 중 |
| **그래프 시각화** | Stress/Arousal/Decision 궤적 | 중 |
| **데모 스크립트** | `examples/ptsd_simulation.py` | 하 |

**효과**:
- 연구·학술·헬스테크 쪽에서 반응 시작
- "단순 라이브러리"가 아닌 "연구 플랫폼" 포지션

---

## ⚙️ 4순위: 엔진 확장 (후순위)

**⚠️ 주의**: 지금 이걸 먼저 하면 "뭔가 많긴 한데 왜 쓰지?" 상태가 됨

| 작업 | 설명 |
|------|------|
| Hippocampus (공간/맥락) | 엔진 확장 |
| Cerebellum (시퀀스 최적화) | 엔진 확장 |

---

## 📊 현재 상태 요약

```
✅ 완료: PyPI 배포, LangChain 통합
🔴 다음: 홍보 (Twitter/Reddit/HN)
🟡 그 다음: Vector DB 연동
🟢 나중: ADHD/PTSD 문서화
```

---

## 🎯 추천 액션 (오늘/내일)

1. **Twitter/X 포스트** (10분)
2. **Reddit r/Python** (15분)
3. **Hacker News "Show HN"** (15분)

**이 세 개만 해도 관심도가 10배 이상 달라집니다.**

---

**Author**: GNJz (Qquarts)  
**Last Updated**: 2026-01-30

