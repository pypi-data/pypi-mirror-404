# 🔍 Cognitive Kernel v2.0.1 작업 분석 문서

> **작업 범위 및 구현 계획 상세 분석**

**작성일**: 2026-01-31  
**분석자**: AI Assistant  
**버전**: 2.0.1

---

## 📋 작업 개요

인수인계 문서에 명시된 **5개 우선순위 그룹, 총 8개 작업**을 정확히 파악하고 구현 계획을 수립합니다.

---

## 🎯 우선순위 1: API 개선

### 작업 1.1: 전체 확률 분포 접근

**현재 상태:**
- `decide()` 메서드는 `pfc_result.selection_probability`만 반환 (단일 선택 확률)
- PFC 엔진의 `softmax_probabilities()`는 모든 확률을 계산하지만, `select_action()`에서는 선택된 것만 반환
- 세차운동 데모에서 각 옵션마다 `decide()`를 반복 호출해야 함 (비효율적)

**문제점:**
```python
# 현재 decide() 반환값
{
    "action": "choose_red",
    "utility": 0.7,
    "probability": 0.45,  # 단일 선택 확률만
    "habit_suggestion": None,
    "conflict": False,
}
```

**해결 방안:**
1. `decide()` 메서드에서 모든 옵션에 대한 확률을 계산
2. PFC 엔진의 `softmax_probabilities()` 결과를 반환값에 추가
3. 반환값 구조 확장

**구현 위치:**
- `src/cognitive_kernel/core.py` - `decide()` 메서드 (281-357줄)

**구현 세부사항:**
```python
def decide(...) -> Dict[str, Any]:
    # ... 기존 코드 ...
    
    # PFC 결정
    pfc_result = self.pfc.process(actions)
    
    # 전체 확률 분포 계산 (NEW)
    utilities = [self.pfc.evaluate_action(a) for a in actions]
    probabilities = self.pfc.softmax_probabilities(utilities)
    probability_distribution = {
        opt: prob for opt, prob in zip(options, probabilities)
    }
    
    return {
        "action": pfc_result.action.name if pfc_result.action else None,
        "utility": pfc_result.utility,
        "probability": pfc_result.selection_probability,
        "probability_distribution": probability_distribution,  # NEW
        "habit_suggestion": habit_action,
        "conflict": ...,
    }
```

**예상 시간:** 2-3시간

---

### 작업 1.2: 공개 API 정리

**현재 상태:**
- `_extract_keywords()`: 내부 메서드 (379-392줄)
- `_calculate_memory_relevance()`: 내부 메서드 (394-435줄)
- 데모 코드에서 직접 호출 (`stability_core_demo.py`, `precession_demo.py`)

**문제점:**
- 내부 메서드(`_` prefix)를 외부에서 호출하는 것은 규약 위반
- API 안정성 저하 (내부 구현 변경 시 데모 코드 깨짐)

**해결 방안:**
1. `_extract_keywords()` → `extract_keywords()` (공개 메서드)
2. `_calculate_memory_relevance()` → `calculate_memory_relevance()` (공개 메서드)
3. 기존 내부 메서드는 새 공개 메서드를 호출하도록 변경 (하위 호환성)

**구현 위치:**
- `src/cognitive_kernel/core.py` - 두 메서드 모두

**구현 세부사항:**
```python
def extract_keywords(self, option_name: str) -> List[str]:
    """
    옵션 이름에서 키워드 추출 (공개 API)
    
    Args:
        option_name: 옵션 이름 (예: "choose_red", "work_on_project")
        
    Returns:
        키워드 리스트 (예: ["red"], ["work", "project"])
    """
    # 기존 _extract_keywords() 로직
    ...

def calculate_memory_relevance(
    self,
    option: str,
    memories: Optional[List[Dict]] = None,
) -> float:
    """
    옵션과 기억의 관련성 계산 (공개 API)
    
    Args:
        option: 옵션 이름
        memories: 기억 리스트 (None이면 recall() 자동 호출)
        
    Returns:
        관련성 점수 (0~1)
    """
    if memories is None:
        memories = self.recall(k=self.config.working_memory_capacity)
    
    opt_keywords = self.extract_keywords(option)
    return self._calculate_memory_relevance(opt_keywords, memories)
```

**예상 시간:** 1-2시간

---

## 🎯 우선순위 2: 엔진 통합 완성

### 작업 2.1: Thalamus 게이팅 루프

**현재 상태:**
- Thalamus 엔진은 초기화되지만 `remember()` 경로에서 사용되지 않음
- `remember()` 메서드는 입력을 바로 Panorama에 저장 (194-243줄)

**문제점:**
- 입력 필터링이 없어 모든 입력이 저장됨
- 인지 모드의 `gate_threshold`, `max_channels` 설정이 무시됨

**해결 방안:**
1. `remember()`에서 입력을 `SensoryInput`으로 변환
2. Thalamus의 `filter_single()` 메서드로 필터링
3. 필터링된 결과만 Panorama에 저장

**구현 위치:**
- `src/cognitive_kernel/core.py` - `remember()` 메서드

**구현 세부사항:**
```python
def remember(self, ...) -> Optional[str]:
    """
    기억 저장 (Thalamus 게이팅 통합)
    
    Returns:
        생성된 기억 ID (게이트 통과 시) 또는 None (차단 시)
    """
    from .engines.thalamus.data_types import SensoryInput, ModalityType
    
    # Thalamus 게이팅
    sensory_input = SensoryInput(
        content={"event_type": event_type, **content} if content else {"event_type": event_type},
        modality=ModalityType.SEMANTIC,  # 텍스트 기반 기억
        intensity=importance,
        salience=emotion,  # 감정 = 현저성
    )
    
    filtered = self.thalamus.filter_single(
        content=sensory_input.content,
        modality=sensory_input.modality,
        intensity=sensory_input.intensity,
        salience=sensory_input.salience,
    )
    
    # 게이트 통과하지 못하면 None 반환
    if filtered is None or not filtered.passed_gate:
        return None
    
    # 게이트 통과한 경우만 Panorama에 저장
    timestamp = time.time()
    event_id = self.panorama.append_event(...)
    ...
    
    return event_id
```

**주의사항:**
- Thalamus는 `energy_provider`를 받을 수 있음 (Hypothalamus 연결)
- `remember()`에서 `self.hypothalamus`를 Thalamus에 연결해야 할 수도 있음

**예상 시간:** 3-4시간

---

### 작업 2.2: Hypothalamus 통합

**현재 상태:**
- Hypothalamus 엔진은 초기화되지만 `decide()`의 utility 계산에 반영되지 않음
- 에너지/스트레스가 의사결정에 영향 없음

**문제점:**
- 에너지가 낮아도 모든 행동을 동일하게 평가
- 스트레스가 높아도 위험한 행동을 선택할 수 있음

**해결 방안:**
1. `decide()`에서 Hypothalamus 상태 조회
2. 에너지/스트레스를 utility 계산에 반영
3. 에너지 부족 시 에너지 소모 행동에 패널티
4. 스트레스 높을 때 위험 행동에 패널티

**구현 위치:**
- `src/cognitive_kernel/core.py` - `decide()` 메서드

**구현 세부사항:**
```python
def decide(self, ...) -> Dict[str, Any]:
    # ... 기존 코드 ...
    
    # Hypothalamus 상태 조회
    energy_state = self.hypothalamus.get_energy_state()
    energy = energy_state['energy']
    stress = self.hypothalamus.state.stress
    
    # Action 생성 (Hypothalamus 패널티 반영)
    actions = []
    for i, opt in enumerate(options):
        # ... 기존 memory_relevance 계산 ...
        expected_reward = 0.5 + alpha * memory_relevance
        
        # Hypothalamus 패널티 (NEW)
        # 에너지 부족 시 에너지 소모 행동에 패널티
        energy_cost = 0.0
        if energy < 0.3:  # 에너지 부족
            # "work", "exercise" 같은 에너지 소모 행동 감지
            if any(word in opt.lower() for word in ['work', 'exercise', 'run', 'active']):
                energy_cost = (0.3 - energy) * 0.5  # 에너지 부족 정도에 비례
        
        # 스트레스 높을 때 위험 행동에 패널티
        stress_penalty = 0.0
        if stress > 0.7:  # 스트레스 높음
            # "risk", "danger" 같은 위험 행동 감지
            if any(word in opt.lower() for word in ['risk', 'danger', 'challenge', 'fight']):
                stress_penalty = (stress - 0.7) * 0.3
        
        # 최종 utility
        expected_reward = expected_reward - energy_cost - stress_penalty
        
        # 외부 토크 주입
        if external_torque and opt in external_torque:
            expected_reward += external_torque[opt]
        
        actions.append(self._Action(...))
    
    # ... 나머지 코드 ...
```

**예상 시간:** 2-3시간

---

### 작업 2.3: 습관 덮어쓰기

**현재 상태:**
- `decide()`에서 `habit_suggestion`과 `conflict` flag만 반환
- 습관 강도가 아무리 높아도 PFC 결정을 덮어쓰지 않음

**문제점:**
- 습관화된 행동이 있어도 항상 PFC 결정이 우선
- 생물학적으로는 습관이 강하면 PFC를 우회함

**해결 방안:**
1. `decide()`에서 습관 강도 확인
2. 임계값(예: 0.7)을 넘으면 습관 행동 반환
3. `CognitiveConfig`에 `habit_override_threshold` 추가

**구현 위치:**
- `src/cognitive_kernel/core.py` - `decide()` 메서드, `CognitiveConfig` 클래스

**구현 세부사항:**
```python
# CognitiveConfig에 추가
@dataclass
class CognitiveConfig:
    ...
    habit_override_threshold: float = 0.7  # 습관 강도 임계값

def decide(self, ...) -> Dict[str, Any]:
    # ... 기존 코드 ...
    
    # 습관 체크 (NEW)
    habit_action = None
    habit_strength = 0.0
    if use_habit and context:
        # BasalGanglia에서 습관 행동 조회
        habit_result = self.basal_ganglia.select_action(context, options)
        if habit_result.action and habit_result.action.is_habit:
            habit_action = habit_result.action.name
            habit_strength = habit_result.action.habit_strength
    
    # 습관 덮어쓰기 (NEW)
    if habit_strength > self.config.habit_override_threshold:
        return {
            "action": habit_action,
            "source": "habit_override",
            "habit_strength": habit_strength,
            "utility": 0.0,  # 습관은 utility 계산 없음
            "probability": 1.0,  # 습관은 확률 1.0
            "probability_distribution": {opt: 1.0 if opt == habit_action else 0.0 for opt in options},
        }
    
    # PFC 결정 (기존 로직)
    pfc_result = self.pfc.process(actions)
    ...
```

**주의사항:**
- BasalGanglia의 `select_action()`은 `ActionResult`를 반환
- `ActionResult.action`이 `Action` 객체이고, `Action.is_habit`과 `Action.habit_strength` 속성 있음

**예상 시간:** 2-3시간

---

## 🎯 우선순위 3: MemoryRank 개선

### 작업 3.1: `local_weight_boost` 구현

**현재 상태:**
- `local_weight_boost`는 `ModeConfig`에 파라미터로만 존재 (54줄)
- 실제 MemoryRank 엔진에서 사용되지 않음
- 주석: "개념적 파라미터, 향후 구현"

**문제점:**
- ASD 모드에서 `local_weight_boost=3.0`으로 설정되어 있지만 효과 없음
- 로컬 연결 강화가 실제로 작동하지 않음

**해결 방안:**
1. "로컬 연결" 정의 필요
   - 시간적 근접성: 같은 시간대에 저장된 기억
   - 공간적 근접성: 같은 이벤트 타입
   - 그래프 구조적 근접성: 짧은 경로로 연결된 노드
2. `build_graph()`에서 엣지 가중치 계산 시 `local_weight_boost` 적용
3. `MemoryRankConfig`에 `local_weight_boost` 추가

**구현 위치:**
- `src/cognitive_kernel/engines/memoryrank/memoryrank_engine.py` - `build_graph()` 메서드
- `src/cognitive_kernel/engines/memoryrank/config.py` - `MemoryRankConfig` 클래스
- `src/cognitive_kernel/core.py` - `_init_engines()` 메서드 (MemoryRankConfig 전달)

**구현 세부사항:**
```python
# MemoryRankConfig에 추가
@dataclass
class MemoryRankConfig:
    ...
    local_weight_boost: float = 1.0  # 로컬 연결 가중치 부스트

# memoryrank_engine.py의 build_graph() 수정
def build_graph(self, edges, node_attributes):
    # ... 기존 코드 ...
    
    # 가중치 행렬 W[i, j] = j -> i 로의 weight
    W = np.zeros((n, n), dtype=float)
    for src, dst, w in edges:
        if w <= 0:
            continue
        if src not in self._id_to_index or dst not in self._id_to_index:
            continue
        i = self._id_to_index[dst]
        j = self._id_to_index[src]
        
        base_weight = float(w)
        
        # 로컬 연결 강화 (NEW)
        if self.config.local_weight_boost > 1.0:
            if self._is_local_connection(src, dst, node_attributes):
                base_weight *= self.config.local_weight_boost
        
        W[i, j] += base_weight
    
    # ... 나머지 코드 ...

def _is_local_connection(
    self,
    node1_id: str,
    node2_id: str,
    node_attributes: Optional[Dict[str, MemoryNodeAttributes]],
) -> bool:
    """
    로컬 연결 여부 판단
    
    정의:
    - 같은 이벤트 타입 (Panorama에서 확인 필요)
    - 시간적 근접성 (같은 세션, 비슷한 시간대)
    - 또는 그래프 구조적 근접성 (직접 연결)
    
    현재는 간단히: 직접 연결된 엣지만 로컬로 간주
    향후: Panorama 이벤트 정보를 활용해 더 정교하게 판단
    """
    # 간단한 구현: 직접 연결된 엣지는 로컬
    # 향후: Panorama 이벤트 타입, 타임스탬프 비교
    return True  # 일단 모든 연결을 로컬로 간주
```

**주의사항:**
- "로컬 연결"의 정의가 명확하지 않음
- Panorama 이벤트 정보에 접근하려면 `core.py`에서 정보 전달 필요
- 현재는 간단한 구현으로 시작, 향후 개선 가능

**예상 시간:** 4-5시간

---

## 🎯 우선순위 4: 데모 코드 정리

### 작업 4.1: 규약 준수 데모 작성

**현재 상태:**
- `stability_core_demo.py`: 내부 메서드 직접 호출 (규약 위반)
- `precession_demo.py`: 내부 메서드 직접 호출 (규약 위반)
- `precession_demo_v2.py`: 규약 준수 (참고용)

**규약:**
1. `kernel.decide()` 직접 사용
2. 세션 격리 (uuid 기반)
3. 공개 API만 사용
4. CONFIG로 파라미터화

**해결 방안:**
1. `stability_core_demo.py`를 `stability_core_demo_v2.py`로 재작성
2. `precession_demo.py`를 `precession_demo_v2.py`로 교체 (이미 존재하므로 삭제 또는 업데이트)
3. 내부 메서드 호출 제거, 공개 API만 사용

**구현 위치:**
- `examples/stability_core_demo.py` → `examples/stability_core_demo_v2.py`
- `examples/precession_demo.py` → 삭제 또는 업데이트

**예상 시간:** 3-4시간

---

## 🎯 우선순위 5: 테스트 및 검증

### 작업 5.1: 통합 테스트
### 작업 5.2: 성능 벤치마크

**현재 상태:**
- `tests/` 디렉토리 존재
- 통합 테스트 없음

**예상 시간:** 4-5시간 (통합 테스트) + 2-3시간 (벤치마크)

---

## 📊 작업 우선순위 요약

| 우선순위 | 작업 | 예상 시간 | 복잡도 |
|---------|------|----------|--------|
| 1.1 | 전체 확률 분포 접근 | 2-3h | 낮음 |
| 1.2 | 공개 API 정리 | 1-2h | 낮음 |
| 2.1 | Thalamus 게이팅 루프 | 3-4h | 중간 |
| 2.2 | Hypothalamus 통합 | 2-3h | 중간 |
| 2.3 | 습관 덮어쓰기 | 2-3h | 중간 |
| 3.1 | local_weight_boost 구현 | 4-5h | 높음 |
| 4.1 | 데모 코드 정리 | 3-4h | 낮음 |
| 5.1-5.2 | 테스트 및 검증 | 6-8h | 중간 |

**총 예상 시간:** 23-32시간

---

## 🔧 구현 시 주의사항

### 1. 하위 호환성
- 기존 API 변경 시 하위 호환성 유지
- 내부 메서드를 공개 API로 전환할 때 기존 코드가 깨지지 않도록 주의

### 2. 테스트
- 각 작업 완료 후 해당 기능 테스트
- 통합 테스트로 전체 파이프라인 검증

### 3. 문서화
- 새로운 API 추가 시 docstring 작성
- 인수인계 문서 업데이트

### 4. PHAM 블록체인 서명
- 엔진 모듈 수정 시 PHAM 서명 필요 (메모리 참조)

---

## ✅ 다음 단계

1. **우선순위 1부터 순차적으로 진행**
2. **각 작업 완료 후 테스트 및 검증**
3. **인수인계 문서 업데이트**
4. **PHAM 서명 (필요 시)**

---

**마지막 업데이트**: 2026-01-31

