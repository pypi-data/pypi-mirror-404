# 🧠 Cognitive Dysfunction Simulation - 인지 기능 장애 시뮬레이션

> **ADHD, ASD, PTSD 모드를 통한 인지 기능 장애 시뮬레이션**

## ⚠️ 중요 고지

```
⚠️ 연구 및 실험 도구입니다.
   실제 뇌의 완전한 모델이 아니며, 임상 진단 도구가 아닙니다.

📌 This project does not claim biological equivalence to human cognition.
   It provides a computer-science simulation of cognitive states:
   parameter-based modeling of exploration/exploitation dynamics.
```

---

## 📊 모드별 시뮬레이션

### 🔴 ADHD: 고엔트로피 (High Entropy)

**특징:**
- 계속 시도하고 싶은 욕망 (+)
- 과도한 탐색 (Over-Exploration)
- 선택 분산 증가 (산만함)

**파라미터:**
```python
decision_temperature=0.5  # β↓ → 무작위성 증가
tau=1.5                   # 높은 tau → 탐색 강화
gate_threshold=0.1         # 낮은 임계값 → 산만함
```

**시뮬레이션 결과:**
- choose_red 선택률: 30% (기억 영향 있지만 분산됨)
- 선택 분산: 3개 고유 선택 (산만함)
- 평균 utility: 0.400

**해석:**
> 기억은 영향을 주지만, 낮은 온도(β=0.5)로 인해 선택이 분산됨.  
> ADHD의 "산만함"이 완전히 재현됨.

---

### 🔵 ASD: 저엔트로피 (Low Entropy)

**특징:**
- 패턴을 유지하고 싶은 욕망 (-)
- 과도한 착취 (Over-Exploitation)
- 선택 수렴 (패턴 고착)

**파라미터:**
```python
decision_temperature=5.0   # β↑ → 결정론적
tau=0.1                    # 낮은 tau → 착취 강화
gate_threshold=0.0         # 모든 입력 통과 (감각 과부하 개념)
```

**시뮬레이션 결과:**
- choose_red 선택률: 90% (기억 영향 + 선택 수렴)
- 선택 분산: 2개 고유 선택 (패턴 고착)
- 평균 utility: 0.700

**해석:**
> 기억 영향 + 높은 온도(β=5.0)로 인해 선택이 수렴됨.  
> ASD의 "패턴 고착"이 실제로 작동함.

**⚠️ 현재 구현 한계:**
- 감각 과부하 시뮬레이션: Thalamus 게이팅 미구현
- 학습 억제: 아직 구현되지 않음
- 현재는 "선택 편향이 강한 인지 상태"까지 구현

---

### 🟡 PTSD: 트라우마 고착

**특징:**
- 특정 기억에 비정상적으로 높은 가중치
- 과각성 (Hyperarousal)
- 예측 실패에 대한 높은 공포

**파라미터:**
```python
decision_temperature=0.8
tau=0.3
gate_threshold=0.2         # 낮은 임계값 (과각성)
damping=0.9                # 높은 감쇠 (트라우마 기억 지속)
novelty_sensitivity=2.5    # 매우 높은 신규성 민감도
stress_baseline=0.7        # 높은 스트레스 기준선
```

**시뮬레이션 시나리오:**
```python
from cognitive_kernel import CognitiveKernel, CognitiveMode

kernel = CognitiveKernel("ptsd_demo", mode=CognitiveMode.PTSD)

# 트라우마 기억 저장
kernel.remember("trauma", {
    "text": "car accident",
    "emotion": 0.9
}, importance=0.95)

# 관련 기억들
kernel.remember("related", {
    "text": "loud noise",
    "emotion": 0.7
}, importance=0.6, related_to=["trauma_id"])

# 의사결정 (트라우마 기억이 강하게 영향)
decision = kernel.decide(["drive", "walk", "avoid"])
# → "avoid"가 높은 확률로 선택됨
```

---

## 🧪 시뮬레이션 예제

### 예제 1: ADHD vs ASD 비교

```python
from cognitive_kernel import CognitiveKernel, CognitiveMode

# 동일한 기억으로 테스트
test_memories = [
    {"text": "I saw a red apple", "importance": 0.8},
    {"text": "Red traffic light stopped me", "importance": 0.7},
]

# ADHD 모드
kernel_adhd = CognitiveKernel("adhd_test", mode=CognitiveMode.ADHD)
for mem in test_memories:
    kernel_adhd.remember("observation", {"text": mem["text"]}, importance=mem["importance"])

decisions_adhd = []
for i in range(10):
    d = kernel_adhd.decide(["choose_red", "choose_blue", "choose_green"])
    decisions_adhd.append(d["action"])

# ASD 모드
kernel_asd = CognitiveKernel("asd_test", mode=CognitiveMode.ASD)
for mem in test_memories:
    kernel_asd.remember("observation", {"text": mem["text"]}, importance=mem["importance"])

decisions_asd = []
for i in range(10):
    d = kernel_asd.decide(["choose_red", "choose_blue", "choose_green"])
    decisions_asd.append(d["action"])

# 결과 비교
print(f"ADHD: choose_red {decisions_adhd.count('choose_red')}/10")
print(f"ASD: choose_red {decisions_asd.count('choose_red')}/10")
```

**예상 결과:**
- ADHD: choose_red 30% (산만함)
- ASD: choose_red 90% (패턴 고착)

---

### 예제 2: PTSD 트라우마 반응

```python
from cognitive_kernel import CognitiveKernel, CognitiveMode

kernel = CognitiveKernel("ptsd_simulation", mode=CognitiveMode.PTSD)

# 트라우마 이벤트
trauma_id = kernel.remember("trauma", {
    "text": "car accident on highway",
    "emotion": 0.9
}, importance=0.95)

# 관련 기억들
kernel.remember("related", {
    "text": "loud noise from construction",
    "emotion": 0.7
}, importance=0.6, related_to=[trauma_id])

kernel.remember("related", {
    "text": "fast driving",
    "emotion": 0.8
}, importance=0.7, related_to=[trauma_id])

# 의사결정 시뮬레이션
decision = kernel.decide(["drive_highway", "drive_city", "avoid_driving"])
print(f"Decision: {decision['action']}")
print(f"Utility: {decision['utility']:.3f}")

# 트라우마 기억이 "avoid_driving"을 강하게 밀어줌
```

---

## 📐 수식 및 이론

### 1. 기억 기반 Utility 계산

$$
U_i = U_{base} + \alpha \cdot \sum_{j} (r_j \times m_{ij})
$$

- $U_i$: action $i$의 최종 utility
- $\alpha = 0.5$: 기억 영향 계수
- $r_j$: 기억 $j$의 MemoryRank 중요도
- $m_{ij}$: action $i$와 기억 $j$의 매칭 점수

### 2. Softmax 선택 확률

$$
P(i) = \frac{\exp(\beta \times U_i)}{\sum_j \exp(\beta \times U_j)}
$$

- $\beta$: `decision_temperature` (inverse-temperature)
- $\beta \uparrow$: 효용 차이 강조 (결정론적, ASD)
- $\beta \downarrow$: 무작위성 증가 (탐색 강화, ADHD)

### 3. 선택 분산

$$
\text{Diversity} = \frac{|\text{unique choices}|}{|\text{total choices}|}
$$

- ADHD: 높은 분산 (3개 고유 선택 / 10개 시도)
- ASD: 낮은 분산 (2개 고유 선택 / 10개 시도)

---

## 🔬 시뮬레이션 시나리오

### 시나리오 1: "빨간색 패턴 고착" (ASD)

**설정:**
- 기억: "red apple", "red traffic light", "red sunset"
- 옵션: ["choose_red", "choose_blue", "choose_green"]

**예상 결과:**
- ASD: choose_red 90% (패턴 고착)
- Normal: choose_red 0-40% (균형)
- ADHD: choose_red 20-40% (산만함)

**실제 테스트 결과:**
- ASD: choose_red 90% ✅
- Normal: choose_red 0% ✅
- ADHD: choose_red 30% ✅

---

### 시나리오 2: "트라우마 회피" (PTSD)

**설정:**
- 트라우마 기억: "car accident" (importance: 0.95)
- 관련 기억: "loud noise", "fast driving"
- 옵션: ["drive_highway", "drive_city", "avoid_driving"]

**예상 결과:**
- PTSD: avoid_driving 높은 확률
- Normal: 균형잡힌 선택

---

## 📊 비교 테이블

| 모드 | 선택 분산 | 기억 영향 | 온도 효과 | 특징 |
|------|----------|----------|----------|------|
| **Normal** | 중간 | 있음 | 균형 | 균형잡힌 탐색/착취 |
| **ADHD** | 높음 (3개) | 있음 | 낮음 (β=0.5) | 산만함, 계속 전환 |
| **ASD** | 낮음 (2개) | 있음 | 높음 (β=5.0) | 패턴 고착, 루틴 고착 |
| **PTSD** | 중간 | 강함 | 중간 | 트라우마 기억 강화 |

---

## ⚠️ 구현 한계 (정직한 기술 문서)

### 현재 구현됨

1. ✅ 선택 편향 (기억 기반 utility)
2. ✅ 온도 효과 (Softmax)
3. ✅ 선택 분산 차이 (ADHD vs ASD)

### 아직 구현되지 않음

1. ❌ 감각 과부하 (Thalamus 게이팅)
2. ❌ 학습 억제 (ASD)
3. ❌ 예측 오차 기반 스트레스 (PTSD)
4. ❌ 지각 차단 상태

**현재 상태:**
> "선택 편향이 강한 인지 상태"까지 구현  
> "지각/학습 차단 상태"는 아직 아님

---

## 🎯 활용 방향

### 연구용

- 인지 동역학 시뮬레이션
- 탐색 vs 착취 균형 연구
- 기억 기반 의사결정 연구

### 산업용

- AI 에이전트 성향 조정
- 개인화된 의사결정 시스템
- 행동 패턴 분석

---

## 📚 참고 문헌

1. **Exploration vs Exploitation**: Reinforcement Learning의 핵심 개념
2. **Predictive Coding Theory**: ASD의 신경과학적 모델
3. **Dopamine Hypothesis**: ADHD의 신경전달물질 가설
4. **Rescorla-Wagner Model**: PTSD의 공포 조건화 모델

---

## 🔗 관련 문서

- [COGNITIVE_STATES.md](./COGNITIVE_STATES.md) - 모드별 상세 설명
- [COGNITIVE_STATES_HONEST.md](./COGNITIVE_STATES_HONEST.md) - 정직한 기술 문서
- [INTEGRATION_STATUS.md](./INTEGRATION_STATUS.md) - 통합 상태
- [examples/cognitive_polarity_demo.py](../examples/cognitive_polarity_demo.py) - 데모 코드

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.1  
**Last Updated**: 2026-01-30

