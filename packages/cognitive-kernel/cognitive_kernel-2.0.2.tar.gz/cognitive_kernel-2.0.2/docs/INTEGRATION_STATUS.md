# ✅ Cognitive Modes 통합 상태 (v2.0.1)

## 📊 통합 완료 상태

### 모든 모드 통합 완료

| 모드 | 상태 | 기억 기반 의사결정 | 특징 |
|------|------|-------------------|------|
| **NORMAL** | ✅ 완료 | ✅ 작동 | 균형잡힌 탐색/착취 |
| **ADHD** | ✅ 완료 | ✅ 작동 | 산만함 (높은 선택 분산) |
| **ASD** | ✅ 완료 | ✅ 작동 | 패턴 고착 (낮은 선택 분산) |
| **PTSD** | ✅ 완료 | ✅ 작동 | 트라우마 고착 |

---

## 🧪 테스트 결과 (v2.0.1)

### 동일한 기억으로 테스트

**기억:**
- "I saw a red apple" (importance: 0.8)
- "Red traffic light stopped me" (importance: 0.7)
- "Red sunset was beautiful" (importance: 0.6)

**결과:**

| 모드 | choose_red 선택률 | 선택 분산 | 평균 utility | 특징 |
|------|------------------|-----------|--------------|------|
| **ADHD** | 30% | 3개 고유 선택 | 0.400 | 산만함 + 기억 영향 |
| **ASD** | 90% | 2개 고유 선택 | 0.700 | 패턴 고착 + 기억 영향 |

**해석:**
- ✅ **ADHD**: 기억은 영향을 주지만, 낮은 온도(β=0.5)로 인해 선택이 분산됨
- ✅ **ASD**: 기억 영향 + 높은 온도(β=5.0)로 인해 선택이 수렴됨

---

## 🔧 구현 내용

### 1. 모드 정의 (cognitive_modes.py)

```python
class CognitiveMode(Enum):
    NORMAL = "normal"
    ADHD = "adhd"    # 고엔트로피: 과도한 탐색
    ASD = "asd"      # 저엔트로피: 과도한 착취
    PTSD = "ptsd"    # 트라우마 고착
```

### 2. 파라미터 프리셋

각 모드별로 엔진 파라미터가 자동 설정:

```python
# ADHD 모드
decision_temperature=0.5  # β↓ → 무작위성 증가
tau=1.5                   # 높은 tau → 탐색 강화
gate_threshold=0.1         # 낮은 임계값 → 산만함

# ASD 모드
decision_temperature=5.0   # β↑ → 결정론적
tau=0.1                    # 낮은 tau → 착취 강화
gate_threshold=0.0         # 모든 입력 통과
```

### 3. 기억 기반 의사결정 (v2.0.1)

```python
# decide() 메서드
expected_reward = 0.5 + alpha * memory_relevance
# alpha = 0.5 (기억 영향 계수)
# memory_relevance = Σ(importance_i × match_score_i)
```

**모든 모드에서 작동:**
- ✅ NORMAL: 균형잡힌 기억 반영
- ✅ ADHD: 기억 영향 + 선택 분산
- ✅ ASD: 기억 영향 + 선택 수렴
- ✅ PTSD: 트라우마 기억 강화

---

## 🎯 핵심 성과

### Before (v2.0.0)
- ❌ 모든 action의 expected_reward = 0.5 (하드코딩)
- ❌ MemoryRank 결과가 의사결정에 반영되지 않음
- ❌ ASD 패턴 고착은 "연출" (온도 효과만)

### After (v2.0.1)
- ✅ 기억 기반 expected_reward 계산
- ✅ MemoryRank 결과가 의사결정에 반영됨
- ✅ ASD 패턴 고착이 실제로 작동함
- ✅ ADHD 산만함도 기억 영향 받음

---

## 📐 수식 정리

### 기억 기반 Utility 계산

$$
U_i = U_{base} + \alpha \cdot \sum_{j} (r_j \times m_{ij})
$$

- $U_i$: action $i$의 최종 utility
- $U_{base}$: 기본 utility (0.5)
- $\alpha$: 기억 영향 계수 (0.5)
- $r_j$: 기억 $j$의 MemoryRank 중요도
- $m_{ij}$: action $i$와 기억 $j$의 매칭 점수

### Softmax 선택 확률

$$
P(i) = \frac{\exp(\beta \times U_i)}{\sum_j \exp(\beta \times U_j)}
$$

- $\beta$: `decision_temperature` (inverse-temperature)
- $\beta \uparrow$ (온도 $\downarrow$): 효용 차이 강조 (결정론적)
- $\beta \downarrow$ (온도 $\uparrow$): 무작위성 증가 (탐색 강화)

---

## 🚀 사용 예시

### 모드별 사용

```python
from cognitive_kernel import CognitiveKernel, CognitiveMode

# ADHD 모드
kernel_adhd = CognitiveKernel("adhd_demo", mode=CognitiveMode.ADHD)
kernel_adhd.remember("observation", {"text": "I saw a red apple"}, importance=0.8)
decision = kernel_adhd.decide(["choose_red", "choose_blue", "choose_green"])
# → 선택 분산 높음 (산만함)

# ASD 모드
kernel_asd = CognitiveKernel("asd_demo", mode=CognitiveMode.ASD)
kernel_asd.remember("observation", {"text": "I saw a red apple"}, importance=0.8)
decision = kernel_asd.decide(["choose_red", "choose_blue", "choose_green"])
# → choose_red 선택률 높음 (패턴 고착)
```

### 모드 전환

```python
kernel = CognitiveKernel("demo", mode=CognitiveMode.NORMAL)
# ... 작업 ...

# ASD 모드로 전환
kernel.set_mode(CognitiveMode.ASD)
# → 이제 패턴 고착 성향이 강화됨
```

---

## ✅ 완료 체크리스트

- [x] 모든 모드 정의 (NORMAL, ADHD, ASD, PTSD)
- [x] 파라미터 프리셋 구현
- [x] CognitiveKernel에 모드 통합
- [x] set_mode() 메서드 구현
- [x] 기억 기반 의사결정 구현 (v2.0.1)
- [x] 모든 모드에서 기억 기반 의사결정 작동 확인
- [x] ADHD vs ASD 차이 검증
- [x] 문서화 완료

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.1  
**Last Updated**: 2026-01-30

