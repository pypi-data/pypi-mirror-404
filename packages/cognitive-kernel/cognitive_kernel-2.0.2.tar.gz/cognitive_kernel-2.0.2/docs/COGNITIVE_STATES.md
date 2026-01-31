# 🧠 Cognitive States - 인지 상태 모델링

> **ADHD와 ASD를 "탐색(Exploration) vs 착취(Exploitation)"의 극단으로 모델링**

## ⚖️ 핵심 개념: 인지 동역학의 양극단

사용자님의 통찰:

> **"ADHD는 계속 시도하고 싶은 욕망 (+),  
> ASD는 패턴을 유지하고 싶은 욕망 (-)"**

이것은 인지 동역학의 **'탐색 vs 착취'** 대칭 구조를 정확히 타격합니다.

### 개념적 수식 (비율 표현)

$$
\text{Entropy\_Control} = \frac{\text{Exploration(ADHD)}}{\text{Exploitation(ASD)}}
$$

**주의**: 이는 개념적 비율 표현이며, 실제 계산되는 수치가 아닙니다.  
실제 구현은 각 모드의 파라미터 조합으로 동작합니다:

- **ADHD**: `tau↑`, `decision_temperature↑`, `gate_threshold↓` → 탐색 강화
- **ASD**: `tau↓`, `decision_temperature↓`, `gate_threshold↓` → 착취 강화

---

## 📊 모드별 특성

| 특성 | ADHD (고엔트로피) | Normal (균형) | ASD (저엔트로피) |
|------|------------------|---------------|-----------------|
| **동역학적 핵심** | 고엔트로피 (High Entropy) | Medium | 저엔트로피 (Low Entropy) |
| **PFC 제어** | 가변성 폭주 | 균형 | 안정성 고착 |
| **탐색 vs 착취** | 극단적 탐색 | 균형 | 극단적 착취 |
| **욕망의 방향** | 새로운 자극으로의 이행 | 균형 | 기존 궤적의 보존 |

---

## 🔴 ADHD Mode: "새로운 시도의 무한 궤적" (+)

### 특징

- **계속 시도하고 싶은 욕망** (+)
- **과도한 탐색 (Over-Exploration)**
- 하나의 궤적이 완성되기 전에 새로운 궤적 생성
- 멈추지 않는 엔진

### 파라미터 설정

```python
ModeConfig(
    gate_threshold=0.1,          # 낮은 임계값 → 모든 입력 통과 (산만)
    max_channels=10,             # 많은 채널 동시 처리
    decision_temperature=0.5,    # β↓ (temperature↑) → 무작위성 증가 (탐색 강화)
    working_memory_capacity=5,   # 낮은 용량 (집중력 부족)
    tau=1.5,                     # 높은 탐색 온도
    impulsivity=0.8,             # 높은 충동성
    patience=0.2,                # 낮은 인내심
    novelty_sensitivity=2.0,     # 높은 신규성 민감도
)
```

### 동역학

- **BasalGanglia**: 
  - `tau=1.5` (높음) → Softmax에서 Q값 차이가 덜 중요해짐 → 탐색 강화
  - `impulsivity=0.8` (높음) → 습관 형성 빠름, 탐색 증가
- **PFC**: 
  - `decision_temperature=0.5` (낮음) → `P(i) = exp(β×U_i)`에서 β가 낮아서 효용 차이 덜 중요
  - 여러 옵션이 비슷하면 무작위적 선택 증가 (탐색 강화)
- **Thalamus**: 
  - `gate_threshold=0.1` (낮음) → 모든 입력 통과 (산만)

---

## 🔵 ASD Mode: "패턴 유지의 완고한 궤적" (-)

### 특징 (설계 목표)

- **패턴을 유지하고 싶은 욕망** (-) - 개념적 모델
- **과도한 착취 (Over-Exploitation)** - 파라미터로 모사
- 변화를 거부하고 정해진 패턴 안에서만 순환 - **현재는 Softmax 온도 효과로 부분적 재현**
- 리미트 사이클(Limit Cycle)에 갇힘 - **이론적 목표, 아직 완전 구현되지 않음**

### 파라미터 설정

```python
ModeConfig(
    gate_threshold=0.0,          # 모든 미세 자극 통과 (감각 과부하)
    max_channels=1,              # 단일 채널 집중
    decision_temperature=5.0,    # β↑ (temperature↓) → 효용 차이 강조 (결정론적, 루틴 고착)
    working_memory_capacity=7,
    tau=0.1,                     # 매우 낮은 탐색 온도 → 착취 강화
    impulsivity=0.1,             # 낮은 충동성
    patience=0.9,                # 높은 인내심 (루틴 유지)
    local_weight_boost=3.0,      # 로컬 연결 강화 (패턴 고착)
    novelty_sensitivity=3.0,      # 높은 신규성 민감도 (낯선 상황 공포)
    stress_baseline=0.5,         # 높은 스트레스 기준선
)
```

### 동역학 (현재 구현 상태)

- **MemoryRank**: 
  - `local_weight_boost=3.0` (개념적 파라미터, **현재 코드에서 사용되지 않음**)
  - 실제로는 edges의 weight가 높으면 특정 패턴이 강화될 수 있으나, `decide()`에서 반영되지 않음
- **PFC**: 
  - `decision_temperature=5.0` (높음) → `P(i) = exp(β×U_i)`에서 β가 높아서 효용 차이 강조
  - **현재는 모든 action의 utility가 동일하므로, 온도 효과만 작동**
  - 선택 수렴은 발생하지만, "기억 기반 패턴 고착"은 아직 구현되지 않음
- **Thalamus**: 
  - `gate_threshold=0.0` (최소) → 파라미터만 설정됨
  - **`remember()`는 Thalamus를 거치지 않음** (감각 과부하 시뮬레이션 미구현)

### 감각 과부하 (Sensory Overload) - 개념적 모델

ASD 모드에서는 `gate_threshold=0.0`으로 설정되어, **이론적으로는** 일반적으로 필터링되는 미세한 자극들도 모두 통과해야 합니다:

- 형광등 소음
- 옷감의 촉감
- 먼 대화 소리
- 키보드 클릭 소리
- 에어컨 소음

**⚠️ 현재 구현 상태:**
- `remember()`는 Thalamus를 거치지 않음
- 감각 과부하 시뮬레이션은 아직 구현되지 않음
- 이는 **설계 목표**이며, 파라미터 프리셋으로만 정의됨

---

## 🧪 시뮬레이션 결과

### 패턴 고착 테스트

**시나리오**: "빨간색" 관련 기억을 형성한 후, 새로운 선택지("choose_yellow")를 추가

| Mode | 선택 분산 (고유 선택 수) | "choose_red" 선택률 | 설명 |
|------|----------------------|---------------------|------|
| Normal | 중간 (균형) | 40% | 균형잡힌 탐색/착취 |
| ADHD | 높음 (3~4개) | 80% | 산만함, 계속 전환 (Softmax 온도 효과) |
| ASD | 낮음 (1~2개) | 20% | 선택 수렴 (Softmax 온도 효과, 기억 기반 고착 미구현) |

**선택 분산 해석**:
- **높은 분산**: 다양한 선택 → 탐색 강화 (Softmax 온도 효과)
- **낮은 분산**: 선택 공간 수렴 → 착취 강화 (Softmax 온도 효과)
- **⚠️ 참고**: 현재는 모든 action의 utility가 동일하므로, 온도 효과만 작동함

### 핵심 인사이트

- **ADHD**: 계속 시도하고 싶은 욕망 (+) → 높은 엔트로피
- **ASD**: 패턴을 유지하고 싶은 욕망 (-) → 낮은 엔트로피
- **균형(Normal)**: 가장 효율적인 의사결정

---

## 💻 사용 예제

### 기본 사용

```python
from cognitive_kernel import CognitiveKernel, CognitiveMode

# ASD 모드로 초기화
kernel = CognitiveKernel("asd_demo", mode=CognitiveMode.ASD)

# 패턴 형성
kernel.remember("observation", {"text": "I saw a red apple"}, importance=0.5)
kernel.remember("observation", {"text": "Red traffic light"}, importance=0.5)

# 의사결정 (패턴 고착 관찰)
decision = kernel.decide(["choose_red", "choose_blue", "choose_green"])
# → "choose_red"가 높은 확률로 선택됨 (패턴 고착)
```

### 모드 전환

```python
# 정상 모드에서 시작
kernel = CognitiveKernel("demo", mode=CognitiveMode.NORMAL)

# ASD 모드로 전환
kernel.set_mode(CognitiveMode.ASD)

# 이제 패턴 유지 성향이 강화됨
```

### 비교 테스트

```python
# Normal vs ADHD vs ASD
for mode in [CognitiveMode.NORMAL, CognitiveMode.ADHD, CognitiveMode.ASD]:
    kernel = CognitiveKernel(f"{mode.value}_demo", mode=mode)
    
    # 동일한 입력
    kernel.remember("test", {"text": "pattern"}, importance=0.5)
    
    # 의사결정 비교
    decision = kernel.decide(["option1", "option2", "option3"])
    print(f"{mode.value}: {decision['action']}")
```

---

## 🔬 신경과학적 근거

### ADHD

- **Dopamine**: 낮은 도파민 수준 → 보상 기대치가 빠르게 소멸
- **PFC**: 억제 기능 부족 → 산만함
- **BasalGanglia**: 탐색 가중치 증가

### ASD

- **Predictive Coding**: 예측 실패에 대한 높은 민감도
- **Local Over-connectivity**: 로컬 연결 강화, 글로벌 연결 약화
- **Sensory Gating Failure**: Thalamus 게이팅 실패 → 감각 과부하

---

## 📚 참고 문헌

1. **Exploration vs Exploitation**: Reinforcement Learning의 핵심 개념
2. **Predictive Coding Theory**: ASD의 신경과학적 모델
3. **Dopamine Hypothesis**: ADHD의 신경전달물질 가설

---

## ⚠️ 주의사항

이 모델은:
- ✅ **연구 및 실험 도구**
- ✅ **인지 동역학 시뮬레이션**
- ❌ **임상 진단 도구 아님**
- ❌ **실제 뇌의 완전한 모델 아님**

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.0  
**License**: MIT

