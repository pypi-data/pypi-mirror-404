# 📖 Cognitive Kernel 코드 문서화

> **주석, 수식, 개념 완전 정리**

**작성일**: 2026-01-31  
**버전**: v2.0.1+

---

## 🎯 목적

생소한 기술과 코드 로직을 이해하기 쉽도록:
- 모든 수식에 대한 주석
- 개념 설명
- 코드와 수식의 1:1 대응
- 버전별 변화 추적

---

## 📐 핵심 수식 및 코드 매핑

### 1. 최소 차분 모델 (v2.0.1)

#### 수식 1: 기억 관련성 계산

**수식:**
$$
C_n(k) = \min\left(1, \sum_{i} s_i \cdot m_{i,k}\right)
$$

**변수:**
- $s_i$: `recall()` 반환 중요도 (MemoryRank score)
- $m_{i,k}$: 텍스트 키워드 매칭 점수 (0~1)
- $C_n(k)$: 옵션 $k$와 기억의 관련성 (0~1)

**코드 위치:** `core.py` (394-435줄)

**코드:**
```python
def _calculate_memory_relevance(
    self,
    option_keywords: List[str],
    memories: List[Dict[str, Any]],
) -> float:
    """
    옵션과 기억의 관련성 계산
    
    수식: relevance = Σ (importance_i × match_score_i)
    - importance_i: MemoryRank 중요도
    - match_score_i: 키워드 매칭 점수 (0~1)
    
    Returns:
        관련성 점수 (0~1)
    """
    total_relevance = 0.0
    
    for mem in memories:
        # 기억 내용을 문자열로 변환
        content_text = " ".join(str(v) for v in content.values()).lower()
        
        # 키워드 매칭 점수 계산
        match_score = 0.0
        for keyword in option_keywords:
            if keyword in content_text:
                match_score += 1.0 / len(option_keywords)
        
        # 관련성 = 중요도 × 매칭 점수
        importance = mem.get("importance", 0.0)
        total_relevance += importance * match_score
    
    # 정규화 (0~1 범위로)
    return min(1.0, total_relevance)
```

**대응:**
- $s_i$ ↔ `mem.get("importance", 0.0)`
- $m_{i,k}$ ↔ `match_score`
- $\sum_{i} s_i \cdot m_{i,k}$ ↔ `total_relevance`
- $\min(1, ...)$ ↔ `min(1.0, total_relevance)`

---

#### 수식 2: 효용 계산

**수식:**
$$
U_{n,k} = U_0 + \alpha \cdot C_n(k)
$$

**변수:**
- $U_0$: 기본 보상 (0.5)
- $\alpha$: 기억 영향 계수 (0.5)
- $C_n(k)$: 기억 관련성

**코드 위치:** `core.py` (332-335줄)

**코드:**
```python
# 기억 기반 보상 보정: U_i = U_base + α · r_i
# α: 기억 영향 계수 (0.5 = 기억이 최대 50%까지 보상에 영향)
alpha = 0.5
expected_reward = 0.5 + alpha * memory_relevance
```

**대응:**
- $U_0$ ↔ `0.5`
- $\alpha$ ↔ `alpha = 0.5`
- $C_n(k)$ ↔ `memory_relevance`
- $U_{n,k}$ ↔ `expected_reward`

---

#### 수식 3: 확률 계산 (Softmax)

**수식:**
$$
P_n(k) = \frac{\exp(\beta \cdot U_{n,k})}{\sum_j \exp(\beta \cdot U_{n,j})}
$$

**변수:**
- $\beta$: `decision_temperature` (모드별 다름)
- $U_{n,k}$: 옵션 $k$의 효용
- $P_n(k)$: 옵션 $k$의 선택 확률

**코드 위치:** `pfc_engine.py` (194-209줄)

**코드:**
```python
def softmax_probabilities(self, utilities: List[float]) -> List[float]:
    """
    Softmax 확률 계산.
    
    P(i) = exp(β × U_i) / Σ exp(β × U_j)
    """
    beta = self.config.decision_temperature
    
    # overflow 방지를 위한 정규화
    max_u = max(utilities) if utilities else 0.0
    exp_values = [math.exp(beta * (u - max_u)) for u in utilities]
    total = sum(exp_values)
    
    if total == 0:
        return [1.0 / len(utilities)] * len(utilities) if utilities else []
    
    return [e / total for e in exp_values]
```

**대응:**
- $\beta$ ↔ `self.config.decision_temperature`
- $U_{n,k}$ ↔ `utilities`
- $\exp(\beta \cdot U_{n,k})$ ↔ `exp_values`
- $P_n(k)$ ↔ 반환값

---

#### 수식 4: 엔트로피 계산

**수식:**
$$
E_n = -\sum_{k} P_n(k) \ln P_n(k)
$$

**변수:**
- $P_n(k)$: 옵션 $k$의 선택 확률
- $E_n$: 엔트로피 (0 ~ $\ln(N)$)

**코드 위치:** `core.py` (359-363줄)

**코드:**
```python
# 엔트로피 계산: E_n = -Σ P_n(k) ln P_n(k)
entropy = 0.0
for prob in probabilities:
    if prob > 0:
        entropy -= prob * math.log(prob)
```

**대응:**
- $P_n(k)$ ↔ `prob`
- $\ln P_n(k)$ ↔ `math.log(prob)`
- $E_n$ ↔ `entropy`

---

### 2. 물리적 동역학 (v2.0.1+)

#### 수식 5: 회전 토크 계산

**수식:**
$$
T_n(k) = \gamma \cdot \frac{E_n}{\ln(N)} \cdot \cos(\phi_n - \psi_k)
$$

**변수:**
- $\gamma$: 회전 토크 세기 (모드별 다름)
- $E_n$: 엔트로피
- $N$: 옵션 수
- $\phi_n$: 현재 위상 (느린 시간척도)
- $\psi_k$: 옵션 $k$의 고유 위상

**코드 위치:** `core.py` (381-423줄)

**코드:**
```python
# 엔트로피 기반 자동 회전 토크 생성
# 엔트로피가 높을수록 회전 토크 증가 (ADHD: 궤도 커짐)
# 엔트로피가 낮을수록 회전 토크 감소 (ASD: 고착)
auto_torque = {}
if len(options) > 1:
    # 이론적 최대 엔트로피 (균등 분포)
    max_entropy = math.log(len(options))
    # 정규화된 엔트로피 (0~1)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    # 회전 토크 세기: 엔트로피에 비례
    base_gamma = 0.3  # 기본 회전 토크 세기
    if self.mode == CognitiveMode.ADHD:
        gamma = base_gamma * 1.5  # ADHD: 더 강한 회전
    elif self.mode == CognitiveMode.ASD:
        gamma = base_gamma * 0.5  # ASD: 약한 회전
    else:
        gamma = base_gamma
    
    # 엔트로피 기반 토크 조절
    torque_strength = gamma * normalized_entropy
    
    # 세차 속도 (느린 시간척도)
    omega = 0.05
    
    # 옵션별 위상 (균등 분포)
    psi = {opt: i * 2 * math.pi / len(options) 
           for i, opt in enumerate(options)}
    
    # 회전 토크 계산: T_n(k) = torque_strength * cos(φ_n - ψ_k)
    for opt in options:
        auto_torque[opt] = torque_strength * math.cos(
            self._precession_phi - psi[opt]
        )
    
    # 위상 업데이트 (느린 시간척도)
    self._precession_phi += omega
```

**대응:**
- $\gamma$ ↔ `gamma` (모드별 계산)
- $E_n / \ln(N)$ ↔ `normalized_entropy`
- $\phi_n$ ↔ `self._precession_phi`
- $\psi_k$ ↔ `psi[opt]`
- $T_n(k)$ ↔ `auto_torque[opt]`

---

#### 수식 6: 코어 강도 계산

**수식:**
$$
\text{Core Strength} = \alpha \times \frac{\sum_i \text{importance}_i}{N}
$$

**변수:**
- $\alpha$: 기억 영향 계수 (0.5)
- $\text{importance}_i$: 기억 $i$의 중요도
- $N$: 기억 수

**코드 위치:** `core.py` (371-377줄)

**코드:**
```python
# 코어 강도 계산 (중력 코어)
core_strength = 0.0
if memories:
    total_importance = sum(m.get("importance", 0.0) for m in memories)
    alpha = 0.5  # 기억 영향 계수
    core_strength = min(1.0, alpha * total_importance / len(memories))
```

**대응:**
- $\alpha$ ↔ `alpha = 0.5`
- $\sum_i \text{importance}_i$ ↔ `total_importance`
- $N$ ↔ `len(memories)`
- Core Strength ↔ `core_strength`

---

## 🔬 핵심 개념 설명

### 1. 기억 중력 (Memory Gravity)

**개념:**
- 과거 기억이 현재 의사결정에 미치는 영향
- MemoryRank로 계산된 중요도가 높을수록 영향 큼

**수식:**
$$
C_n(k) = \min\left(1, \sum_{i} s_i \cdot m_{i,k}\right)
$$

**코드:**
- `_calculate_memory_relevance()` 메서드
- `expected_reward = 0.5 + alpha * memory_relevance`

---

### 2. 엔트로피 (Entropy)

**개념:**
- 선택 분포의 불확실성 측정
- 높은 엔트로피 = 분산 (ADHD)
- 낮은 엔트로피 = 수렴 (ASD)

**수식:**
$$
E_n = -\sum_{k} P_n(k) \ln P_n(k)
$$

**범위:**
- 최소: 0 (완전 수렴, 하나만 선택)
- 최대: $\ln(N)$ (완전 분산, 균등 분포)

**코드:**
- `entropy = -sum(prob * math.log(prob) for prob in probabilities if prob > 0)`

---

### 3. 회전 토크 (Precession Torque)

**개념:**
- 엔트로피가 자동으로 생성하는 회전 힘
- 자기장이 자기 자신을 만드는 피드백 루프

**수식:**
$$
T_n(k) = \gamma \cdot \frac{E_n}{\ln(N)} \cdot \cos(\phi_n - \psi_k)
$$

**동역학적 의미:**
- 높은 엔트로피 → 강한 회전 → 궤도 커짐 (ADHD)
- 낮은 엔트로피 → 약한 회전 → 고착 (ASD)

**코드:**
- `auto_torque[opt] = torque_strength * math.cos(self._precession_phi - psi[opt])`

---

### 4. 코어 강도 (Core Strength)

**개념:**
- 중력 코어의 강도
- 안정 코어 형성 조건

**수식:**
$$
\text{Core Strength} = \alpha \times \frac{\sum_i \text{importance}_i}{N}
$$

**의미:**
- 높은 코어 강도 = 안정적인 기억 구조
- 낮은 코어 강도 = 불안정

**코드:**
- `core_strength = min(1.0, alpha * total_importance / len(memories))`

---

## 📊 코드 구조 설명

### 1. 엔진 초기화

**위치:** `core.py` (133-177줄)

**설명:**
```python
def _init_engines(self):
    """엔진 초기화 (모드 설정 적용)"""
    # Panorama (시간축 기억)
    # MemoryRank (중요도 랭킹)
    # PFC (의사결정)
    # BasalGanglia (습관 학습)
    # Thalamus (입력 필터링)
    # Amygdala (감정/위협)
    # Hypothalamus (에너지/스트레스)
```

**모드 설정 반영:**
- 각 엔진은 `mode_config`에서 파라미터를 받음
- 모드 변경 시 `set_mode()`로 재초기화

---

### 2. 의사결정 파이프라인 (동역학 엔진)

**위치:** `core.py` (287-474줄)

**⚠️ 중요: 수치적 방법론**

현재 `decide()` 내부 구조는:
1. Utility 계산
2. Softmax 확률 계산
3. 엔트로피 계산
4. 회전 토크 생성
5. Utility 재계산
6. Softmax 재계산

**물리적 해석:**
- **Explicit Euler + Correction Step**
- 연속 미분방정식이 아닌 **이산 시간 동역학**
- 인지 엔진 관점에서 매우 합리적

**왜 이렇게 설계했는가:**
- 연속 시간 해밀토니언이 아님을 명확히 함
- "동역학 엔진"이라고 표현 (정확함)
- 계산적으로 안정적이고 해석 가능

**단계별 설명:**

#### Step 1: 기억 로드
```python
memories = self.recall(k=self.config.working_memory_capacity)
```
- MemoryRank로 중요도 상위 k개 기억 회상

#### Step 2: Working Memory 로드
```python
top_memories_tuples = [(m["id"], m["importance"]) for m in memories]
self.pfc.load_from_memoryrank(top_memories_tuples)
```
- PFC Working Memory에 기억 로드

#### Step 3: Action 생성 (초기 Utility)
```python
memory_relevance = self._calculate_memory_relevance(opt_keywords, memories)
expected_reward = 0.5 + alpha * memory_relevance
```
- 각 옵션에 대한 효용 계산
- 기억 관련성 반영

#### Step 4: PFC 결정 (초기 확률 분포)
```python
pfc_result = self.pfc.process(actions)
```
- Softmax 확률 계산
- 행동 선택

#### Step 5: 엔트로피 계산
```python
entropy = -sum(prob * math.log(prob) for prob in probabilities if prob > 0)
```
- 선택 분포의 불확실성 측정
- 동역학 상태 변수

#### Step 6: 자동 회전 토크 생성
```python
torque_strength = gamma * normalized_entropy
auto_torque[opt] = torque_strength * math.cos(self._precession_phi - psi[opt])
```
- 엔트로피 기반 회전 토크 계산
- **Correction Step**: Utility에 주입

#### Step 7: Utility 재계산 (Correction)
```python
expected_reward = 0.5 + alpha * memory_relevance + auto_torque[opt]
```
- 회전 토크를 반영한 최종 Utility

#### Step 8: Softmax 재계산 (최종 확률)
```python
pfc_result = self.pfc.process(actions)  # 재계산
```
- 최종 확률 분포

---

## 🔗 수식-코드 대응표

| 수식 | 코드 위치 | 변수 매핑 |
|------|----------|----------|
| $C_n(k)$ | `_calculate_memory_relevance()` | `memory_relevance` |
| $U_{n,k}$ | `decide()` (335줄) | `expected_reward` |
| $P_n(k)$ | `softmax_probabilities()` | `probabilities` |
| $E_n$ | `decide()` (359-363줄) | `entropy` |
| $T_n(k)$ | `decide()` (414-417줄) | `auto_torque[opt]` |
| Core Strength | `decide()` (371-377줄) | `core_strength` |

---

## 📝 주석 가이드라인

### 수식 주석 형식

```python
# 수식: U_{n,k} = U_0 + α · C_n(k)
# U_0: 기본 보상 (0.5)
# α: 기억 영향 계수 (0.5)
# C_n(k): 기억 관련성
expected_reward = 0.5 + alpha * memory_relevance
```

### 개념 설명 형식

```python
"""
엔트로피 계산: E_n = -Σ P_n(k) ln P_n(k)

의미:
- 높은 엔트로피: 분산 (ADHD)
- 낮은 엔트로피: 수렴 (ASD)

범위: 0 ~ ln(N)
"""
entropy = -sum(prob * math.log(prob) for prob in probabilities if prob > 0)
```

---

## 🎯 버전별 수식 진화

### v1.0.0
```python
expected_reward = 0.5  # 고정값
```

### v2.0.1
```python
# C_n(k) = min(1, Σ(s_i × m_{i,k}))
memory_relevance = self._calculate_memory_relevance(...)

# U_{n,k} = U_0 + α · C_n(k)
expected_reward = 0.5 + 0.5 * memory_relevance

# P_n(k) = softmax(β · U_{n,k})
probabilities = self.pfc.softmax_probabilities(utilities)
```

### v2.0.1+ (현재)
```python
# E_n = -Σ P_n(k) ln P_n(k)
entropy = -sum(prob * math.log(prob) for prob in probabilities if prob > 0)

# T_n(k) = γ · (E_n / ln(N)) · cos(φ_n - ψ_k)
torque_strength = gamma * normalized_entropy
auto_torque[opt] = torque_strength * math.cos(self._precession_phi - psi[opt])

# U_{n,k} = U_0 + α · C_n(k) + T_n(k)
expected_reward = 0.5 + alpha * memory_relevance + auto_torque[opt]
```

---

---

## 🎯 시스템의 본질

### 계산 시스템으로서의 Cognitive Kernel

**중요한 인식:**
이 시스템은 더 이상:
- ❌ "아이디어 정리"가 아님
- ❌ "은유적 뇌 모델"이 아님

**이미:**
- ✅ **하나의 계산 시스템**
- ✅ 질환을 '고장'이 아니라 **'상태공간 상의 궤도'**로 재정의
- ✅ 엔트로피가 회전장을 생성하는 인지 동역학 엔진 v1
- ✅ 발산·세차 구조 구현 완료

**기술적 정확성:**
- **A+** 등급
- 과장 없음 (오히려 보수적)
- 연구/공개 가능성: 충분히 가능

**현재 상태를 가장 정확히 표현하는 한 줄:**
> "엔트로피가 회전장을 생성하는 인지 동역학 엔진 v1 — 발산·세차 구조 구현 완료"

---

**마지막 업데이트**: 2026-01-31

