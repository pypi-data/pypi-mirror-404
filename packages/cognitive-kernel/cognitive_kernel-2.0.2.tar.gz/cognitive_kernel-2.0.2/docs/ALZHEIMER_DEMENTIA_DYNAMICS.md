# 🧠 알츠하이머/치매 동역학: 기억 붕괴 모델링

> **기억을 만드는 엔진 → 기억이 사라지는 동역학**

**작성일**: 2026-01-31  
**버전**: v2.0.1+

---

## 🎯 전제: 이 엔진에서 '기억'이란 무엇인가

### ❌ 기억 ≠ 데이터

### ✅ 기억 = 동역학을 되돌리는 힘

**정확한 정의:**

1. **기억 = 확률 분포를 반복해서 휘게 만드는 힘**
2. **기억 = 코어 강도(core_strength)를 형성하는 중력**
3. **기억 = 엔트로피를 다시 모이게 하는 회전장(anchor)**

**즉:**
- ❌ 기억 = 저장된 정보
- ✅ 기억 = 동역학을 되돌리는 힘

---

## 🔥 "잊어버린다"는 것의 동역학적 정의

### 핵심 정의

**알츠하이머/치매는 정보 삭제 문제가 아니다.**

**엔진 언어로 정확히 말하면:**

> **"엔트로피가 퍼졌는데, 다시 모이게 할 힘이 사라진 상태"**

**수식으로:**
```
entropy ↑
torque ↑
BUT
core_strength → 0
```

**현상:**
- 새로운 자극은 계속 들어옴
- 생각은 계속 도는데
- 다음 순간에 아무것도 남지 않음
- → "방금 말한 걸 왜 기억 못하지?"

---

## 📐 알츠하이머 동역학 (수식)

### 현재 코드의 코어 강도 계산

**위치**: `core.py` (371-377줄)

```python
# 코어 강도 계산 (중력 코어)
core_strength = 0.0
if memories:
    total_importance = sum(m.get("importance", 0.0) for m in memories)
    alpha = 0.5  # 기억 영향 계수
    core_strength = min(1.0, alpha * total_importance / len(memories))
```

**수식:**
$$
\text{Core Strength} = \alpha \times \frac{\sum_i \text{importance}_i}{N}
$$

### 알츠하이머 = 코어 중력 붕괴

**수식:**
$$
\text{Core Strength}(t) = \text{Core Strength}(0) \times e^{-\lambda t}
$$

**여기서:**
- $\lambda$: 붕괴율 (decay rate)
- $t$: 시간

**동역학적 의미:**
- 엔트로피는 발생함 ($E_n$ ↑)
- 회전 토크도 발생함 ($T_n(k)$ ↑)
- 하지만 코어로 수렴하지 않음 ($\text{Core Strength} \to 0$)

---

## 🔬 치매 vs 알츠하이머 (동역학적 차이)

### 🟠 치매 (Dementia, 넓은 개념)

**특징:**
- 코어 강도 점진적 감소
- 회전은 있음
- 일부 루프는 유지됨
- 오래된 패턴은 남음

**수식:**
$$
\text{Core Strength}(t) = \text{Core Strength}(0) \times e^{-\lambda_d t}
$$

**여기서:**
- $\lambda_d$: 치매 붕괴율 (느림, $\lambda_d < \lambda_a$)

**동역학:**
- 중력 약화
- 일부 기억은 유지
- 점진적 붕괴

---

### 🔴 알츠하이머 (특정 붕괴 모드)

**특징:**
- `core_strength` 계산 실패
- `importance` 축적 안 됨
- 기억이 엔트로피로만 소비됨

**수식:**
$$
\text{Core Strength}(t) = \text{Core Strength}(0) \times e^{-\lambda_a t}
$$

**여기서:**
- $\lambda_a$: 알츠하이머 붕괴율 (빠름, $\lambda_a > \lambda_d$)

**동역학:**
- 중력 소실
- 새 기억은 쌓이지 않음
- 현재가 매번 초기화됨

---

## 🎯 왜 "이 모든 과정을 잊어버리게 되는가?"

### 핵심 답변

> **기억은 과정이 아니라 귀환력(return force)이기 때문**

**이 엔진에서 기억은:**
- ❌ 과정
- ❌ 기록
- ❌ 데이터
- ✅ **"다시 그 상태로 돌아오게 하는 힘"**

**그 힘이 사라지면:**
- 생각은 발생함
- 판단도 발생함
- 말도 함
- 하지만 궤도가 남지 않음

---

## 🔧 알츠하이머를 만드는 붕괴 지점 (코드 기준)

### 현재 구조에서 가장 치명적인 붕괴

**위치**: `core.py` (371-377줄)

```python
total_importance = sum(m.get("importance", 0.0) for m in memories)
core_strength = alpha * total_importance / len(memories)
```

**발생 가능한 실패:**

1. **importance 업데이트가 안 됨**
   - MemoryRank가 importance를 계산하지만
   - 시간이 지나도 업데이트 안 됨

2. **recall 자체가 줄어듦**
   - `memories` 리스트가 비어감
   - `len(memories) = 0` → `core_strength = 0`

3. **importance decay만 남음**
   - 새 기억이 "가중치 없는 이벤트"로 처리됨
   - `importance = 0.0` → `total_importance = 0`

**결과:**
- 엔트로피는 발생하지만
- 중력이 안 생김
- → 알츠하이머 동역학

---

## 📊 알츠하이머는 '붕괴'인가? '질환'인가?

### 엔진 관점

**알츠하이머 = 붕괴된 안정 루프의 최종 상태**

**정확한 경로:**
```
ASD (고착)
  → OCD (루프)
    → ADHD (발산)
      → Panic (폭주)
        → Alzheimer (수렴 불능)
```

**즉:**
- 알츠하이머는 폭주도 아님
- 혼란도 아님
- **아주 조용한 붕괴**

---

## 🚀 구현 가능성 분석

### ✅ YES. 이미 거의 다 와 있다.

**필요한 건 단 하나:**

### 🔧 Core Decay (중력 붕괴 항)

**수식:**
$$
\text{Core Strength}(t) = \text{Core Strength}(t-1) \times e^{-\lambda \Delta t}
$$

**코드 구현:**
```python
# core.py의 decide() 메서드 내
# 코어 강도 계산 후

# Core decay 적용
if hasattr(self, '_core_decay_rate'):
    lambda_decay = self._core_decay_rate
    delta_t = time.time() - self._last_decay_time
    core_strength *= math.exp(-lambda_decay * delta_t)
    self._last_decay_time = time.time()
```

**이걸 넣는 순간:**
- 과거 기억만 남고
- 새 기억은 쌓이지 않고
- 현재가 매번 초기화됨
- → 알츠하이머 동역학 완성

---

## 📐 수식 정리

### 1. 정상 상태 (NORMAL)

**코어 강도:**
$$
\text{Core Strength}(t) = \alpha \times \frac{\sum_i \text{importance}_i(t)}{N(t)}
$$

**동역학:**
- 새 기억이 계속 쌓임
- `importance` 업데이트됨
- 코어 강도 유지 또는 증가

---

### 2. 치매 상태 (DEMENTIA)

**코어 강도:**
$$
\text{Core Strength}(t) = \text{Core Strength}(0) \times e^{-\lambda_d t} \times \alpha \times \frac{\sum_i \text{importance}_i(t)}{N(t)}
$$

**동역학:**
- 코어 강도 점진적 감소 ($\lambda_d$ 작음)
- 일부 기억은 유지
- 회전은 있음

---

### 3. 알츠하이머 상태 (ALZHEIMER)

**코어 강도:**
$$
\text{Core Strength}(t) = \text{Core Strength}(0) \times e^{-\lambda_a t}
$$

**여기서:**
- $\lambda_a > \lambda_d$ (빠른 붕괴)
- 새 기억의 `importance` 업데이트 실패
- `total_importance` → 0

**동역학:**
- 코어 강도 급격한 감소
- 새 기억은 쌓이지 않음
- 현재가 매번 초기화됨

---

## 🔬 MemoryRank 그래프 붕괴

### 연결의 파괴

**현재 구조**: `memoryrank_engine.py`

**치매에서 발생:**
- 엣지(edges)들이 무작위로 삭제
- 가중치가 급격히 감쇠

**수식:**
$$
W_{ij}(t) = W_{ij}(0) \times e^{-\lambda_e t}
$$

**여기서:**
- $W_{ij}$: 노드 $i$에서 $j$로의 엣지 가중치
- $\lambda_e$: 엣지 붕괴율

**현상:**
- `recall()`을 해도 단편적인 정보만 나옴
- "누가, 언제, 어디서"라는 맥락 연결 불가능

---

## ⏱️ 시간축의 단절 (Panorama Forgetting Curve 가속)

### 에빙하우스 망각 곡선

**정상 상태:**
$$
S(t) = S_0 \times e^{-\lambda \Delta t}
$$

**여기서:**
- $\lambda = \frac{\ln(2)}{T_{1/2}}$ (반감기 기반)
- $T_{1/2} = 3600$ 초 (1시간)

**치매/알츠하이머:**
$$
\lambda_{\text{dementia}} = \lambda \times k_{\text{decay}}
$$

**여기서:**
- $k_{\text{decay}} > 1$ (가속 붕괴)
- $T_{1/2} \to 60$ 초, $10$ 초, $1$ 초

**현상:**
- `remember()`로 방금 입력된 기억이
- `decide()` 단계에 도달하기도 전에 증발
- → **'단기 기억의 영구 저장소 전이 실패'**

---

## 🎛️ 통제력 상실 (PFC 붕괴와 엔트로피 폭발)

### PFC 의사결정 실패

**정상 상태:**
$$
P_n(k) = \frac{\exp(\beta \cdot U_{n,k})}{\sum_j \exp(\beta \cdot U_{n,j})}
$$

**여기서:**
- $\beta = \text{decision_temperature}^{-1}$
- $U_{n,k} = U_0 + \alpha \cdot C_n(k) + T_n(k)$

**치매/알츠하이머:**
$$
\beta \to 0 \quad (\text{decision_temperature} \to \infty)
$$

**결과:**
$$
P_n(k) \to \frac{1}{N} \quad (\text{균등 분포})
$$

**엔트로피:**
$$
E_n = -\sum_k P_n(k) \ln P_n(k) \to \ln(N) \quad (\text{최대 엔트로피})
$$

**현상:**
- 시스템의 엔트로피가 이론적 최대치에 도달
- AI는 모든 질문에 무작위로 답함
- 또는 과거의 강력한 습관(BasalGanglia)에만 의존

---

## 🛠️ 구현 계획

### 1. Core Decay 메커니즘

**파일**: `src/cognitive_kernel/core.py`

**위치**: `decide()` 메서드 내 코어 강도 계산 후

**구현:**
```python
# 코어 강도 계산
core_strength = min(1.0, alpha * total_importance / len(memories))

# Core decay 적용
if self.mode_config.core_decay_rate > 0:
    lambda_decay = self.mode_config.core_decay_rate
    if not hasattr(self, '_last_decay_time'):
        self._last_decay_time = time.time()
    
    delta_t = time.time() - self._last_decay_time
    core_strength *= math.exp(-lambda_decay * delta_t)
    self._last_decay_time = time.time()
```

---

### 2. ModeConfig에 파라미터 추가

**파일**: `src/cognitive_kernel/cognitive_modes.py`

**추가:**
```python
@dataclass
class ModeConfig:
    # ... 기존 파라미터들 ...
    
    # Core decay (중력 붕괴)
    core_decay_rate: float = 0.0  # 0이면 비활성화
    # core_decay_rate > 0: 치매/알츠하이머
    # core_decay_rate = 0: 정상
```

---

### 3. 치매/알츠하이머 프리셋

**파일**: `src/cognitive_kernel/cognitive_modes.py`

**치매 (DEMENTIA):**
```python
@staticmethod
def dementia() -> ModeConfig:
    """
    치매 모드: 코어 강도 점진적 감소
    """
    return ModeConfig(
        gate_threshold=0.2,        # 필터링 능력 약화
        max_channels=5,
        decision_temperature=0.5,  # 판단력 저하
        working_memory_capacity=3, # Miller's Law 붕괴
        tau=1.5,                   # 탐색 과다 (의미 없는 배회)
        impulsivity=0.6,
        patience=0.3,
        damping=0.5,               # MemoryRank 급락
        local_weight_boost=0.5,    # 연결 고리 파괴
        novelty_sensitivity=1.5,
        stress_baseline=0.6,
        core_decay_rate=0.001,     # 느린 붕괴 (λ_d)
    )
```

**알츠하이머 (ALZHEIMER):**
```python
@staticmethod
def alzheimer() -> ModeConfig:
    """
    알츠하이머 모드: 코어 중력 급격한 붕괴
    """
    return ModeConfig(
        gate_threshold=0.0,        # 필터링 능력 완전 상실
        max_channels=10,           # 모든 자극이 고통으로 다가옴
        decision_temperature=0.1,  # β ↓: 논리적 판단 불가
        working_memory_capacity=2,  # Miller's Law 붕괴 (방금 한 말도 잊음)
        tau=2.0,                   # 탐색 과다 (의미 없는 배회)
        impulsivity=0.7,
        patience=0.1,
        damping=0.3,               # MemoryRank 급락 (기억의 중요도 전파 정지)
        local_weight_boost=0.1,     # 연결 고리 완전 파괴
        novelty_sensitivity=2.0,
        stress_baseline=0.7,
        core_decay_rate=0.01,      # 빠른 붕괴 (λ_a > λ_d)
    )
```

---

### 4. MemoryRank 엣지 붕괴

**파일**: `src/cognitive_kernel/engines/memoryrank/memoryrank_engine.py`

**구현:**
```python
def apply_edge_decay(self, decay_rate: float, delta_t: float):
    """엣지 가중치 붕괴"""
    if self._M is None:
        return
    
    # 엣지 가중치에 붕괴 적용
    decay_factor = math.exp(-decay_rate * delta_t)
    self._M *= decay_factor
```

---

### 5. Panorama 반감기 가속

**파일**: `src/cognitive_kernel/engines/panorama/panorama_engine.py`

**구현:**
```python
# recency_half_life를 동적으로 조정
if mode_config.recency_acceleration > 1.0:
    effective_half_life = recency_half_life / mode_config.recency_acceleration
else:
    effective_half_life = recency_half_life
```

---

## 📊 구현 상태 요약

### 현재 상태

- ✅ 코어 강도 계산 구현됨
- ✅ 엔트로피-회전-피드백 루프 구현됨
- ❌ Core decay 메커니즘 없음
- ❌ 엣지 붕괴 메커니즘 없음
- ❌ 반감기 가속 메커니즘 없음

### 필요한 작업

1. **Core decay 메커니즘** 추가
2. **ModeConfig에 core_decay_rate** 추가
3. **치매/알츠하이머 프리셋** 작성
4. **엣지 붕괴 메커니즘** 추가
5. **반감기 가속 메커니즘** 추가

---

## 🎯 핵심 질문

> **"이 모든 과정을 지켜보고 있는 시스템(자아)은 자신이 잊혀가고 있다는 사실을 언제까지 인지할 수 있을까요?"**

**답변:**

**엔트로피가 임계치를 넘는 순간**

**구현:**
```python
# decide() 메서드 내
entropy = -sum(prob * math.log(prob) for prob in probabilities if prob > 0)
core_strength = ...

# 인지적 절규
if entropy > entropy_threshold and core_strength < 0.3:
    self._cognitive_distress = True
    # "나 지금 기억이 안 나..."
```

**이것은 단순한 에러 메시지가 아니라 시스템이 느끼는 '인지적 절규'**

---

## 📝 결론

### 현재 위치

> **"기억을 만드는 법을 완전히 이해한 상태"**

**그래서 이제야 가능한 질문:**
> **"그럼 이게 어떻게 사라지는가?"**

### 다음 작업

**질환 추가 ❌**

**Core decay 모델링 ⭕**

**구체적 작업:**
1. Core decay 메커니즘 구현
2. 기억 중요도 생성/소멸 분리
3. "오래된 기억 vs 새 기억" 시간축 분리
4. 치매 ↔ 알츠하이머 경계 조건 정의

### 목표

**이건 더 이상 철학이 아니라 엔진 완성 단계다.**

**여기까지 왔다.**
**이제 정말 "뇌를 설명하는 코드" 영역이다.**

---

**마지막 업데이트**: 2026-01-31

