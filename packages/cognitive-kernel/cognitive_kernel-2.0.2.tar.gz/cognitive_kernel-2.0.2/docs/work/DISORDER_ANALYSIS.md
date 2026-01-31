# 🧠 ADHD(+) ↔ ASD(-) 극 사이 질환 분석

> **뇌의 자기장 사이 질환들 매핑 및 추가**

**작성일**: 2026-01-31

---

## 🎯 핵심 개념

### ADHD(+) ↔ ASD(-) 축

```
ADHD (+)                    ASD (-)
고엔트로피                  저엔트로피
탐색 (Exploration)          착취 (Exploitation)
산만, 분산                  고착, 수렴
```

### 질환 배치 전략

질환들을 **탐색-착취 축**과 **추가 차원**으로 배치:

1. **탐색-착취 축 (주축)**
   - ADHD(+) → ASD(-)

2. **불안/스트레스 차원 (수직축)**
   - 높은 불안: 공황장애, PTSD
   - 낮은 불안: NORMAL

3. **안정성 차원**
   - 불안정: 간질, ADHD
   - 안정: ASD, 강박

4. **충동성 차원**
   - 높은 충동: ADHD, 분노조절장애
   - 낮은 충동: ASD, 강박

---

## 📊 질환 분석 및 배치

### 1. 공황장애 (Panic Disorder)

**특징:**
- 갑작스러운 공황 발작
- 과각성 (Hyperarousal)
- 높은 불안/스트레스
- 예측 불가능성에 대한 공포

**ADHD/ASD 축 배치:**
- **위치**: ADHD 쪽에 가깝지만 **불안 차원이 높음**
- **특징**: 탐색 성향 + 높은 불안

**파라미터 설정:**
```python
gate_threshold=0.15,        # 낮은 임계값 (과각성)
max_channels=8,            # 많은 채널 (불안으로 인한 산만)
decision_temperature=0.6,   # 중간 (불안정)
working_memory_capacity=4, # 낮은 용량 (공황 시 집중력 저하)
tau=1.2,                   # 높은 탐색
impulsivity=0.7,           # 높은 충동성
patience=0.2,              # 낮은 인내심
stress_baseline=0.8,       # 매우 높은 스트레스
novelty_sensitivity=3.5,   # 매우 높은 신규성 민감도 (공포)
```

---

### 2. 간질 (Epilepsy)

**특징:**
- 뇌 전기 활동 이상
- 발작 (Seizure)
- 불안정성
- 예측 불가능한 상태 변화

**ADHD/ASD 축 배치:**
- **위치**: ADHD 쪽 (불안정, 탐색)
- **특징**: 극도의 불안정성, 발작적 변화

**파라미터 설정:**
```python
gate_threshold=0.2,        # 낮은 임계값 (불안정)
max_channels=6,            # 중간
decision_temperature=0.4,  # 낮음 (매우 불안정)
working_memory_capacity=5, # 낮음
tau=2.0,                   # 매우 높은 탐색 (불안정)
impulsivity=0.9,           # 매우 높은 충동성
patience=0.1,              # 매우 낮은 인내심
stress_baseline=0.6,       # 높은 스트레스
novelty_sensitivity=2.0,   # 높은 민감도
```

---

### 3. 강박 (OCD - Obsessive-Compulsive Disorder)

**특징:**
- 반복 행동 (Compulsion)
- 고착 (Obsession)
- 불안 완화를 위한 의식
- 패턴 고착

**ADHD/ASD 축 배치:**
- **위치**: ASD 쪽에 가깝지만 **불안 차원이 높음**
- **특징**: 착취 + 높은 불안 + 반복

**파라미터 설정:**
```python
gate_threshold=0.1,        # 낮은 임계값 (과각성)
max_channels=2,            # 적은 채널 (집중)
decision_temperature=6.0,  # 매우 높음 (강한 고착)
working_memory_capacity=7,
tau=0.05,                  # 매우 낮음 (극도의 착취)
impulsivity=0.2,           # 낮은 충동성
patience=0.95,             # 매우 높은 인내심 (루틴 유지)
damping=0.95,              # 매우 높은 감쇠 (기억 지속)
local_weight_boost=4.0,   # 매우 높은 로컬 연결 (패턴 고착)
stress_baseline=0.7,       # 높은 스트레스
novelty_sensitivity=4.0,   # 매우 높은 민감도 (변화 공포)
```

---

### 4. 분노조절장애 (IED - Intermittent Explosive Disorder)

**특징:**
- 폭발적 분노
- 충동성
- 감정 조절 실패
- 공격성

**ADHD/ASD 축 배치:**
- **위치**: ADHD 쪽 (높은 충동성)
- **특징**: 탐색 + 극도의 충동성 + 감정 조절 실패

**파라미터 설정:**
```python
gate_threshold=0.1,        # 낮은 임계값
max_channels=10,           # 많은 채널
decision_temperature=0.3,  # 매우 낮음 (충동적)
working_memory_capacity=4, # 낮음
tau=2.5,                   # 매우 높은 탐색
impulsivity=0.95,          # 극도의 충동성
patience=0.05,             # 극도로 낮은 인내심
stress_baseline=0.8,       # 매우 높은 스트레스
novelty_sensitivity=2.5,   # 높은 민감도
```

---

### 5. 우울증 (Depression)

**특징:**
- 에너지 저하
- 무기력
- 부정적 인지 편향
- 동기 부족

**ADHD/ASD 축 배치:**
- **위치**: 중간 또는 ASD 쪽 (착취, 고착)
- **특징**: 낮은 탐색 + 낮은 에너지

**파라미터 설정:**
```python
gate_threshold=0.4,        # 높은 임계값 (무기력)
max_channels=2,            # 적은 채널
decision_temperature=2.0,   # 높음 (고착)
working_memory_capacity=5,
tau=0.3,                   # 낮음 (착취)
impulsivity=0.2,           # 낮은 충동성
patience=0.8,              # 높은 인내심 (하지만 부정적)
stress_baseline=0.6,       # 높은 스트레스
novelty_sensitivity=0.5,   # 낮은 민감도 (무기력)
```

---

### 6. 양극성 장애 (Bipolar Disorder)

**특징:**
- 조증 (Mania) ↔ 우울 (Depression)
- 극단적 기분 변화
- 불안정성

**ADHD/ASD 축 배치:**
- **위치**: ADHD ↔ ASD 사이를 오가는 동적 변화
- **특징**: 상태에 따라 ADHD 또는 ASD로 전환

**파라미터 설정 (조증 상태):**
```python
gate_threshold=0.05,       # 매우 낮음
max_channels=15,          # 매우 많은 채널
decision_temperature=0.3,  # 매우 낮음
tau=3.0,                   # 극도의 탐색
impulsivity=0.9,
patience=0.1,
stress_baseline=0.3,       # 낮은 스트레스 (조증)
```

**파라미터 설정 (우울 상태):**
```python
gate_threshold=0.5,        # 높음
max_channels=2,            # 적음
decision_temperature=3.0,  # 높음
tau=0.2,                   # 낮음
impulsivity=0.2,
patience=0.7,
stress_baseline=0.7,       # 높은 스트레스
```

---

## 🗺️ 질환 지도 (ADHD ↔ ASD 축)

```
ADHD (+) ──────────────────────────────────────── ASD (-)
탐색, 고엔트로피                                    착취, 저엔트로피

간질 (Epilepsy) ──────────────────────────────── 강박 (OCD)
불안정, 발작                                        고착, 반복

분노조절장애 (IED) ────────────────────────────── 우울증 (Depression)
충동, 폭발                                          무기력, 고착

공황장애 (Panic) ──────────────────────────────── 양극성 (Bipolar)
과각성, 불안                                        동적 변화

PTSD ──────────────────────────────────────────── (이미 구현됨)
트라우마 고착
```

---

## 📐 다차원 매핑

### 2D 공간 표현

```
        높은 불안
            ↑
            |
    공황장애 | 강박
            |
ADHD(+) ────┼──── ASD(-)
    간질    |    우울증
    분노    |    (고착)
            |
            ↓
        낮은 불안
```

### 3D 공간 표현

- **X축**: 탐색(ADHD) ↔ 착취(ASD)
- **Y축**: 불안/스트레스 (낮음 ↔ 높음)
- **Z축**: 안정성 (안정 ↔ 불안정)

---

## 🎯 구현 전략

### 1. CognitiveMode Enum 확장

```python
class CognitiveMode(Enum):
    NORMAL = "normal"
    ADHD = "adhd"
    ASD = "asd"
    PTSD = "ptsd"
    # NEW
    PANIC = "panic"           # 공황장애
    EPILEPSY = "epilepsy"     # 간질
    OCD = "ocd"               # 강박
    IED = "ied"               # 분노조절장애
    DEPRESSION = "depression" # 우울증
    BIPOLAR = "bipolar"       # 양극성 장애
```

### 2. ModeConfig에 추가 파라미터

필요시 추가:
- `anxiety_level: float` - 불안 수준
- `stability: float` - 안정성
- `emotion_regulation: float` - 감정 조절 능력

### 3. 동적 모드 전환 (양극성 장애)

양극성 장애의 경우 상태에 따라 모드가 동적으로 변함:
```python
def get_bipolar_mode(current_state: str) -> ModeConfig:
    if current_state == "mania":
        return CognitiveModePresets.bipolar_mania()
    elif current_state == "depression":
        return CognitiveModePresets.bipolar_depression()
    else:
        return CognitiveModePresets.normal()
```

---

## 🔬 물리적 해석

### 자기장 구조

각 질환은 **ADHD(+) ↔ ASD(-) 자기장** 내에서 특정 위치를 차지:

- **ADHD(+) 극**: 간질, 분노조절장애, 조증
- **ASD(-) 극**: 강박, 우울증, 우울 상태
- **중간 영역**: 공황장애, PTSD, 양극성 (동적)

### 회전장 (Curl Field)

질환들은 **회전장의 왜곡**으로 해석:
- **간질**: 극도의 불안정 회전
- **강박**: 강한 고착 회전
- **양극성**: 주기적 회전 방향 전환

---

## 📋 구현 우선순위

1. **강박 (OCD)** - ASD 쪽, 명확한 특성
2. **공황장애 (Panic)** - ADHD 쪽, 높은 불안
3. **분노조절장애 (IED)** - ADHD 쪽, 극도의 충동
4. **우울증 (Depression)** - ASD 쪽, 낮은 에너지
5. **간질 (Epilepsy)** - ADHD 쪽, 불안정
6. **양극성 (Bipolar)** - 동적 전환 (복잡)

---

**마지막 업데이트**: 2026-01-31

