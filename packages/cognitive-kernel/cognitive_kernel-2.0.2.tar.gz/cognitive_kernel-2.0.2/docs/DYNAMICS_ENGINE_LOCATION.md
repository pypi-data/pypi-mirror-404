# 📁 Dynamics Engine 폴더 위치

> **Dynamics Engine이 어디에 있는지, 어떻게 구성되어 있는지**

**작성일**: 2026-01-31  
**버전**: v2.0.1+

---

## 📍 위치

### 절대 경로
```
/Users/jazzin/Desktop/00_BRAIN/Cognitive_Kernel/src/cognitive_kernel/engines/dynamics/
```

### 상대 경로 (프로젝트 루트 기준)
```
src/cognitive_kernel/engines/dynamics/
```

---

## 📂 폴더 구조

### Dynamics Engine은 단독 폴더가 아닙니다

**Dynamics Engine은 `engines/` 폴더 안에 있는 다른 엔진들과 같은 레벨에 있습니다.**

```
src/cognitive_kernel/engines/
├── __init__.py                    # 엔진 통합 임포트
├── interfaces.py                  # 엔진 인터페이스
│
├── panorama/                     # 시간축 기억 (Episodic Memory)
│   ├── __init__.py
│   ├── config.py
│   └── panorama_engine.py
│
├── memoryrank/                   # 중요도 랭킹 (PageRank)
│   ├── __init__.py
│   ├── config.py
│   └── memoryrank_engine.py
│
├── pfc/                          # 의사결정 (Prefrontal Cortex)
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   └── pfc_engine.py
│
├── basal_ganglia/                # 습관 학습 (Q-Learning)
│   ├── __init__.py
│   ├── config.py
│   └── basal_ganglia_engine.py
│
├── amygdala/                     # 감정/공포 (Rescorla-Wagner)
│   ├── __init__.py
│   ├── config.py
│   └── amygdala_engine.py
│
├── hypothalamus/                 # 에너지/스트레스 (HPA Dynamics)
│   ├── __init__.py
│   ├── config.py
│   └── hypothalamus_engine.py
│
├── thalamus/                     # 감각 게이팅 (Salience Filtering)
│   ├── __init__.py
│   ├── config.py
│   └── thalamus_engine.py
│
└── dynamics/                      # 동역학 엔진 ⭐ 새로 추가됨
    ├── __init__.py
    ├── config.py                  # DynamicsConfig
    ├── models.py                  # DynamicsState
    └── dynamics_engine.py         # DynamicsEngine
```

---

## 🔗 속해있는 구조

### 1. Cognitive Kernel 프로젝트 구조

```
Cognitive_Kernel/
├── src/
│   └── cognitive_kernel/
│       ├── __init__.py
│       ├── core.py                # CognitiveKernel (통합 레이어)
│       ├── cognitive_modes.py
│       ├── pipeline.py
│       └── engines/                # ← 여기에 속해있음
│           ├── __init__.py
│           ├── panorama/
│           ├── memoryrank/
│           ├── pfc/
│           ├── basal_ganglia/
│           ├── amygdala/
│           ├── hypothalamus/
│           ├── thalamus/
│           └── dynamics/          # ← Dynamics Engine
│
├── docs/
├── tests/
└── ...
```

### 2. 엔진 통합

**`engines/__init__.py`에서 모든 엔진을 통합합니다:**

```python
from .panorama import PanoramaMemoryEngine, PanoramaConfig
from .memoryrank import MemoryRankEngine, MemoryRankConfig
from .pfc import PFCEngine, PFCConfig
from .basal_ganglia import BasalGangliaEngine, BasalGangliaConfig
from .dynamics import DynamicsEngine, DynamicsConfig, DynamicsState  # ← 추가됨
```

---

## 📦 Dynamics Engine 파일 구조

```
dynamics/
├── __init__.py                    # 공개 API
│   └── DynamicsEngine, DynamicsConfig, DynamicsState
│
├── config.py                      # DynamicsConfig 클래스
│   └── 동역학 엔진 설정 (gamma, omega, core_decay_rate 등)
│
├── models.py                      # DynamicsState 클래스
│   └── 동역학 상태 (entropy, core_strength, precession_phi 등)
│
└── dynamics_engine.py             # DynamicsEngine 클래스
    └── 동역학 계산 로직 (엔트로피, 코어 강도, 회전 토크 등)
```

---

## 🎯 사용 방법

### 1. Cognitive Kernel에서 사용 (통합)

```python
from cognitive_kernel import CognitiveKernel

kernel = CognitiveKernel('my_brain')
# kernel.dynamics는 자동으로 초기화됨
```

### 2. 독립적으로 사용 (Edge AI)

```python
from cognitive_kernel.engines.dynamics import DynamicsEngine, DynamicsConfig

# 독립 사용
dynamics = DynamicsEngine(DynamicsConfig(core_decay_rate=0.01))
entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
```

### 3. engines 패키지에서 임포트

```python
from cognitive_kernel.engines import DynamicsEngine, DynamicsConfig

# engines 패키지 통합 임포트
dynamics = DynamicsEngine(DynamicsConfig())
```

---

## 📊 요약

### 위치
- **경로**: `src/cognitive_kernel/engines/dynamics/`
- **속성**: `engines/` 폴더 안에 있는 다른 엔진들과 같은 레벨
- **단독 폴더**: ❌ (다른 엔진들과 함께 `engines/` 안에 있음)

### 구조
- **상위**: `engines/` (모든 엔진의 통합 폴더)
- **동급**: panorama, memoryrank, pfc, basal_ganglia, amygdala, hypothalamus, thalamus
- **하위**: config.py, models.py, dynamics_engine.py, __init__.py

### 특징
- ✅ 다른 엔진들과 동일한 구조
- ✅ 독립적으로 사용 가능 (Edge AI)
- ✅ Cognitive Kernel에 통합됨

---

**마지막 업데이트**: 2026-01-31

