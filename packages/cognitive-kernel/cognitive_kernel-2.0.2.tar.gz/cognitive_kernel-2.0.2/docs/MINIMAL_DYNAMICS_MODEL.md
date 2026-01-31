# 🏛️ Cognitive Kernel v2.0.1 최소 차분 모델

> **코드와 1:1로 대응되는 수학적 정의**

이 모델은 결정 스텝 $n$에서 회상된 기억의 중요도와 텍스트 매칭을 기반으로 시스템 엔트로피($E_n$)가 결정되는 과정을 정의합니다.

---

## 📐 상태방정식

### 1. 기억 관련성 계산

$$
C_n(k) = \min\left(1, \sum_{i} s_i \cdot m_{i,k}\right)
$$

**코드 구현:**
```python
# _calculate_memory_relevance()
total_relevance = 0.0
for mem in memories:
    importance = mem.get("importance", 0.0)  # s_i
    match_score = 0.0  # m_{i,k}
    for keyword in option_keywords:
        if keyword in content_text:
            match_score += 1.0 / len(option_keywords)
    total_relevance += importance * match_score  # s_i * m_{i,k}

return min(1.0, total_relevance)  # C_n(k)
```

**주의:**
- 하한 0 clamp는 코드에 없음 (음수가 나올 경로가 없어서 결과는 동일)
- 실제 구현: `min(1.0, total_relevance)`만 수행

---

### 2. Utility 계산

$$
U_{n,k} = U_0 + \alpha \cdot C_n(k)
$$

**코드 구현:**
```python
# decide() 메서드
alpha = 0.5  # 기억 영향 계수
expected_reward = 0.5 + alpha * memory_relevance  # U_0 + α * C_n(k)
```

**변수:**
- $U_0 = 0.5$: 기본 보상 (코드 내부 상수)
- $\alpha = 0.5$: 기억 영향 계수 (코드 내부 상수)

---

### 3. 선택 확률 (PFC Softmax)

$$
P_n(k) = \frac{\exp(\beta \cdot U_{n,k})}{\sum_j \exp(\beta \cdot U_{n,j})}
$$

**코드 구현:**
```python
# PFCEngine._softmax_probabilities()
beta = self.config.decision_temperature
exp_values = [math.exp(beta * (u - max_u)) for u in utilities]
total = sum(exp_values)
probs = [e / total for e in exp_values]
```

**변수:**
- $\beta = \text{decision\_temperature}$: Inverse-temperature
- 구현 주체: **PFCEngine.process(actions)** 내부 softmax

---

### 4. 시스템 엔트로피

$$
E_n = -\sum_{k} P_n(k) \ln P_n(k)
$$

**의미:**
- 선택의 불확실성 및 탐색도
- $E_n \to 0$: 저엔트로피 (결정론적, 수렴)
- $E_n \to \ln(N)$: 고엔트로피 (무작위, 분산)

---

## 🔍 변수 정의 (v2.0.1 구현 기준)

| 변수 | 정의 | 코드 위치 |
|------|------|----------|
| $s_i$ | recall()로 반환된 기억 $i$의 중요도 점수 | MemoryRank score |
| $m_{i,k}$ | 옵션 $k$의 키워드가 기억 $i$의 payload 텍스트와 매칭되는 정도 (0~1) | `_calculate_memory_relevance()` |
| $\beta$ | decision_temperature (Inverse-temperature) | `PFCConfig.decision_temperature` |
| $\alpha$ | 기억 영향 계수 (기본 보상 $U_0$에 대한 기억 중력의 가중치) | `decide()` 내부 상수 (0.5) |
| $U_0$ | 기본 보상 | `decide()` 내부 상수 (0.5) |
| $E_n$ | 시스템 엔트로피 (선택의 불확실성 및 탐색도) | 계산 가능 |

---

## ⚖️ 모드별 동역학적 특성

### ASD (-): 저엔트로피 고착

**파라미터:**
- $\beta \uparrow$ (decision_temperature = 5.0)
- $\alpha = 0.5$ (기억 영향 계수)

**동역학:**
$$
\beta \uparrow + \alpha C_n(k) \to U \text{ 격차 확대} \to P \text{ 수렴} \to E_n \to 0
$$

**결과:**
- 선택 분포 $P$가 특정 선택지로 수렴
- 엔트로피 $E_n \to 0$ (저엔트로피 고착 상태)

**코드 검증:**
- 테스트 결과: choose_red 90% (패턴 고착)
- 선택 분산: 2개 고유 선택

---

### ADHD (+): 고엔트로피 발산

**파라미터:**
- $\beta \downarrow$ (decision_temperature = 0.5)
- $\alpha = 0.5$ (기억 영향 계수)

**동역학:**
$$
\beta \downarrow \to P \text{ 평탄화} \to E_n \to \ln(N)
$$

**결과:**
- 선택 분포 $P$가 평탄해짐
- 엔트로피 $E_n \to \ln(N)$ (고엔트로피 발산 상태)

**코드 검증:**
- 테스트 결과: choose_red 30% (산만함)
- 선택 분산: 3개 고유 선택

**주의:**
- BasalGanglia의 `tau`, `impulsivity`, `patience`는 현재 `P_n(k)`에 직접 개입하지 않음
- BasalGanglia는 `habit_suggestion` 채널로만 영향 (충돌 flag 관찰 가능)

---

## 🔬 코드-수식 1:1 대응

### decide() 메서드 실행 경로

```python
def decide(self, options: List[str], ...):
    # 1. 기억 회상
    memories = self.recall(k=5)  # s_i 획득
    
    # 2. 관련성 계산
    for opt in options:
        opt_keywords = self._extract_keywords(opt)
        memory_relevance = self._calculate_memory_relevance(opt_keywords, memories)
        # → C_n(k) = min(1, Σ s_i * m_{i,k})
    
    # 3. Utility 계산
    expected_reward = 0.5 + 0.5 * memory_relevance
    # → U_{n,k} = U_0 + α * C_n(k)
    
    # 4. PFC Softmax
    pfc_result = self.pfc.process(actions)
    # → P_n(k) = exp(β * U_{n,k}) / Σ exp(β * U_{n,j})
    
    # 5. 엔트로피 계산 (가능)
    # E_n = -Σ P_n(k) * ln(P_n(k))
```

---

## 📊 수식 정리 (최종 확정본)

### 완전한 모델

$$
\begin{align}
C_n(k) &= \min\left(1, \sum_{i} s_i \cdot m_{i,k}\right) \\
U_{n,k} &= U_0 + \alpha \cdot C_n(k) \\
P_n(k) &= \frac{\exp(\beta \cdot U_{n,k})}{\sum_j \exp(\beta \cdot U_{n,j})} \\
E_n &= -\sum_{k} P_n(k) \ln P_n(k)
\end{align}
$$

**변수 정의:**
- $s_i$: recall() 반환 중요도 (현재 MemoryRank score)
- $m_{i,k} \in [0,1]$: 텍스트 키워드 매칭 (현재 포함 여부 기반 분할 점수)
- $\beta = \text{decision\_temperature}$: Inverse-temperature
- $\alpha = 0.5$: 기억 영향 계수 (현재 코드에선 decide() 내부 상수)
- $U_0 = 0.5$: 기본 보상 (현재 코드에선 decide() 내부 상수)

---

## 🎯 모드별 엔트로피 예측

### ASD 모드

$$
\beta = 5.0, \quad \alpha = 0.5
$$

**시나리오:** "red" 관련 기억 3개 (s_i = 0.8, 0.7, 0.6)

$$
C_n(\text{choose\_red}) = \min(1, 0.8 \times 1.0 + 0.7 \times 1.0 + 0.6 \times 1.0) = 1.0
$$

$$
U_{n,\text{choose\_red}} = 0.5 + 0.5 \times 1.0 = 1.0
$$

$$
U_{n,\text{choose\_blue}} = U_{n,\text{choose\_green}} = 0.5 + 0.5 \times 0.0 = 0.5
$$

$$
P_n(\text{choose\_red}) \approx 0.99 \quad \text{(β=5.0으로 수렴)}
$$

$$
E_n \approx -0.99 \ln(0.99) - 0.005 \ln(0.005) - 0.005 \ln(0.005) \approx 0.05
$$

**결과:** $E_n \to 0$ (저엔트로피 고착) ✅

---

### ADHD 모드

$$
\beta = 0.5, \quad \alpha = 0.5
$$

**동일한 시나리오:**

$$
U_{n,\text{choose\_red}} = 1.0, \quad U_{n,\text{choose\_blue}} = U_{n,\text{choose\_green}} = 0.5
$$

$$
P_n(\text{choose\_red}) \approx 0.38, \quad P_n(\text{choose\_blue}) \approx 0.31, \quad P_n(\text{choose\_green}) \approx 0.31
$$

$$
E_n \approx -0.38 \ln(0.38) - 0.31 \ln(0.31) - 0.31 \ln(0.31) \approx 1.08
$$

**최대 엔트로피:** $\ln(3) \approx 1.10$

**결과:** $E_n \to \ln(N)$ (고엔트로피 발산) ✅

---

## ⚠️ 정확한 구현 상태

### 현재 구현됨

1. ✅ $C_n(k)$ 계산 (`_calculate_memory_relevance()`)
2. ✅ $U_{n,k}$ 계산 (`decide()` 메서드)
3. ✅ $P_n(k)$ 계산 (PFCEngine softmax)
4. ✅ $E_n$ 계산 가능 (수식으로 계산)

### 현재 미구현

1. ❌ BasalGanglia가 $P_n(k)$에 직접 개입
   - 현재는 `habit_suggestion` 채널로만 영향
   - 충돌 flag로 관찰 가능

2. ❌ Thalamus 게이팅 루프
   - `remember()`가 Thalamus를 거치지 않음

3. ❌ Hypothalamus 통합
   - 에너지/스트레스가 utility에 반영되지 않음

---

## 🔗 관련 문서

- [COGNITIVE_STATES.md](./COGNITIVE_STATES.md) - 모드별 상세 설명
- [COGNITIVE_LOOPS_ANALYSIS.md](./COGNITIVE_LOOPS_ANALYSIS.md) - 루프 분석
- [COGNITIVE_STATES_HONEST.md](./COGNITIVE_STATES_HONEST.md) - 정직한 기술 문서

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.1  
**Last Updated**: 2026-01-30

