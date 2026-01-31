# 🧠 뇌 질환 스펙트럼 분석: 붕괴와 루프 사이

> **현재 구현 상태, 붕괴-루프 스펙트럼, 확장성 분석**

**작성일**: 2026-01-31  
**버전**: v2.0.1+

---

## 📊 현재 구현된 질환 (10개)

### ✅ 완전 구현된 질환

| 질환 | Enum | Preset 메서드 | 상태 |
|------|------|---------------|------|
| NORMAL | ✅ | `normal()` | ✅ 완료 |
| ADHD | ✅ | `adhd()` | ✅ 완료 |
| ASD | ✅ | `asd()` | ✅ 완료 |
| PTSD | ✅ | `ptsd()` | ✅ 완료 |
| PANIC | ✅ | `panic()` | ✅ 완료 |
| EPILEPSY | ✅ | `epilepsy()` | ✅ 완료 |
| OCD | ✅ | `ocd()` | ✅ 완료 |
| IED | ✅ | `ied()` | ✅ 완료 |
| DEPRESSION | ✅ | `depression()` | ✅ 완료 |
| BIPOLAR | ✅ | `bipolar_mania()` / `bipolar_depression()` | ⚠️ 부분 완료 |

---

## 🗺️ ADHD(+) ↔ ASD(-) 스펙트럼 매핑

### 극단 위치

```
ADHD (+) ──────────────────────────────────────── ASD (-)
고엔트로피, 발산                                    저엔트로피, 수렴
탐색 (Exploration)                                착취 (Exploitation)
```

### 질환 배치

#### ADHD(+) 극단 쪽 (고엔트로피, 발산)
1. **EPILEPSY** (간질)
   - 위치: ADHD(+) 극단에 가까움
   - 특징: 극도의 불안정, 발작
   - 파라미터: `tau=2.0`, `impulsivity=0.9`, `decision_temperature=0.4`

2. **IED** (분노조절장애)
   - 위치: ADHD(+) 쪽
   - 특징: 극도의 충동성, 폭발적 분노
   - 파라미터: `tau=2.5`, `impulsivity=0.95`, `decision_temperature=0.3`

3. **ADHD** (주의력결핍 과잉행동장애)
   - 위치: ADHD(+) 극
   - 특징: 과도한 탐색, 산만
   - 파라미터: `tau=1.5`, `impulsivity=0.8`, `decision_temperature=0.5`

4. **PANIC** (공황장애)
   - 위치: ADHD(+) 쪽, 높은 불안 차원
   - 특징: 과각성, 높은 불안
   - 파라미터: `tau=1.2`, `impulsivity=0.7`, `stress_baseline=0.8`

#### 중간 영역
5. **PTSD** (외상후 스트레스 장애)
   - 위치: 중간, 높은 불안 차원
   - 특징: 트라우마 고착, 과각성
   - 파라미터: `tau=0.3`, `damping=0.9`, `stress_baseline=0.7`

6. **BIPOLAR** (양극성 장애)
   - 위치: ADHD ↔ ASD 사이를 동적으로 이동
   - 특징: 조증(ADHD 쪽) ↔ 우울(ASD 쪽) 전환
   - 파라미터: 
     - 조증: `tau=3.0`, `impulsivity=0.9`
     - 우울: `tau=0.2`, `impulsivity=0.2`

#### ASD(-) 극단 쪽 (저엔트로피, 수렴)
7. **OCD** (강박)
   - 위치: ASD(-) 쪽, 높은 불안 차원
   - 특징: 고착, 반복 행동, 패턴 고착
   - 파라미터: `tau=0.05`, `decision_temperature=6.0`, `local_weight_boost=4.0`

8. **DEPRESSION** (우울증)
   - 위치: ASD(-) 쪽
   - 특징: 무기력, 고착, 낮은 에너지
   - 파라미터: `tau=0.3`, `decision_temperature=2.0`, `novelty_sensitivity=0.5`

9. **ASD** (자폐 스펙트럼 장애)
   - 위치: ASD(-) 극
   - 특징: 과도한 착취, 패턴 고착
   - 파라미터: `tau=0.1`, `decision_temperature=5.0`, `local_weight_boost=3.0`

---

## 🔄 붕괴와 루프 사이

### 개념 정의

#### 붕괴 (Collapse)
**정의**: 시스템이 완전히 고착되어 움직이지 않는 상태
- **특징**: 
  - 엔트로피 = 0 (완전 수렴)
  - 회전 토크 = 0 (움직임 없음)
  - 모든 선택이 하나로 수렴
- **예시**: 극단적 ASD, 깊은 우울증

#### 루프 (Loop)
**정의**: 반복적인 패턴에 빠진 상태
- **특징**:
  - 낮은 엔트로피 (하지만 0은 아님)
  - 주기적 회전 (세차운동)
  - 제한된 선택 공간 내에서 순환
- **예시**: OCD, 강박적 반복

### 붕괴-루프 스펙트럼

```
붕괴 (Collapse) ──────────────────────────────── 루프 (Loop)
완전 고착                                        반복 패턴
엔트로피 = 0                                     낮은 엔트로피
회전 토크 = 0                                    주기적 회전
```

### 질환 배치

#### 붕괴 쪽 (완전 고착)
1. **ASD** (극단)
   - `decision_temperature=5.0` (매우 높음)
   - `tau=0.1` (매우 낮음)
   - `local_weight_boost=3.0` (패턴 고착)

2. **DEPRESSION** (깊은 우울)
   - `decision_temperature=2.0` (높음)
   - `tau=0.3` (낮음)
   - `novelty_sensitivity=0.5` (무기력)

#### 루프 쪽 (반복 패턴)
3. **OCD** (강박)
   - `decision_temperature=6.0` (극도로 높음)
   - `tau=0.05` (극도로 낮음)
   - `local_weight_boost=4.0` (패턴 고착)
   - **특징**: 반복 행동 (루프)

4. **PTSD** (트라우마 고착)
   - `damping=0.9` (높은 감쇠)
   - `local_weight_boost=2.0` (트라우마 노드 강화)
   - **특징**: 트라우마 기억 루프

#### 중간 영역
5. **BIPOLAR** (양극성)
   - 조증: 루프에서 벗어남 (ADHD 쪽)
   - 우울: 루프로 수렴 (ASD 쪽)
   - **특징**: 동적 전환

---

## 📐 다차원 매핑

### 3D 공간 표현

```
                    높은 불안
                        ↑
                        |
            공황장애    |    강박
            PTSD        |    (루프)
                        |
ADHD(+) ────────────────┼─────────────── ASD(-)
(발산)                  |                (수렴)
    간질                |    우울증
    분노                |    (붕괴)
                        |
                        ↓
                    낮은 불안
```

### 차원별 분석

#### 1. 탐색-착취 축 (X축)
- **ADHD(+)**: `tau` 높음, `decision_temperature` 낮음
- **ASD(-)**: `tau` 낮음, `decision_temperature` 높음

#### 2. 불안/스트레스 축 (Y축)
- **높은 불안**: `stress_baseline` 높음, `novelty_sensitivity` 높음
- **낮은 불안**: `stress_baseline` 낮음, `novelty_sensitivity` 낮음

#### 3. 안정성 축 (Z축)
- **불안정**: `decision_temperature` 낮음, `impulsivity` 높음
- **안정**: `decision_temperature` 높음, `impulsivity` 낮음

---

## 🔍 현재 구현 상태 점검

### ✅ 완전 구현된 질환 (9개)

1. **NORMAL** - 정상 모드
2. **ADHD** - 고엔트로피, 발산
3. **ASD** - 저엔트로피, 수렴
4. **PTSD** - 트라우마 고착
5. **PANIC** - 공황장애
6. **EPILEPSY** - 간질
7. **OCD** - 강박 (루프)
8. **IED** - 분노조절장애
9. **DEPRESSION** - 우울증 (붕괴)

### ⚠️ 부분 구현된 질환 (1개)

10. **BIPOLAR** - 양극성 장애
    - **현재 상태**: 
      - Enum에 `BIPOLAR` 정의됨
      - `bipolar_mania()` 메서드 있음
      - `bipolar_depression()` 메서드 있음
      - `get_config()`는 `bipolar_mania()`만 반환
    - **문제점**: 
      - 동적 전환 메커니즘이 없음
      - 조증 ↔ 우울 상태 전환 로직 미구현
    - **필요 작업**:
      - 상태 추적 메커니즘
      - 자동 전환 로직
      - 또는 수동 전환 API

---

## 🚀 확장성 분석

### 1. 현재 확장 가능한 영역

#### 붕괴 쪽 확장
**추가 가능한 질환:**
- **Catatonia** (긴장증)
  - 특징: 완전한 움직임 정지
  - 파라미터: `tau=0.01`, `decision_temperature=10.0`

- **Severe Depression** (중증 우울)
  - 특징: 극도의 무기력
  - 파라미터: `tau=0.05`, `novelty_sensitivity=0.1`

#### 루프 쪽 확장
**추가 가능한 질환:**
- **Tourette Syndrome** (뚜렛 증후군)
  - 특징: 반복적 틱
  - 파라미터: `tau=0.2`, `impulsivity=0.8`, `local_weight_boost=3.0`

- **Trichotillomania** (발모벽)
  - 특징: 반복적 행동
  - 파라미터: `tau=0.1`, `local_weight_boost=3.5`

#### 중간 영역 확장
**추가 가능한 질환:**
- **Borderline Personality Disorder** (경계선 성격장애)
  - 특징: 불안정한 정서, 충동성
  - 파라미터: `tau=1.5`, `impulsivity=0.7`, `stress_baseline=0.7`

- **Anxiety Disorder** (불안장애)
  - 특징: 높은 불안, 중간 탐색
  - 파라미터: `tau=0.8`, `stress_baseline=0.6`, `novelty_sensitivity=2.5`

---

### 2. 확장 메커니즘

#### 현재 구조
```python
class CognitiveMode(Enum):
    # 기존 질환들...
    NEW_DISORDER = "new_disorder"

class CognitiveModePresets:
    @staticmethod
    def new_disorder() -> ModeConfig:
        return ModeConfig(...)
    
    @staticmethod
    def get_config(mode: CognitiveMode) -> ModeConfig:
        # 새 질환 추가
        elif mode == CognitiveMode.NEW_DISORDER:
            return CognitiveModePresets.new_disorder()
```

#### 확장 용이성
- ✅ **쉬움**: Enum 추가 + Preset 메서드 + get_config() 업데이트
- ✅ **독립적**: 기존 질환에 영향 없음
- ✅ **파라미터 조정**: ModeConfig로 세밀한 조정 가능

---

### 3. 동적 질환 (복잡한 확장)

#### 양극성 장애 개선
**현재 문제:**
- 조증/우울 상태 전환 로직 없음

**개선 방안:**
```python
class BipolarState(Enum):
    MANIA = "mania"
    DEPRESSION = "depression"
    MIXED = "mixed"
    EUTHYMIC = "euthymic"

class CognitiveKernel:
    def __init__(self, ...):
        self._bipolar_state: Optional[BipolarState] = None
        if mode == CognitiveMode.BIPOLAR:
            self._bipolar_state = BipolarState.MANIA
    
    def _update_bipolar_state(self):
        """양극성 상태 자동 전환"""
        # 시간 기반 또는 이벤트 기반 전환
        ...
    
    def get_bipolar_config(self) -> ModeConfig:
        """현재 양극성 상태에 맞는 설정 반환"""
        if self._bipolar_state == BipolarState.MANIA:
            return CognitiveModePresets.bipolar_mania()
        elif self._bipolar_state == BipolarState.DEPRESSION:
            return CognitiveModePresets.bipolar_depression()
        ...
```

#### 다른 동적 질환
**추가 가능:**
- **Cyclothymia** (순환성 기분장애)
  - 양극성의 경미한 형태
  - 더 빠른 전환

- **Rapid Cycling Bipolar** (급속 순환 양극성)
  - 매우 빠른 상태 전환
  - 주기적 전환 메커니즘 필요

---

### 4. 복합 질환 (고급 확장)

#### 공존 질환
**예시:**
- ADHD + Anxiety
- ASD + OCD
- Depression + Anxiety

**구현 방안:**
```python
class CompositeMode:
    """복합 모드"""
    def __init__(self, modes: List[CognitiveMode], weights: List[float]):
        self.modes = modes
        self.weights = weights
    
    def get_config(self) -> ModeConfig:
        """모드들의 가중 평균"""
        configs = [CognitiveModePresets.get_config(m) for m in self.modes]
        # 가중 평균 계산
        ...
```

---

## 📊 구현 상태 요약

### 완료도

| 카테고리 | 구현 상태 | 비고 |
|----------|----------|------|
| **기본 질환** | ✅ 100% | NORMAL, ADHD, ASD, PTSD |
| **ADHD(+) 쪽** | ✅ 100% | PANIC, EPILEPSY, IED |
| **ASD(-) 쪽** | ✅ 100% | OCD, DEPRESSION |
| **동적 질환** | ⚠️ 50% | BIPOLAR (조증/우울 분리 구현, 전환 로직 없음) |
| **복합 질환** | ❌ 0% | 미구현 |

### 확장 가능성

| 확장 타입 | 난이도 | 우선순위 |
|----------|--------|----------|
| **새 질환 추가** | ⭐ 쉬움 | 높음 |
| **동적 전환** | ⭐⭐ 보통 | 중간 (BIPOLAR 개선) |
| **복합 질환** | ⭐⭐⭐ 어려움 | 낮음 |

---

## 🎯 다음 작업 제안

### 우선순위 1: BIPOLAR 개선
- 동적 상태 전환 메커니즘 구현
- 시간 기반 또는 이벤트 기반 전환
- 상태 추적 및 모니터링

### 우선순위 2: 새 질환 추가
- Catatonia (붕괴 쪽)
- Tourette Syndrome (루프 쪽)
- Borderline Personality Disorder (중간 영역)

### 우선순위 3: 복합 질환 연구
- 공존 질환 모델링
- 가중 평균 메커니즘

---

---

## 🔬 냉정 판정 (코드 기준)

**상세 분석**: [IMPLEMENTATION_STATUS_COLD.md](./IMPLEMENTATION_STATUS_COLD.md)

### 핵심 결론

> **"ADHD-ASD는 완성, OCD·Panic은 절반, Epilepsy는 구조 준비 완료 단계"**

> **이 엔진은 '질환 수집기'가 아니라 '질환이 생길 수밖에 없는 물리적 판'을 이미 갖고 있다.**

### 다음 작업

**질환 추가 ❌**

**임계점과 시간축 추가 ⭕**

---

**마지막 업데이트**: 2026-01-31

