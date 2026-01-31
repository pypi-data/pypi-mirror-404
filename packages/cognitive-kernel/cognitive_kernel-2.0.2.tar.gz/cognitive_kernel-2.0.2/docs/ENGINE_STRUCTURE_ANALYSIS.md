# 엔진 구조 분석 및 정리 방안

> **현재 상태 분석 및 독립 모듈 vs 통합 모듈 판단**

**작성일**: 2026-01-31  
**버전**: v2.0.2

---

## 🔍 현재 상황 분석

### 1. Dynamics Engine의 현재 위치

**위치**: `src/cognitive_kernel/engines/dynamics/`

**구조**:
```
engines/dynamics/
├── __init__.py          # 공개 API
├── config.py            # DynamicsConfig
├── models.py            # DynamicsState
└── dynamics_engine.py   # DynamicsEngine
```

**의존성 상태**:
- ✅ **독립 배포 가능**: 100%
- ✅ **표준 라이브러리만 사용**: `math`, `time`
- ✅ **CognitiveMode 의존성 제거 완료**: 문자열 모드 지원

---

## 📊 독립 모듈 vs 통합 모듈 판단

### 옵션 1: 독립 모듈로 분리 (권장)

**장점:**
- ✅ Edge AI 환경에서 독립 사용 가능
- ✅ 다른 프로젝트에서 재사용 가능
- ✅ 버전 관리 독립적
- ✅ 테스트 및 배포 용이
- ✅ 모듈화 원칙 준수

**단점:**
- ⚠️ 별도 저장소 관리 필요
- ⚠️ Cognitive Kernel과의 통합 관리 필요

**구조 제안**:
```
00_BRAIN/
├── Cognitive_Kernel/          # 메인 프로젝트
│   └── src/cognitive_kernel/
│       └── engines/
│           ├── dynamics/      # 통합 버전 (의존성 있음)
│           ├── panorama/
│           ├── memoryrank/
│           └── ...
│
└── Dynamics_Engine/           # 독립 모듈 (새 폴더)
    ├── src/dynamics_engine/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── models.py
    │   └── dynamics_engine.py
    ├── tests/
    ├── docs/
    ├── README.md
    ├── setup.py
    └── requirements.txt
```

---

### 옵션 2: Cognitive Kernel 내부에 유지

**장점:**
- ✅ 단일 저장소 관리
- ✅ 통합 테스트 용이
- ✅ 버전 동기화 자동

**단점:**
- ❌ 독립 사용 불가
- ❌ 다른 프로젝트 재사용 어려움
- ❌ Edge AI 배포 복잡

---

## 🎯 권장 방안

### **하이브리드 접근법 (권장)**

**1단계: 독립 모듈 생성**
- `00_BRAIN/Dynamics_Engine/` 폴더 생성
- 독립 배포 가능한 버전 배치
- `setup.py` 및 `README.md` 포함

**2단계: Cognitive Kernel 통합**
- `Cognitive_Kernel`에서 독립 모듈을 의존성으로 사용
- 또는 심볼릭 링크로 연결
- 또는 `engines/dynamics/`는 독립 모듈의 복사본 유지

**3단계: 문서 정리**
- 각 엔진별 README 작성
- 통합 문서 업데이트
- 폴더 구조 문서화

---

## 📁 현재 엔진 구조 분석

### Cognitive Kernel 내부 엔진들

```
engines/
├── dynamics/          # ✅ 독립 배포 가능 (100%)
├── panorama/          # ⚠️ Cognitive Kernel 의존성 있음
├── memoryrank/        # ⚠️ Panorama 의존성 있음
├── pfc/              # ⚠️ Cognitive Kernel 의존성 있음
├── basal_ganglia/    # ⚠️ Cognitive Kernel 의존성 있음
├── thalamus/         # ⚠️ Cognitive Kernel 의존성 있음
├── amygdala/         # ⚠️ Cognitive Kernel 의존성 있음
└── hypothalamus/     # ⚠️ Cognitive Kernel 의존성 있음
```

### 독립 배포 가능성

| 엔진 | 독립 배포 가능 | 의존성 |
|------|---------------|--------|
| Dynamics Engine | ✅ 100% | 없음 (표준 라이브러리만) |
| Panorama Memory | ⚠️ 부분 | Cognitive Kernel 구조 |
| MemoryRank | ❌ 불가 | Panorama 의존 |
| PFC | ❌ 불가 | Cognitive Kernel 구조 |
| Basal Ganglia | ❌ 불가 | Cognitive Kernel 구조 |
| Thalamus | ❌ 불가 | Cognitive Kernel 구조 |
| Amygdala | ❌ 불가 | Cognitive Kernel 구조 |
| Hypothalamus | ❌ 불가 | Cognitive Kernel 구조 |

---

## 🚀 실행 계획

### Phase 1: Dynamics Engine 독립 모듈 생성

**작업 내용:**
1. `00_BRAIN/Dynamics_Engine/` 폴더 생성
2. 독립 모듈 구조 생성
3. `setup.py` 작성
4. `README.md` 작성
5. 테스트 스크립트 작성
6. GitHub 저장소 생성 (선택)

**파일 구조:**
```
Dynamics_Engine/
├── src/
│   └── dynamics_engine/
│       ├── __init__.py
│       ├── config.py
│       ├── models.py
│       └── dynamics_engine.py
├── tests/
│   └── test_dynamics_engine.py
├── docs/
│   ├── README.md
│   └── API_REFERENCE.md
├── examples/
│   └── basic_usage.py
├── setup.py
├── requirements.txt
├── README.md
└── LICENSE
```

### Phase 2: Cognitive Kernel 통합 유지

**작업 내용:**
1. `Cognitive_Kernel`에서 독립 모듈 사용
2. 또는 `engines/dynamics/`는 독립 모듈의 복사본으로 유지
3. 통합 테스트 업데이트

### Phase 3: 문서 정리

**작업 내용:**
1. 각 엔진별 README 작성
2. 폴더 구조 문서화
3. 통합 문서 업데이트
4. 아키텍처 다이어그램 생성

---

## 📋 결론 및 권장사항

### ✅ 권장: 독립 모듈 생성

**이유:**
1. **Edge AI 지원**: 독립 배포 가능
2. **재사용성**: 다른 프로젝트에서 사용 가능
3. **모듈화 원칙**: 단일 책임 원칙 준수
4. **버전 관리**: 독립적 버전 관리 가능

### 📁 폴더 구조 제안

```
00_BRAIN/
├── Cognitive_Kernel/              # 메인 프로젝트
│   ├── src/cognitive_kernel/
│   │   └── engines/
│   │       ├── dynamics/         # 통합 버전 (의존성 있음)
│   │       └── ...
│   └── docs/
│
└── Dynamics_Engine/               # 독립 모듈 (새로 생성)
    ├── src/dynamics_engine/
    ├── tests/
    ├── docs/
    ├── setup.py
    └── README.md
```

### 🔄 통합 방법

**방법 1: 의존성으로 사용 (권장)**
```python
# Cognitive_Kernel/requirements.txt
dynamics-engine>=1.0.0

# Cognitive_Kernel/src/cognitive_kernel/engines/dynamics/
# → 독립 모듈의 심볼릭 링크 또는 import
```

**방법 2: 복사본 유지**
- `Cognitive_Kernel/engines/dynamics/`는 독립 모듈의 복사본
- 주기적으로 동기화

---

## 🎯 다음 단계

1. ✅ **독립 모듈 생성**: `00_BRAIN/Dynamics_Engine/` 폴더 생성
2. ✅ **setup.py 작성**: pip 설치 가능하도록
3. ✅ **README.md 작성**: 사용법 및 API 문서
4. ✅ **테스트 작성**: 독립 모듈 테스트
5. ✅ **GitHub 업로드**: 독립 저장소 생성 (선택)
6. ✅ **Cognitive Kernel 통합**: 의존성 또는 복사본으로 연결

---

**작성자**: GNJz (Qquarts)  
**작성일**: 2026-01-31

