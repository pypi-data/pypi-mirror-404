# 🏗️ Cognitive Kernel 아키텍처 구조

## 📁 폴더 구조

### 독립 엔진 (Standalone Engines)

루트 레벨에 있는 독립 실행 가능한 엔진들:

```
Cognitive_Kernel/
├── Amygdala/          # 독립 엔진 (감정/위협)
├── BasalGanglia/      # 독립 엔진 (습관 학습)
├── Hypothalamus/      # 독립 엔진 (에너지/스트레스)
├── MemoryRank/        # 독립 엔진 (중요도 랭킹)
├── Panorama/          # 독립 엔진 (시간축 기억)
├── PFC/               # 독립 엔진 (의사결정)
└── Thalamus/          # 독립 엔진 (입력 필터링)
```

**특징:**
- 각각 독립적으로 사용 가능
- 자체 테스트, 문서, 블록체인 서명 포함
- PyPI에 개별 배포 가능

---

### 통합 모듈 (Integrated Module)

`src/cognitive_kernel/` 아래에 있는 통합 패키지:

```
src/cognitive_kernel/
├── __init__.py
├── core.py                    # CognitiveKernel 통합 클래스
├── cognitive_modes.py         # 모드 정의 (ADHD/ASD/PTSD/NORMAL)
├── vector_integration.py      # Vector DB 통합
├── llamaindex_memory.py       # LlamaIndex 통합
└── engines/                   # 엔진 통합 버전
    ├── amygdala/
    ├── basal_ganglia/
    ├── hypothalamus/
    ├── memoryrank/
    ├── panorama/
    ├── pfc/
    └── thalamus/
```

**특징:**
- 모든 엔진을 통합한 고수준 인터페이스
- `CognitiveKernel` 클래스로 단일 API 제공
- 모드 기반 파라미터 조정

---

## 🔄 ASD의 위치

### ❌ ASD는 독립 엔진이 아닙니다

**ASD 관련 폴더:**
- ❌ `ASD/` 폴더 없음
- ❌ 독립 엔진 없음

**ASD의 실제 위치:**
- ✅ `src/cognitive_kernel/cognitive_modes.py`에 모드로 정의
- ✅ `CognitiveMode.ASD` enum 값
- ✅ `CognitiveModePresets.asd()` 메서드로 파라미터 설정

---

## 🧠 Cognitive Modes 구조

### 모드 정의

```python
# src/cognitive_kernel/cognitive_modes.py

class CognitiveMode(Enum):
    NORMAL = "normal"
    ADHD = "adhd"    # 고엔트로피: 과도한 탐색
    ASD = "asd"      # 저엔트로피: 과도한 착취
    PTSD = "ptsd"    # 트라우마 고착
```

### 모드 동작 방식

ASD는 **독립 엔진이 아니라**, 기존 엔진들의 **파라미터 조합**입니다:

```python
# ASD 모드 = 여러 엔진의 파라미터 조정

ModeConfig(
    # Thalamus 파라미터
    gate_threshold=0.0,      # 모든 입력 통과
    
    # PFC 파라미터
    decision_temperature=5.0, # 결정론적 (β↑)
    
    # BasalGanglia 파라미터
    tau=0.1,                 # 착취 강화
    
    # MemoryRank 파라미터
    local_weight_boost=3.0,  # 개념적 (미구현)
    
    # ...
)
```

---

## 📊 구조 비교

| 항목 | 독립 엔진 (예: MemoryRank) | 모드 (예: ASD) |
|------|---------------------------|----------------|
| **위치** | 루트 레벨 폴더 | `cognitive_modes.py` |
| **독립성** | ✅ 독립 실행 가능 | ❌ 파라미터 조합 |
| **설치** | `pip install memoryrank` | Cognitive Kernel 내장 |
| **사용** | `from memoryrank import ...` | `CognitiveMode.ASD` |
| **테스트** | 자체 테스트 폴더 | 통합 테스트 |
| **문서** | 자체 README | `COGNITIVE_STATES.md` |

---

## 🔍 실제 사용 예시

### 독립 엔진 사용

```python
# MemoryRank를 독립적으로 사용
from memoryrank import MemoryRankEngine

engine = MemoryRankEngine()
# ...
```

### 통합 모듈 사용 (ASD 모드)

```python
# Cognitive Kernel에서 ASD 모드 사용
from cognitive_kernel import CognitiveKernel, CognitiveMode

kernel = CognitiveKernel("asd_demo", mode=CognitiveMode.ASD)
# 내부적으로 모든 엔진이 ASD 파라미터로 초기화됨
```

---

## 🎯 핵심 정리

1. **ASD는 독립 엔진이 아님**
   - `ASD/` 폴더 없음
   - `cognitive_modes.py`에 모드로만 정의

2. **ASD는 파라미터 조합**
   - 기존 7개 엔진의 파라미터를 조정
   - 새로운 알고리즘을 추가하는 것이 아님

3. **독립 엔진 vs 통합 모듈**
   - 독립 엔진: 루트 레벨, 개별 사용 가능
   - 통합 모듈: `src/cognitive_kernel/`, 모든 엔진 통합

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.0  
**Last Updated**: 2026-01-30

