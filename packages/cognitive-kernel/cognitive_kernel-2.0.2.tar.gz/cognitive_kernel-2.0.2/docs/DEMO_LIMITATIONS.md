# ⚠️ Demo Limitations - 데모 코드의 한계점

> **정직한 한계점 기록: 원리 증명용 프로토타입의 공학적 한계**

## 🎯 핵심 문제

### 데모 코드의 위반 사항

**v2.0.1 엔진룸과의 1:1 정합성 위반:**
- `kernel.decide()`를 우회하고 직접 softmax 계산
- 내부 메서드 `_calculate_memory_relevance` 직접 호출
- PFC 내부의 $\beta$를 사용하지 않고 외부에서 softmax 재구현

**하드코딩 금지 규약 위반:**
- 물리 상수들이 하드코딩됨
- CONFIG 딕셔너리 미사용

**세션 격리 문제:**
- Persistence 오염 (기억이 남아서 재현성 저하)
- 독립된 임시 세션 미생성

---

## 📋 구체적 문제점

### 1. 결정 경로 통합 위반

**문제:**
```python
# ❌ 잘못된 방식
utilities = np.array(utilities)
exp_utils = np.exp(beta * (utilities - np.max(utilities)))
probabilities = exp_utils / np.sum(exp_utils)
```

**올바른 방식:**
- `kernel.decide()`를 사용해야 함
- PFC 내부의 $\beta$가 실제로 확률을 계산하게 해야 함

---

### 2. 내부 메서드 직접 호출

**문제:**
```python
# ❌ 잘못된 방식
opt_keywords = kernel._extract_keywords(opt)
memory_relevance = kernel._calculate_memory_relevance(opt_keywords, memories)
```

**올바른 방식:**
- 공개 API만 사용
- `kernel.recall()`과 `kernel.decide()`를 통해서만 데이터 흐름

---

### 3. 세션 오염

**문제:**
```python
# ❌ 잘못된 방식
kernel = CognitiveKernel("precession_demo", mode=CognitiveMode.ASD)
```

**올바른 방식:**
- uuid나 timestamp를 사용해 실행 시마다 독립된 임시 세션 생성
- `auto_load=False`로 설정하여 기존 세션 로드 방지

---

### 4. 하드코딩된 상수

**문제:**
```python
# ❌ 잘못된 방식
alpha = 0.5
beta = 5.0
gamma = 0.3
omega = 0.05
```

**올바른 방식:**
- CONFIG 딕셔너리로 파라미터화
- 모든 물리 상수를 설정 가능하게

---

## 🔧 수정 방향

### 1. 결정 경로 통합 (1:1 정합)

**필요한 인터페이스 확장:**
```python
def decide(
    self,
    options: List[str],
    context: Optional[str] = None,
    use_habit: bool = True,
    external_torque: Optional[Dict[str, float]] = None,  # NEW
) -> Dict[str, Any]:
```

**토크 주입:**
- `external_torque`: 옵션별 토크 값 ($\gamma T_n(k)$)
- Utility 계산 시 반영: $U_{n,k} = U_0 + \alpha C_n(k) + \gamma T_n(k)$

---

### 2. 세션 격리 (재현성 확보)

**필요한 수정:**
```python
import uuid
session_name = f"precession_demo_{uuid.uuid4().hex[:8]}"
kernel = CognitiveKernel(session_name, mode=CognitiveMode.ASD, auto_load=False)
```

**또는:**
```python
import time
session_name = f"precession_demo_{int(time.time())}"
```

---

### 3. 공개 API 전환

**필요한 수정:**
- `kernel.recall(k=3)` 사용
- `kernel.decide(options, ...)` 사용
- 내부 메서드 직접 호출 금지

---

### 4. 규약 준수 (No Hard-coding)

**필요한 수정:**
```python
CONFIG = {
    "alpha": 0.5,      # 기억 영향 계수
    "beta": 5.0,       # 결정 축 고정 (ASD)
    "gamma": 0.3,      # 회전 토크 (ADHD)
    "omega": 0.05,     # 세차 속도
    "n_steps": 100,    # 시뮬레이션 스텝
}
```

---

## 📊 현재 상태

### 데모 코드 분류

| 데모 | 상태 | 문제점 |
|------|------|--------|
| `precession_demo.py` | ⚠️ 프로토타입 | 위반 사항 7가지 |
| `stability_core_demo.py` | ⚠️ 프로토타입 | 위반 사항 7가지 |
| `cognitive_polarity_demo.py` | ✅ 규약 준수 | 정상 |

---

## ✅ 수정 완료 사항

### v2.0.1 규약 준수 데모 (`precession_demo_v2.py`)

**수정 완료:**
1. ✅ `kernel.decide()` 인터페이스 확장 (토크 주입)
2. ✅ 세션 격리 구현 (uuid 기반)
3. ✅ 공개 API만 사용 (`kernel.decide()` 직접 사용)
4. ✅ CONFIG로 파라미터화

**남은 한계점:**
- `decide()`는 단일 선택의 확률만 반환
- 전체 확률 분포를 얻기 위해 각 옵션에 대해 `decide()` 호출 필요
- 실제로는 PFC 내부에서 전체 분포를 계산하지만, 공개 API로는 접근 불가

**향후 개선:**
- `decide()` 반환값에 전체 확률 분포 추가 고려
- 또는 `get_probability_distribution()` 같은 별도 메서드 추가

---

## 🎯 결론

**v2.0.1 규약 준수 데모:**
- ✅ `kernel.decide()` 직접 사용 (1:1 정합성)
- ✅ 세션 격리 (uuid 기반)
- ✅ 공개 API만 사용
- ✅ CONFIG로 파라미터화
- ⚠️ 전체 확률 분포 접근 제한 (API 한계)

---

## 🔗 관련 문서

- [MINIMAL_DYNAMICS_MODEL.md](./MINIMAL_DYNAMICS_MODEL.md) - 최소 차분 모델
- [PHYSICAL_DYNAMICS.md](./PHYSICAL_DYNAMICS.md) - 물리적 동역학

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.1  
**Last Updated**: 2026-01-30

