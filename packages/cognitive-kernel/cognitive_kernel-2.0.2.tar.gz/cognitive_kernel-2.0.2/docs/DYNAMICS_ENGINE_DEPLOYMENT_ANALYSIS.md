# 🔍 Dynamics Engine 독립 배포 가능성 분석

> **Dynamics Engine을 독립 모듈로 배포할 수 있는지 분석**

**작성일**: 2026-01-31  
**버전**: v2.0.1+

---

## 📊 현재 상태 분석

### 1. 파일 구조

```
engines/dynamics/
├── __init__.py          # 공개 API
├── config.py            # DynamicsConfig (의존성 없음)
├── models.py            # DynamicsState (의존성 없음)
└── dynamics_engine.py   # DynamicsEngine (일부 의존성)
```

---

## 🔗 의존성 분석

### ✅ 독립적인 파일

1. **`config.py`**
   - 의존성: 없음 (표준 라이브러리만 사용)
   - 배포 가능성: ✅ 완전 독립

2. **`models.py`**
   - 의존성: 없음 (표준 라이브러리만 사용)
   - 배포 가능성: ✅ 완전 독립

3. **`__init__.py`**
   - 의존성: 내부 모듈만 임포트
   - 배포 가능성: ✅ 완전 독립

---

### ⚠️ 의존성이 있는 파일

**`dynamics_engine.py`**

**의존성:**
1. **표준 라이브러리**: `math`, `time` ✅
2. **내부 모듈**: `config`, `models` ✅
3. **외부 의존성**: `CognitiveMode` ⚠️

**위치**: `generate_torque()` 메서드 내부

```python
# dynamics_engine.py (161 라인)
from ...cognitive_modes import CognitiveMode
if mode == CognitiveMode.ADHD:
    gamma = base_gamma * 1.5
elif mode == CognitiveMode.ASD:
    gamma = base_gamma * 0.5
```

---

## 🎯 독립 배포 가능성 판정

### 현재 상태: **부분 독립 (90%)**

**독립 가능한 부분:**
- ✅ `calculate_entropy()` - 완전 독립
- ✅ `calculate_core_strength()` - 완전 독립
- ✅ `check_cognitive_distress()` - 완전 독립
- ✅ `update_history()` - 완전 독립

**의존성 있는 부분:**
- ⚠️ `generate_torque()` - `CognitiveMode` 의존

---

## 🔧 독립 배포를 위한 개선 방안

### 옵션 1: CognitiveMode 의존성 제거 (권장)

**방법:**
- `mode` 파라미터를 `str` 또는 `Enum`으로 변경
- 또는 `mode`를 선택적 파라미터로 만들고 기본값 사용

**예시:**
```python
def generate_torque(
    self,
    options: List[str],
    entropy: float,
    mode: Optional[Union[str, Any]] = None,  # CognitiveMode 대신
    base_gamma: Optional[float] = None,
    omega: Optional[float] = None,
) -> Dict[str, float]:
    # mode가 문자열이면 처리
    if isinstance(mode, str):
        if mode == "adhd":
            gamma = base_gamma * 1.5
        elif mode == "asd":
            gamma = base_gamma * 0.5
        else:
            gamma = base_gamma
    # ...
```

### 옵션 2: CognitiveMode를 선택적 의존성으로

**방법:**
- `CognitiveMode`를 try-except로 감싸기
- 없으면 기본값 사용

**예시:**
```python
try:
    from ...cognitive_modes import CognitiveMode
    COGNITIVE_MODE_AVAILABLE = True
except ImportError:
    COGNITIVE_MODE_AVAILABLE = False

def generate_torque(...):
    if COGNITIVE_MODE_AVAILABLE and isinstance(mode, CognitiveMode):
        # 기존 로직
    else:
        # 기본 로직
```

---

## 📦 독립 배포 구조 제안

### 최소 배포 패키지

```
dynamics_engine/
├── __init__.py
├── config.py
├── models.py
├── dynamics_engine.py
└── README.md
```

### setup.py 예시

```python
from setuptools import setup, find_packages

setup(
    name="dynamics-engine",
    version="1.0.0",
    description="Cognitive Dynamics Engine - Entropy, Core Strength, Torque",
    packages=find_packages(),
    install_requires=[],  # 표준 라이브러리만 사용
    python_requires=">=3.8",
)
```

---

## ✅ 결론

### 현재 상태

**독립 배포 가능성: 90%**

**장점:**
- ✅ 대부분의 기능이 완전 독립
- ✅ 표준 라이브러리만 사용
- ✅ 설정과 상태가 캡슐화됨

**개선 필요:**
- ⚠️ `generate_torque()`의 `CognitiveMode` 의존성 제거

### 권장 사항

**즉시 배포 가능:**
- `generate_torque()`를 제외한 모든 기능
- 또는 `mode` 파라미터를 문자열로 변경

**완전 독립 배포:**
- `CognitiveMode` 의존성 제거 (5분 작업)
- 완료 후 100% 독립 배포 가능

---

**마지막 업데이트**: 2026-01-31

