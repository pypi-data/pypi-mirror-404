# 🔄 동역학 엔진 모듈화 현황

> **현재 상태 및 엔진화 진행 방향**

**작성일**: 2026-01-31  
**버전**: v2.0.1+

---

## 📊 현재 상태

### ✅ 현재 구조

**동역학 로직의 위치:**

1. **파이프라인 단계로 분리됨** (`pipeline.py`)
   - `EntropyCalculationStep` - 엔트로피 계산
   - `CoreStrengthStep` - 코어 강도 계산 (Core Decay 포함)
   - `TorqueGenerationStep` - 회전 토크 생성

2. **상태는 core.py에 저장됨**
   - `_entropy_history` - 엔트로피 히스토리
   - `_precession_phi` - 회전 위상
   - `_core_strength_history` - 코어 강도 히스토리
   - `_persistent_core` - 지속 코어 강도 (Core Decay)
   - `_last_decay_time` - 마지막 감쇠 시간
   - `_cognitive_distress` - 인지적 절규 상태

3. **레거시 방식도 존재** (`_decide_legacy`)
   - 파이프라인을 사용하지 않을 때
   - 동역학 로직이 `decide()` 메서드 내부에 하드코딩됨

---

## 🎯 엔진화 진행 방향

### ❌ 현재: 엔진화 안 됨

**문제점:**
- 동역학 로직이 파이프라인 단계로만 분리됨
- 상태가 `core.py`에 직접 저장됨
- 독립적인 엔진 모듈이 없음
- 다른 프로젝트에서 재사용 불가

**현재 구조:**
```
core.py
├── _entropy_history (상태)
├── _precession_phi (상태)
├── _core_strength_history (상태)
├── _persistent_core (상태)
└── decide()
    └── pipeline.py
        ├── EntropyCalculationStep
        ├── CoreStrengthStep
        └── TorqueGenerationStep
```

---

### ✅ 목표: 독립적인 Dynamics Engine

**목표 구조:**
```
engines/
└── dynamics/
    ├── __init__.py
    ├── config.py (DynamicsConfig)
    ├── dynamics_engine.py (DynamicsEngine)
    └── models.py (DynamicsState)
```

**장점:**
- ✅ 독립적으로 사용 가능
- ✅ 다른 프로젝트에서 재사용 가능
- ✅ 상태 관리가 엔진 내부로 캡슐화
- ✅ 테스트 용이
- ✅ 업데이트 용이

---

## 🔧 엔진화 계획

### Phase 1: Dynamics Engine 생성

**파일 구조:**
```
src/cognitive_kernel/engines/dynamics/
├── __init__.py
├── config.py
├── dynamics_engine.py
└── models.py
```

**DynamicsConfig:**
```python
@dataclass
class DynamicsConfig:
    """동역학 엔진 설정"""
    base_gamma: float = 0.3  # 기본 회전 토크 세기
    omega: float = 0.05  # 세차 속도
    core_decay_rate: float = 0.0  # 코어 감쇠율
    memory_update_failure: float = 0.0  # 새 기억 반영 실패율
    loop_integrity_decay: float = 0.0  # 루프 무결성 감쇠율
    entropy_threshold: float = 0.8  # 인지적 절규 임계값
    core_distress_threshold: float = 0.3  # 코어 절규 임계값
```

**DynamicsState:**
```python
@dataclass
class DynamicsState:
    """동역학 상태"""
    entropy: float = 0.0
    core_strength: float = 0.0
    precession_phi: float = 0.0
    persistent_core: Optional[float] = None
    last_decay_time: Optional[float] = None
    cognitive_distress: bool = False
    entropy_history: List[float] = field(default_factory=list)
    core_strength_history: List[float] = field(default_factory=list)
```

**DynamicsEngine:**
```python
class DynamicsEngine:
    """동역학 엔진"""
    
    def __init__(self, config: DynamicsConfig):
        self.config = config
        self.state = DynamicsState()
    
    def calculate_entropy(self, probabilities: List[float]) -> float:
        """엔트로피 계산"""
        pass
    
    def calculate_core_strength(
        self,
        memories: List[Dict],
        memory_update_failure: float = 0.0,
    ) -> float:
        """코어 강도 계산 (Core Decay 포함)"""
        pass
    
    def generate_torque(
        self,
        options: List[str],
        entropy: float,
        mode: CognitiveMode,
    ) -> Dict[str, float]:
        """회전 토크 생성"""
        pass
    
    def update_precession(self):
        """위상 업데이트"""
        pass
    
    def check_cognitive_distress(
        self,
        entropy: float,
        core_strength: float,
        num_options: int,
    ) -> Tuple[bool, str]:
        """인지적 절규 확인"""
        pass
```

---

### Phase 2: Pipeline Step과 통합

**변경 사항:**
```python
# pipeline.py
class EntropyCalculationStep(PipelineStep):
    def __init__(self, dynamics_engine):
        self.dynamics_engine = dynamics_engine
    
    def process(self, context):
        context.entropy = self.dynamics_engine.calculate_entropy(
            context.probabilities
        )
        return context

class CoreStrengthStep(PipelineStep):
    def __init__(self, dynamics_engine, kernel):
        self.dynamics_engine = dynamics_engine
        self.kernel = kernel
    
    def process(self, context):
        context.core_strength = self.dynamics_engine.calculate_core_strength(
            context.memories,
            self.kernel.mode_config.memory_update_failure,
        )
        # 인지적 절규 확인
        distress, message = self.dynamics_engine.check_cognitive_distress(
            context.entropy,
            context.core_strength,
            len(context.options),
        )
        context.metadata["cognitive_distress"] = distress
        context.metadata["distress_message"] = message
        return context

class TorqueGenerationStep(PipelineStep):
    def __init__(self, dynamics_engine, mode):
        self.dynamics_engine = dynamics_engine
        self.mode = mode
    
    def process(self, context):
        context.auto_torque = self.dynamics_engine.generate_torque(
            context.options,
            context.entropy,
            self.mode,
        )
        # 위상 업데이트
        self.dynamics_engine.update_precession()
        context.metadata["precession_phi"] = self.dynamics_engine.state.precession_phi
        return context
```

---

### Phase 3: core.py 통합

**변경 사항:**
```python
# core.py
class CognitiveKernel:
    def __init__(self, ...):
        # ...
        # Dynamics Engine 초기화
        from .engines.dynamics import DynamicsEngine, DynamicsConfig
        dynamics_config = DynamicsConfig(
            base_gamma=0.3,
            omega=0.05,
            core_decay_rate=self.mode_config.core_decay_rate,
            memory_update_failure=self.mode_config.memory_update_failure,
            loop_integrity_decay=self.mode_config.loop_integrity_decay,
        )
        self.dynamics = DynamicsEngine(dynamics_config)
        
        # 기존 상태 변수 제거
        # self._entropy_history → self.dynamics.state.entropy_history
        # self._precession_phi → self.dynamics.state.precession_phi
        # ...
```

---

## 📈 현재 vs 목표 비교

### 현재 구조

```
core.py (통합)
├── 상태 변수 (5개)
├── decide()
└── pipeline.py
    └── 단계들 (로직만 분리)
```

**문제점:**
- ❌ 상태가 core.py에 흩어져 있음
- ❌ 독립 사용 불가
- ❌ 재사용 불가

---

### 목표 구조

```
core.py (통합 레이어)
└── engines/
    └── dynamics/
        ├── DynamicsEngine (상태 + 로직)
        ├── DynamicsConfig
        └── DynamicsState
```

**장점:**
- ✅ 상태가 엔진 내부로 캡슐화
- ✅ 독립 사용 가능
- ✅ 재사용 가능
- ✅ 테스트 용이

---

## 🚀 진행 단계

### Step 1: Dynamics Engine 생성 (2-3시간)

1. `engines/dynamics/` 디렉토리 생성
2. `DynamicsConfig` 정의
3. `DynamicsState` 정의
4. `DynamicsEngine` 기본 구조 생성

### Step 2: 로직 이전 (2-3시간)

1. `EntropyCalculationStep` 로직 → `DynamicsEngine.calculate_entropy()`
2. `CoreStrengthStep` 로직 → `DynamicsEngine.calculate_core_strength()`
3. `TorqueGenerationStep` 로직 → `DynamicsEngine.generate_torque()`
4. 인지적 절규 로직 → `DynamicsEngine.check_cognitive_distress()`

### Step 3: 상태 이전 (1-2시간)

1. `core.py`의 상태 변수 → `DynamicsEngine.state`
2. 상태 접근 경로 변경
3. 히스토리 관리 로직 이전

### Step 4: Pipeline Step 업데이트 (1시간)

1. Pipeline Step들이 `DynamicsEngine` 사용하도록 변경
2. 상태 접근 경로 변경

### Step 5: core.py 통합 (1시간)

1. `DynamicsEngine` 초기화
2. 기존 상태 변수 제거
3. 레거시 방식도 `DynamicsEngine` 사용하도록 변경

---

## 📝 현재 진행 상황

### ✅ 완료된 부분

1. **파이프라인 단계로 로직 분리** - 완료
2. **Core Decay 수식 구현** - 완료
3. **인지적 절규 메커니즘** - 완료

### ⚠️ 부분 완료

1. **로직 분리** - 완료 (파이프라인 단계로)
2. **상태 관리** - 미완료 (core.py에 남아있음)

### ❌ 미완료

1. **독립 엔진 모듈** - 미완료
2. **상태 캡슐화** - 미완료
3. **재사용 가능성** - 미완료

---

## 🎯 결론

### 현재 상태

**동역학 로직은 파이프라인 단계로 분리되었지만, 독립적인 엔진 모듈은 아직 생성되지 않았습니다.**

**구조:**
- ✅ 로직: 파이프라인 단계로 분리됨
- ❌ 상태: core.py에 남아있음
- ❌ 엔진: 독립 모듈 없음

### 다음 단계

**Dynamics Engine을 독립 모듈로 생성하여:**
1. 상태와 로직을 모두 캡슐화
2. 다른 프로젝트에서 재사용 가능하게
3. 테스트 용이하게

**예상 시간:** 6-9시간

---

**마지막 업데이트**: 2026-01-31

