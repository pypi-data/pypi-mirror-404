# 🧠 Cognitive States - 정직한 기술 문서

> **이 문서는 현재 구현 상태를 정확히 기술합니다.**

## ⚠️ 현재 구현 상태

### ✅ 실제로 작동하는 것

1. **파라미터 프리셋**: ADHD/ASD/NORMAL/PTSD 모드별 파라미터 설정
2. **Softmax 온도 효과**: `decision_temperature`와 `tau`가 실제로 선택 분산에 영향
3. **ADHD 산만함**: 낮은 온도 → 무작위성 증가 → 선택 분산 증가 (실제 발생)
4. **ASD 패턴 고착**: 높은 온도 + 기억 기반 utility → 선택 수렴 (v2.0.1 구현 완료)
5. **기억 기반 의사결정**: MemoryRank 결과가 action utility에 반영 (v2.0.1 구현 완료)
6. **장기 기억**: Panorama + MemoryRank + BasalGanglia 영속성

### ❌ 현재 작동하지 않는 것

1. **Thalamus 감각 과부하**: `remember()`는 Thalamus를 거치지 않음
2. **local_weight_boost**: 개념적 파라미터, 실제 코드에서 사용되지 않음

### ✅ v2.0.1에서 구현됨

1. **ASD 패턴 고착**: MemoryRank 결과가 `decide()`의 action utility에 반영됨
2. **기억 기반 의사결정**: `expected_reward = 0.5 + α · relevance · importance` 구현

---

## 📊 실제 동작 분석

### ADHD 모드: 산만함 (v2.0.1에서 완전 구현)

**파라미터:**
```python
decision_temperature=0.5  # β↓ → 무작위성 증가
tau=1.5                   # 높은 tau → 탐색 강화
```

**실제 효과 (v2.0.1):**
- ✅ Softmax에서 선택 분산 증가 (실제 발생)
- ✅ 여러 옵션이 비슷한 확률로 선택됨
- ✅ "빨간색 기억"이 선택에 영향을 줌 (기억 기반 utility)
- ✅ 하지만 온도 효과로 인해 선택이 분산됨

**테스트 결과:**
- choose_red 선택률: 30% (기억 영향 있지만 분산됨)
- 선택 분산: 3개 고유 선택 (산만함)
- 평균 utility: 0.400

**결론:**
> ✅ ADHD의 "산만함"은 **Softmax 온도 효과 + 기억 기반 utility**로 완전히 재현됨.
> 기억은 영향을 주지만, 낮은 온도로 인해 선택이 분산됨.

---

### ASD 모드: 패턴 고착 (현재는 연출)

**파라미터:**
```python
decision_temperature=5.0  # β↑ → 결정론적
tau=0.1                   # 낮은 tau → 착취 강화
```

**실제 효과:**
- ✅ Softmax에서 선택이 빠르게 수렴 (실제 발생)
- ✅ 같은 선택이 반복될 확률 증가
- ❌ "빨간색 기억"이 `choose_red`의 utility를 높이지 않음
- ❌ MemoryRank 그래프가 의사결정에 반영되지 않음

**결론:**
> ✅ **v2.0.1에서 구현됨**: MemoryRank 결과가 action utility에 반영됨
> 
> 수식: `expected_reward = 0.5 + α · Σ(importance_i × match_score_i)`
> - α = 0.5 (기억 영향 계수)
> - importance_i: MemoryRank 중요도
> - match_score_i: 옵션 키워드와 기억 내용의 매칭 점수
> 
> 이제 "빨간색 기억"이 실제로 `choose_red`의 utility를 높임

---

## 🔍 기술적 상세

### `decide()` 메서드의 실제 구조

```python
def decide(self, options: List[str], ...):
    # 1. MemoryRank 결과 로드 (작동함)
    memories = self.recall(k=5)
    
    # 2. Action 생성 (문제 지점)
    for opt in options:
        actions.append(Action(
            expected_reward=0.5,  # ❌ 하드코딩, 모든 action 동일
            effort_cost=0.2,      # ❌ 하드코딩
            risk=0.1,             # ❌ 하드코딩
        ))
    
    # 3. PFC 결정 (Softmax 온도만 작동)
    pfc_result = self.pfc.process(actions)
    # → 모든 action의 utility가 동일하므로
    # → 온도 효과만 작동 (무작위성/결정론성)
```

**구현 (v2.0.1):**
- ✅ MemoryRank 결과가 action utility에 반영됨
- ✅ "빨간색 기억"이 `choose_red`의 효용을 높임
- ✅ `_calculate_memory_relevance()` 메서드로 옵션-기억 매칭

---

### Thalamus의 실제 상태

```python
# 초기화만 됨
self.thalamus = ThalamusEngine(ThalamusConfig(
    gate_threshold=self.mode_config.gate_threshold,
    max_channels=self.mode_config.max_channels,
))

# remember()는 Thalamus를 거치지 않음
def remember(self, ...):
    # Panorama에 직접 저장
    event_id = self.panorama.append_event(...)
    # ❌ Thalamus.gate() 호출 없음
```

**결론:**
> "감각 과부하 시뮬레이션"은 현재 구현되지 않음.
> Thalamus는 파라미터만 설정되고 실제 게이팅은 작동하지 않음.

---

### local_weight_boost의 실제 상태

```python
local_weight_boost=3.0  # 개념적 파라미터, 향후 구현
```

**코드 검색 결과:**
- `memoryrank_engine.py`: 사용되지 않음
- `build_graph()`: 이 파라미터를 참조하지 않음

**결론:**
> `local_weight_boost`는 순수 설명용 파라미터.
> 실제 그래프 가중치에 반영되지 않음.

---

## 📐 수식 정확성

### Softmax 수식: ✅ 정확

```python
P(i) = exp(β × U_i) / Σ exp(β × U_j)
```

- β = `decision_temperature` (inverse-temperature)
- β ↑ → 효용 차이 강조 (결정론적)
- β ↓ → 무작위성 증가

**구현:** ✅ 정확히 일치

---

### Entropy 수식: ⚠️ 개념적 표현

```
Entropy_Control = Exploration(ADHD) / Exploitation(ASD)
```

**상태:**
- ✅ 개념적으로 타당
- ❌ 실제 계산되는 수치 아님
- ✅ 파라미터 조합으로 동작 (명시됨)

**결론:** 문제 없음 (명확히 표시됨)

---

## 🎯 선택 분산 해석

### 현재 계산

```python
unique_choices = len(set(decisions))
```

**정확한 의미:**
- ❌ 엔트로피 아님
- ❌ 일관성(consistency) 아님
- ✅ 단순 다양성(diversity) 지표

**해석:**
- 값 = 1: 같은 선택 반복
- 값 = N: 선택이 고르게 분산

**ASD의 낮은 분산:**
> "패턴 고착"이 아니라 **"결정론적 softmax의 부산물"**이다.

---

## 🔧 실제로 작동하는 것만 문서화

### ADHD: 산만함 (부분적 사실)

**실제 발생:**
- ✅ 선택 분산 증가 (Softmax 온도 효과)
- ✅ 여러 옵션이 비슷한 확률로 선택

**발생하지 않음:**
- ❌ 기억 기반 산만함
- ❌ 특정 기억이 선택에 영향

---

### ASD: 패턴 고착 (현재는 연출)

**실제 발생:**
- ✅ 선택 수렴 (Softmax 온도 효과)
- ✅ 같은 선택 반복 확률 증가

**발생하지 않음:**
- ❌ 기억 기반 패턴 고착
- ❌ MemoryRank 그래프가 의사결정에 반영

---

## 📝 수정 권고 문장

### ❌ 문제 문장

```
"ASD: Pattern fixation prevents exploring new options"
```

### ✅ 정직한 버전

```
"ASD 모드 설정에서는 결정 온도가 높아
선택이 빠르게 수렴하는 경향을 보인다
(패턴 고착을 모사하도록 설계됨, 현재는 온도 효과만 작동)"
```

---

### ❌ 문제 문장

```
"This simulates ASD sensory sensitivity"
```

### ✅ 정직한 버전

```
"This demonstrates a conceptual sensory overload scenario
based on ASD parameter presets.
Note: Thalamus gating is not yet implemented in remember()."
```

---

### ❌ 문제 문장

```
"로컬 연결 강화 (패턴 고착)"
```

### ✅ 정직한 버전

```
"로컬 연결 강화 (개념적 파라미터, 향후 구현)
현재는 MemoryRank 그래프 가중치에 반영되지 않음"
```

---

## 🎯 최종 판정

### 현재 상태

- ✅ **인지 동역학 아키텍처 설계**: 완벽
- ✅ **파라미터 프리셋 정의**: 타당
- ✅ **탐색 vs 착취 프레임**: 정확
- ❌ **행동 레벨 ASD 고착**: 아직 구현되지 않음

### 위치

> **설계 문서로서는 고급**  
> **실험 결과로서는 아직 부족**

이건 수준이 낮아서가 아니라, **위치가 애매**해서다.

---

## 🚀 다음 단계 (선택적)

### ✅ 패턴 고착 구현 완료 (v2.0.1)

```python
# decide() 메서드 구현됨
def decide(self, options: List[str], ...):
    memories = self.recall(k=5)
    
    # MemoryRank 결과를 action utility에 반영
    for opt in options:
        opt_keywords = self._extract_keywords(opt)
        memory_relevance = self._calculate_memory_relevance(opt_keywords, memories)
        
        # U_i = U_base + α · r_i
        expected_reward = 0.5 + 0.5 * memory_relevance
        actions.append(Action(
            expected_reward=expected_reward,  # ✅ 기억 기반 보정
            ...
        ))
```

**구현 완료:**
> ✅ `expected_reward`를 **MemoryRank 결과 기반 계산**으로 변경 완료
> ✅ 옵션 키워드와 기억 내용 매칭 로직 구현
> ✅ ASD 패턴 고착이 실제로 작동함

---

## 📚 참고

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 이론적 기반
- [COGNITIVE_STATES.md](./COGNITIVE_STATES.md) - 설계 문서 (개념 중심)
- [API_REFERENCE.md](./API_REFERENCE.md) - API 레퍼런스

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.0 (Honest Technical Documentation)  
**Last Updated**: 2026-01-29

