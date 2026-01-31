# 폴더 구조 정리 권장사항

> **현재 상태 분석 및 정리 방안**

**작성일**: 2026-01-31

---

## 🔍 현재 문제점

1. **폴더 구조가 불명확함**
   - 독립 모듈인지 통합 모듈인지 불분명
   - 문서가 산재되어 있음
   - 개념 정리가 안 됨

2. **엔진 상태가 혼재됨**
   - 독립 배포 가능한 엔진과 통합 엔진이 섞여 있음
   - 각 엔진의 역할과 의존성이 불명확

3. **문서 정리 부족**
   - 각 엔진별 문서 부족
   - 통합 문서 부족
   - 폴더 구조 문서 부족

---

## 📁 권장 폴더 구조

### 옵션 A: 독립 모듈 분리 (권장)

```
00_BRAIN/
├── Cognitive_Kernel/                    # 메인 프로젝트
│   ├── src/cognitive_kernel/
│   │   ├── core.py
│   │   ├── cognitive_modes.py
│   │   └── engines/
│   │       ├── dynamics/               # 통합 버전 (의존성 있음)
│   │       ├── panorama/
│   │       ├── memoryrank/
│   │       └── ...
│   ├── docs/
│   │   ├── development/
│   │   ├── version_history/
│   │   └── technical/
│   ├── tests/
│   └── README.md
│
└── Dynamics_Engine/                     # 독립 모듈 (새로 생성)
    ├── src/dynamics_engine/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── models.py
    │   └── dynamics_engine.py
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

### 옵션 B: Cognitive Kernel 내부 유지

```
00_BRAIN/
└── Cognitive_Kernel/
    ├── src/cognitive_kernel/
    │   ├── core.py
    │   ├── cognitive_modes.py
    │   └── engines/
    │       ├── dynamics/               # 독립 사용 가능하지만 통합 구조
    │       │   ├── __init__.py
    │       │   ├── config.py
    │       │   ├── models.py
    │       │   └── dynamics_engine.py
    │       ├── panorama/
    │       └── ...
    ├── docs/
    │   ├── engines/
    │   │   ├── dynamics/              # Dynamics Engine 전용 문서
    │   │   │   ├── README.md
    │   │   │   ├── API_REFERENCE.md
    │   │   │   └── DEPLOYMENT.md
    │   │   └── ...
    │   ├── development/
    │   └── version_history/
    └── README.md
```

---

## 🎯 최종 권장사항

### **하이브리드 접근법**

**1. 독립 모듈 생성 (필수)**
- `00_BRAIN/Dynamics_Engine/` 폴더 생성
- 독립 배포 가능한 버전 배치
- GitHub에 별도 저장소로 업로드 가능

**2. Cognitive Kernel 통합 유지**
- `Cognitive_Kernel/engines/dynamics/`는 독립 모듈의 복사본 또는 심볼릭 링크
- 통합 테스트 및 개발 편의성 유지

**3. 문서 정리**
- 각 엔진별 `docs/engines/{engine_name}/` 폴더 생성
- 통합 문서는 `docs/` 루트에 유지

---

## 📋 실행 계획

### Step 1: 독립 모듈 생성

```bash
# 1. 독립 모듈 폴더 생성
mkdir -p /Users/jazzin/Desktop/00_BRAIN/Dynamics_Engine

# 2. 기본 구조 생성
cd /Users/jazzin/Desktop/00_BRAIN/Dynamics_Engine
mkdir -p src/dynamics_engine tests docs examples

# 3. 파일 복사
cp -r /Users/jazzin/Desktop/00_BRAIN/Cognitive_Kernel/src/cognitive_kernel/engines/dynamics/* \
      src/dynamics_engine/

# 4. setup.py 작성
# 5. README.md 작성
# 6. requirements.txt 작성
```

### Step 2: 문서 정리

```bash
# 1. 엔진별 문서 폴더 생성
cd /Users/jazzin/Desktop/00_BRAIN/Cognitive_Kernel
mkdir -p docs/engines/dynamics

# 2. 기존 문서 이동
mv docs/DYNAMICS_ENGINE_*.md docs/engines/dynamics/
mv docs/DEMENTIA_ALZHEIMER_IMPLEMENTATION.md docs/engines/dynamics/

# 3. 통합 문서 업데이트
# docs/ENGINE_INDEX.md 생성
```

### Step 3: GitHub 업로드 (선택)

```bash
# 독립 모듈을 별도 저장소로
cd /Users/jazzin/Desktop/00_BRAIN/Dynamics_Engine
git init
git add .
git commit -m "Initial commit: Dynamics Engine v1.0.0"
# GitHub에 새 저장소 생성 후 push
```

---

## ✅ 최종 결론

**Dynamics Engine은 독립 모듈로 분리해야 합니다.**

**이유:**
1. ✅ 100% 독립 배포 가능
2. ✅ Edge AI 지원 필수
3. ✅ 다른 프로젝트 재사용 가능
4. ✅ 모듈화 원칙 준수

**구조:**
- 독립 모듈: `00_BRAIN/Dynamics_Engine/`
- 통합 버전: `Cognitive_Kernel/engines/dynamics/` (복사본 또는 심볼릭 링크)

**문서:**
- 독립 모듈 문서: `Dynamics_Engine/docs/`
- 통합 문서: `Cognitive_Kernel/docs/engines/dynamics/`

---

**작성자**: GNJz (Qquarts)  
**작성일**: 2026-01-31

