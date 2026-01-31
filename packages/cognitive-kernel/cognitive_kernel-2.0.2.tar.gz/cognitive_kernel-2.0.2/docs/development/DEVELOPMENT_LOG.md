# 📜 개발 로그 (Development Log)

> **어떻게 여기까지 만들어졌는가 - 완전한 개발 기록**

**작성일**: 2026-01-31  
**현재 버전**: v2.0.1+

---

## 🎯 목적

생소한 기술과 코드 로직을 이해하기 위해:
- 개발 과정의 모든 단계 기록
- 결정 사항과 이유
- 문제 해결 과정
- 버전별 변화 추적

---

## 📅 타임라인

### 2026-01-29: v1.0.0 초기 구현

**목표:**
- 통합 인지 엔진 기본 구조
- 장기 기억 저장/로드
- 4개 엔진 통합

**구현 내용:**
- `cognitive_kernel.py` 단일 파일
- Panorama, MemoryRank, PFC, BasalGanglia 엔진 통합
- 자동 세션 관리 (with 문 지원)
- JSON 기반 저장/로드

**결정 사항:**
- 단일 파일 구조 선택 (초기 단순화)
- `sys.path.insert`로 엔진 패키지 경로 추가
- 자동 저장 간격: 100개 이벤트마다

**문제점:**
- 기억이 의사결정에 반영되지 않음
- 인지 모드 없음
- Thalamus, Amygdala, Hypothalamus 미통합

**PHAM 기록:**
- Hash: `63a182f8a1420231ee3d45efd5d0b9d2800be6790619934f8f2f82daf3e57454`
- CID: `Qme2rgSYgFzmNszMVV5eMu9ShV7uMLCn8Uj26J9XeosCe9`

---

### 2026-01-30: v2.0.0 패키지 구조 전환

**목표:**
- PyPI 배포 준비
- 패키지 구조 정리
- 외부 라이브러리 통합

**구현 내용:**
- `src/cognitive_kernel/` 패키지 구조
- LangChain 통합 예제
- LlamaIndex 통합 예제
- Vector DB 통합 (Chroma/FAISS)

**결정 사항:**
- PyPI 표준 구조 채택
- `pyproject.toml` 사용
- 선택적 의존성 (langchain, llamaindex, vector)

**Git 커밋:**
- `3376b0b` - feat: Add PyPI package structure (v2.0.0)
- `29047a1` - feat: Add LangChain integration example
- `a04f19` - feat: Add LlamaIndex integration

**문제점:**
- 여전히 기억이 의사결정에 반영 안 됨
- 인지 모드 없음

---

### 2026-01-30 ~ 2026-01-31: v2.0.1 핵심 기능 구현

#### 1단계: 인지 모드 시스템 추가

**목표:**
- ADHD, ASD, PTSD 모드 시뮬레이션
- 모드별 파라미터 조정

**구현 내용:**
- `CognitiveMode` Enum 생성
- `ModeConfig` dataclass
- `set_mode()` 메서드

**결정 사항:**
- 모드별 파라미터:
  - `gate_threshold`: Thalamus 게이팅 임계값
  - `decision_temperature`: PFC 결정 온도 (β)
  - `tau`: BasalGanglia 탐색 온도
  - `damping`: MemoryRank 감쇠

**Git 커밋:**
- `ee704aa` - feat: Add Cognitive Modes (ADHD/ASD/PTSD)

---

#### 2단계: 기억 기반 의사결정 구현

**목표:**
- MemoryRank 결과를 의사결정에 반영
- 최소 차분 모델 구현

**구현 내용:**
- `_calculate_memory_relevance()` 메서드
- 키워드 매칭 알고리즘
- 효용 계산 수식: `U = U_0 + α · C_n(k)`

**수식:**
```python
# 기억 관련성
C_n(k) = min(1, Σ(s_i × m_{i,k}))

# 효용
U_{n,k} = U_0 + α · C_n(k)

# 확률
P_n(k) = softmax(β · U_{n,k})
```

**결정 사항:**
- 기억 영향 계수 α = 0.5
- 기본 보상 U_0 = 0.5
- 키워드 매칭: 단순 문자열 포함 검사

**Git 커밋:**
- `deb20c3` - feat: MemoryRank → Action Utility 연결 구현

**문제점:**
- 키워드 매칭이 단순함 (향후 개선 필요)
- 기억 관련성 계산이 선형적 (비선형 고려 필요)

---

#### 3단계: 물리적 동역학 문서화

**목표:**
- 맥스웰 구조 이식
- 자기장, 세차운동 이론 정리

**구현 내용:**
- `docs/MAXWELL_STRUCTURE.md`
- `docs/PHYSICAL_DYNAMICS.md`
- `docs/STABILITY_CORE.md`

**결정 사항:**
- 이론 문서화 우선
- 코드 구현은 다음 단계

**Git 커밋:**
- `9878124` - docs: 안정 코어 및 맥스웰 구조 분석 추가
- `76e9099` - docs: 물리적 동역학 및 편향 분석 추가

---

#### 4단계: 엔트로피 기반 자동 회전 토크 구현

**목표:**
- 엔트로피 계산
- 자동 회전 토크 생성
- 세차운동 시뮬레이션

**구현 내용:**
- 엔트로피 계산: `E_n = -Σ P_n(k) ln P_n(k)`
- 회전 토크: `T_n(k) = γ · (E_n / ln(N)) · cos(φ_n - ψ_k)`
- 위상 업데이트: `φ_{n+1} = φ_n + ω`

**수식:**
```python
# 엔트로피
E_n = -Σ P_n(k) ln P_n(k)

# 정규화
normalized_entropy = E_n / ln(N)

# 회전 토크
T_n(k) = γ · normalized_entropy · cos(φ_n - ψ_k)

# 위상 업데이트
φ_{n+1} = φ_n + ω  # ω = 0.05
```

**결정 사항:**
- 기본 회전 강도 γ = 0.3
- ADHD: γ × 1.5
- ASD: γ × 0.5
- 세차 속도 ω = 0.05

**Git 커밋:**
- `b0c481c` - feat: 세차운동(precession) 데모 추가
- `760900a` - fix: v2.0.1 규약 준수 세차운동 데모 작성

---

#### 5단계: 질환 모드 추가

**목표:**
- ADHD(+) ↔ ASD(-) 스펙트럼 내 질환 추가
- 각 질환의 특성 반영

**구현 내용:**
- PANIC (공황장애)
- EPILEPSY (간질)
- OCD (강박)
- IED (분노조절장애)
- DEPRESSION (우울증)
- BIPOLAR (양극성 장애)

**결정 사항:**
- 각 질환별 파라미터 조정:
  - PANIC: 높은 gate_threshold, 높은 stress_baseline
  - EPILEPSY: 극도의 불안정 (높은 impulsivity)
  - OCD: 높은 local_weight_boost, 높은 decision_temperature
  - IED: 극도의 impulsivity
  - DEPRESSION: 낮은 novelty_sensitivity, 높은 stress_baseline
  - BIPOLAR: 높은 impulsivity, 높은 novelty_sensitivity

**현재 작업:**
- 2026-01-31 완료

---

#### 6단계: local_weight_boost 구현

**목표:**
- 로컬 연결 가중치 부스트
- 패턴 고착 시뮬레이션

**구현 내용:**
- `MemoryRankConfig`에 `local_weight_boost` 파라미터 추가
- `_is_local_connection()` 메서드 (현재는 모든 연결을 로컬로 간주)
- `build_graph()`에서 로컬 연결 판단 및 가중치 부스트 적용

**결정 사항:**
- 현재 구현: 모든 연결을 로컬로 간주
- 향후 개선: Panorama 이벤트 정보 활용 (시간적 근접성, 이벤트 타입)

**현재 작업:**
- 2026-01-31 완료

---

## 🔬 핵심 결정 사항

### 1. 수식 선택

**최소 차분 모델:**
- 선택 이유: 단순하면서도 효과적
- 대안: 복잡한 신경망 모델 (과도한 복잡도)

**엔트로피 기반 회전:**
- 선택 이유: 물리적 직관과 일치
- 대안: 랜덤 노이즈 (물리적 의미 없음)

---

### 2. 파라미터 값

**기억 영향 계수 α = 0.5:**
- 선택 이유: 기억이 최대 50%까지 보상에 영향
- 실험적 조정 가능

**기본 회전 강도 γ = 0.3:**
- 선택 이유: 적당한 회전 강도
- 모드별 조정 (ADHD: 1.5배, ASD: 0.5배)

**세차 속도 ω = 0.05:**
- 선택 이유: 느린 시간척도 (안정적)
- 빠른 변화 방지

---

### 3. 구조 선택

**v1.0.0: 단일 파일**
- 선택 이유: 초기 단순화
- 문제: 확장성 부족

**v2.0.0: 패키지 구조**
- 선택 이유: PyPI 배포, 확장성
- 장점: 모듈화, 테스트 용이

---

## 🐛 문제 해결 과정

### 문제 1: 기억이 의사결정에 반영 안 됨

**원인:**
- v1.0.0에서 `expected_reward`가 고정값 (0.5)

**해결:**
- `_calculate_memory_relevance()` 구현
- 효용 계산 수식에 반영: `U = U_0 + α · C_n(k)`

**결과:**
- 기억이 의사결정에 반영됨
- MemoryRank 중요도가 선택에 영향

---

### 문제 2: 인지 모드 없음

**원인:**
- 모든 사용자가 동일한 파라미터 사용

**해결:**
- `CognitiveMode` Enum 생성
- `ModeConfig` dataclass로 모드별 파라미터 설정

**결과:**
- ADHD, ASD, PTSD 등 다양한 인지 상태 시뮬레이션 가능

---

### 문제 3: 엔트로피 계산 없음

**원인:**
- 확률 분포만 계산, 엔트로피 미계산

**해결:**
- `E_n = -Σ P_n(k) ln P_n(k)` 구현
- 엔트로피 히스토리 저장

**결과:**
- 엔트로피 기반 자동 회전 토크 생성 가능
- ADHD/ASD 스펙트럼 시각화

---

## 📊 버전별 비교

| 항목 | v1.0.0 | v2.0.0 | v2.0.1 |
|------|--------|--------|--------|
| **파일 구조** | 단일 파일 | 패키지 | 패키지 |
| **엔진 수** | 4개 | 4개 | 7개 |
| **인지 모드** | ❌ | ❌ | ✅ 4개 → 10개 |
| **기억 반영** | ❌ | ❌ | ✅ |
| **엔트로피** | ❌ | ❌ | ✅ |
| **자동 회전 토크** | ❌ | ❌ | ✅ |
| **PHAM 서명** | ✅ | ✅ | ✅ |

---

## 🎯 다음 단계

### v2.1.0 계획

1. **Thalamus 게이팅 루프 통합**
   - `remember()`에 Thalamus 통합
   - 입력 필터링

2. **Hypothalamus 통합**
   - 에너지/스트레스 관리
   - PFC utility에 반영

3. **습관 덮어쓰기**
   - BasalGanglia 습관이 PFC 결정 덮어쓰기

4. **공개 API 정리**
   - internal methods → public
   - 전체 확률 분포 접근

---

## 📝 개발 원칙

1. **단순성 우선**
   - 복잡한 모델보다 단순한 수식 선택
   - 점진적 개선

2. **물리적 직관**
   - 수식이 물리적 의미를 가져야 함
   - 맥스웰 구조, 자기장 등 이론 기반

3. **확장 가능성**
   - 모듈화된 구조
   - 새로운 모드/엔진 추가 용이

4. **문서화**
   - 모든 수식에 주석
   - 개념 설명 포함

5. **PHAM 서명**
   - 모든 버전 업데이트 시 PHAM 서명
   - 블록체인 기록

---

**마지막 업데이트**: 2026-01-31

