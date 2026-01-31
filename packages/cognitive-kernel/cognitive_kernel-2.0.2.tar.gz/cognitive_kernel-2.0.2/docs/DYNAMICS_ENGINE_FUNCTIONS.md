# Dynamics Engine 기능 명세서

> **Dynamics Engine이 정확히 무엇을 하는지 상세 설명**

**작성일**: 2026-01-31  
**버전**: v2.0.2

---

## 🎯 핵심 기능 요약

**Dynamics Engine은 "인지 상태의 동역학을 계산하는 엔진"입니다.**

즉, **"생각이 어떻게 변하는가"**를 수학적으로 계산합니다.

---

## 📊 주요 기능 5가지

### 1. 엔트로피 계산 (calculate_entropy)

**기능:**
- 확률 분포의 "퍼짐 정도"를 계산
- 선택의 불확실성을 수치화

**수식:**
```
E = -Σ P(k) ln P(k)
```

**입력:**
- `probabilities`: 확률 분포 리스트 (예: [0.3, 0.4, 0.3])

**출력:**
- `entropy`: 엔트로피 값 (0 ~ ln(N))

**의미:**
- 엔트로피가 높음 = 선택이 불확실함 (ADHD 특성)
- 엔트로피가 낮음 = 선택이 확정적임 (ASD 특성)

**예시:**
```python
dynamics = DynamicsEngine()
entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
# 결과: 약 1.089 (중간 정도의 불확실성)
```

---

### 2. 코어 강도 계산 (calculate_core_strength)

**기능:**
- 기억의 "중력"을 계산
- 엔트로피를 다시 모이게 하는 힘을 측정
- Core Decay (중력 붕괴) 동역학 적용
- 시간축 분리 (오래된 기억 vs 새 기억)

**수식:**
```
원시 코어: C_raw = α * (Σ importance) / N
Core Decay: C(t) = C(0) * exp(-λ * Δt)
오래된 기억 감쇠: importance *= exp(-λ_old * age)
새 기억 감쇠: importance *= exp(-λ_new * age)
```

**입력:**
- `memories`: 기억 리스트 (각 기억은 importance, timestamp 포함)
- `memory_update_failure`: 새 기억 중요도 반영 실패율 (0~1)
- `alpha`: 기억 영향 계수 (기본 0.5)

**출력:**
- `core_strength`: 코어 강도 (0~1)

**의미:**
- 코어 강도가 높음 = 기억이 강함, 엔트로피를 수렴시킬 수 있음
- 코어 강도가 낮음 = 기억이 약함, 엔트로피가 퍼짐 (치매/알츠하이머)

**특수 기능:**
- **Core Decay**: 시간에 따라 코어 강도가 감쇠 (치매/알츠하이머)
- **시간축 분리**: 오래된 기억과 새 기억에 다른 감쇠율 적용

**예시:**
```python
memories = [
    {"importance": 0.9, "timestamp": time.time() - 7200},  # 2시간 전
    {"importance": 0.9, "timestamp": time.time() - 300},   # 5분 전
]
core = dynamics.calculate_core_strength(memories)
# 치매: 오래된 기억 감쇠, 새 기억 정상
# 알츠하이머: 새 기억 즉시 감쇠
```

---

### 3. 회전 토크 생성 (generate_torque)

**기능:**
- 엔트로피에 기반한 자동 회전 토크 생성
- 선택 분포를 회전시켜 탐색을 유도
- 세차운동 (precession) 구현

**수식:**
```
정규화된 엔트로피: E_norm = E / E_max
토크 세기: T = γ * E_norm
회전 토크: T(k) = T * cos(φ - ψ_k)
위상 업데이트: φ(t+1) = φ(t) + ω
```

**입력:**
- `options`: 옵션 리스트 (예: ["rest", "work", "exercise"])
- `entropy`: 현재 엔트로피
- `mode`: 인지 모드 ("adhd", "asd", "normal" 또는 CognitiveMode 객체)
- `base_gamma`: 기본 회전 토크 세기 (기본 0.3)
- `omega`: 세차 속도 (기본 0.05)

**출력:**
- `torque`: 옵션별 회전 토크 딕셔너리

**의미:**
- 토크가 양수 = 해당 옵션을 선택하도록 유도
- 토크가 음수 = 해당 옵션을 피하도록 유도
- ADHD 모드: 더 강한 회전 (γ * 1.5)
- ASD 모드: 약한 회전 (γ * 0.5)

**예시:**
```python
entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
torque = dynamics.generate_torque(
    ["rest", "work", "exercise"],
    entropy,
    mode="adhd"  # 또는 CognitiveMode.ADHD
)
# 결과: {"rest": 0.15, "work": -0.10, "exercise": 0.05}
```

---

### 4. 인지적 절규 확인 (check_cognitive_distress)

**기능:**
- 엔트로피가 높은데 코어 강도가 낮은 상태 감지
- "기억이 안 나..." 상태를 감지

**조건:**
```
엔트로피 > 임계값 (최대치의 80%)
AND
코어 강도 < 임계값 (0.3)
```

**입력:**
- `entropy`: 현재 엔트로피
- `core_strength`: 현재 코어 강도
- `num_options`: 옵션 수

**출력:**
- `(is_distress, message)`: (True/False, 메시지)

**의미:**
- True = 인지적 절규 상태 (기억이 안 나는 상태)
- False = 정상 상태

**예시:**
```python
is_distress, message = dynamics.check_cognitive_distress(
    entropy=1.5,
    core_strength=0.2,
    num_options=3
)
# 결과: (True, "기억이 안 나...")
```

---

### 5. 히스토리 관리 (update_history)

**기능:**
- 엔트로피와 코어 강도의 시간 변화 추적
- 최근 N개 값만 유지 (기본 100개)

**입력:**
- `entropy`: 현재 엔트로피
- `core_strength`: 현재 코어 강도

**출력:**
- 없음 (내부 상태 업데이트)

**의미:**
- 시간에 따른 변화 추적
- 추세 분석 가능

**예시:**
```python
dynamics.update_history(entropy=1.2, core_strength=0.5)
# state.entropy_history와 state.core_strength_history에 추가
```

---

## 🔄 상태 관리

### DynamicsState

**포함 상태:**
- `entropy`: 현재 엔트로피
- `core_strength`: 현재 코어 강도
- `precession_phi`: 세차 위상 (0 ~ 2π)
- `persistent_core`: 지속 코어 강도 (Core Decay용)
- `last_decay_time`: 마지막 감쇠 시간
- `cognitive_distress`: 인지적 절규 상태
- `entropy_history`: 엔트로피 히스토리
- `core_strength_history`: 코어 강도 히스토리

---

## 🎯 실제 사용 예시

### 기본 사용

```python
from dynamics_engine import DynamicsEngine, DynamicsConfig

# 1. 엔진 생성
config = DynamicsConfig(
    base_gamma=0.3,
    omega=0.05,
    core_decay_rate=0.001,  # 치매 모드
    new_memory_decay_rate=0.1,  # 알츠하이머 모드
)
dynamics = DynamicsEngine(config)

# 2. 엔트로피 계산
probabilities = [0.3, 0.4, 0.3]
entropy = dynamics.calculate_entropy(probabilities)

# 3. 코어 강도 계산
memories = [
    {"importance": 0.9, "timestamp": time.time() - 3600},
    {"importance": 0.8, "timestamp": time.time() - 300},
]
core = dynamics.calculate_core_strength(memories)

# 4. 회전 토크 생성
options = ["rest", "work", "exercise"]
torque = dynamics.generate_torque(options, entropy, mode="adhd")

# 5. 인지적 절규 확인
is_distress, message = dynamics.check_cognitive_distress(
    entropy, core, len(options)
)
```

---

## 🔗 Cognitive Kernel과의 관계

### Cognitive Kernel에서의 역할

**Dynamics Engine은:**
- Cognitive Kernel의 **동역학 계산 엔진**
- `decide()` 메서드에서 사용됨
- 엔트로피 기반 자동 회전 토크 생성
- Core Decay를 통한 치매/알츠하이머 모델링

**하지만:**
- ✅ **독립적으로도 사용 가능**
- ✅ Cognitive Kernel 없이도 작동
- ✅ 다른 프로젝트에서 재사용 가능

---

## 📈 핵심 가치

### 1. 엔트로피 기반 동역학

**"생각의 불확실성"을 수치화하고, 그것을 기반으로 동작을 결정**

### 2. Core Decay 모델링

**"기억의 중력이 붕괴되는 과정"을 물리적으로 모델링**

### 3. 시간축 분리

**"오래된 기억 vs 새 기억"의 다른 감쇠율로 치매/알츠하이머 구분**

### 4. 세차운동 (Precession)

**"선택 분포가 느리게 회전하는 현상"을 구현**

---

## 🎯 요약

**Dynamics Engine은:**
1. ✅ **엔트로피 계산**: 선택의 불확실성 측정
2. ✅ **코어 강도 계산**: 기억의 중력 측정 (Core Decay 포함)
3. ✅ **회전 토크 생성**: 엔트로피 기반 자동 회전
4. ✅ **인지적 절규 감지**: 기억 상실 상태 감지
5. ✅ **히스토리 관리**: 시간 변화 추적

**핵심:**
- "생각이 어떻게 변하는가"를 수학적으로 계산
- 치매/알츠하이머를 "중력 붕괴"로 모델링
- 100% 독립 배포 가능 (표준 라이브러리만 사용)

---

**작성자**: GNJz (Qquarts)  
**작성일**: 2026-01-31

