# 📋 버전 관리 전략 (Version Strategy)

## 🎯 현재 구조

### 1. 통합 패키지: Cognitive Kernel

**위치**: `src/cognitive_kernel/`  
**PyPI 패키지**: `cognitive-kernel`  
**현재 버전**: **v2.0.1**

**특징:**
- 모든 엔진을 통합한 고수준 인터페이스
- 모드 기반 파라미터 조정 (ADHD/ASD/PTSD/NORMAL)
- 장기 기억 + 의사결정 통합

**사용:**
```bash
pip install cognitive-kernel
```

```python
from cognitive_kernel import CognitiveKernel, CognitiveMode

kernel = CognitiveKernel("my_brain", mode=CognitiveMode.ASD)
```

---

### 2. 독립 엔진들 (Standalone Engines)

**위치**: 루트 레벨 폴더

| 엔진 | 폴더 | 독립 배포 가능 | 현재 상태 |
|------|------|--------------|----------|
| MemoryRank | `MemoryRank/` | ✅ 예 | 독립 엔진 |
| Panorama | `Panorama/` | ✅ 예 | 독립 엔진 |
| PFC | `PFC/` | ✅ 예 | 독립 엔진 |
| BasalGanglia | `BasalGanglia/` | ✅ 예 | 독립 엔진 |
| Amygdala | `Amygdala/` | ✅ 예 | 독립 엔진 |
| Hypothalamus | `Hypothalamus/` | ✅ 예 | 독립 엔진 |
| Thalamus | `Thalamus/` | ✅ 예 | 독립 엔진 |

**특징:**
- 각각 독립적으로 사용 가능
- 자체 테스트, 문서, 블록체인 서명
- PyPI에 개별 배포 가능 (선택적)

**사용 예시:**
```python
# MemoryRank만 독립적으로 사용
from memoryrank import MemoryRankEngine

engine = MemoryRankEngine()
```

---

## 🔄 버전 관리 전략

### 현재 상황

1. **Cognitive Kernel (통합 패키지)**
   - 버전: **v2.0.1**
   - PyPI: `cognitive-kernel==2.0.1`
   - 모든 엔진 통합 + 모드 기능

2. **독립 엔진들**
   - 각각 자체 버전 관리 가능
   - 현재는 Cognitive Kernel과 함께 관리
   - 필요시 개별 PyPI 배포 가능

---

## 🎯 향후 방향

### 옵션 1: 계속 Cognitive Kernel 중심 (현재 전략)

**장점:**
- ✅ 단일 패키지로 간단
- ✅ 통합 기능 제공
- ✅ 사용자 입장에서 편리

**구조:**
```
Cognitive Kernel v2.0.1
├── MemoryRank (내장)
├── Panorama (내장)
├── PFC (내장)
├── BasalGanglia (내장)
├── Amygdala (내장)
├── Hypothalamus (내장)
└── Thalamus (내장)
```

**사용:**
```bash
pip install cognitive-kernel
```

---

### 옵션 2: 독립 엔진 + 통합 패키지 병행

**장점:**
- ✅ 각 엔진을 독립적으로 사용 가능
- ✅ 필요한 엔진만 설치 가능
- ✅ 엔진별 독립 버전 관리

**구조:**
```
MemoryRank v1.0.0 (독립)
Panorama v1.0.0 (독립)
PFC v1.0.0 (독립)
...

Cognitive Kernel v2.0.1 (통합)
├── memoryrank (의존성)
├── panorama (의존성)
├── pfc (의존성)
└── ...
```

**사용:**
```bash
# 옵션 A: 통합 패키지
pip install cognitive-kernel

# 옵션 B: 독립 엔진만
pip install memoryrank
```

---

### 옵션 3: 모듈식 구조 (Monorepo)

**장점:**
- ✅ 모든 엔진이 같은 저장소
- ✅ 버전 동기화 가능
- ✅ 통합 테스트 용이

**구조:**
```
cognitive-kernel/
├── packages/
│   ├── memoryrank/
│   ├── panorama/
│   ├── pfc/
│   └── ...
└── cognitive-kernel/ (통합)
```

---

## 💡 현재 권장 전략

### **옵션 1 유지 (Cognitive Kernel 중심)**

**이유:**
1. ✅ 이미 PyPI에 배포됨
2. ✅ 사용자 입장에서 간단
3. ✅ 통합 기능 (모드, 장기 기억) 제공
4. ✅ 독립 엔진은 필요시 개별 배포 가능

**버전 관리:**
- Cognitive Kernel: 메인 버전 (현재 v2.0.1)
- 독립 엔진: 필요시 개별 버전 관리

---

## 🔍 현재 버전 상태

### Cognitive Kernel
- **버전**: v2.0.1
- **PyPI**: `cognitive-kernel==2.0.1`
- **위치**: `src/cognitive_kernel/`
- **기능**: 통합 패키지 + 모드 기능

### 독립 엔진들
- **버전**: 각각 자체 버전 (일부는 1.0.0-alpha)
- **PyPI**: 아직 개별 배포 안 됨 (선택적)
- **위치**: 루트 레벨 폴더
- **기능**: 독립 사용 가능

---

## 📊 비교표

| 항목 | 옵션 1 (현재) | 옵션 2 (독립) | 옵션 3 (Monorepo) |
|------|--------------|--------------|-------------------|
| **복잡도** | 낮음 | 중간 | 높음 |
| **사용 편의성** | 높음 | 중간 | 중간 |
| **유연성** | 중간 | 높음 | 높음 |
| **유지보수** | 쉬움 | 중간 | 어려움 |
| **현재 상태** | ✅ 구현됨 | ❌ 미구현 | ❌ 미구현 |

---

## 🎯 결론

**현재 전략 (옵션 1) 유지 권장:**

1. ✅ 이미 작동하는 구조
2. ✅ 사용자 입장에서 간단
3. ✅ 통합 기능 제공
4. ✅ 필요시 독립 엔진 개별 배포 가능

**변경이 필요한 경우:**
- 독립 엔진을 PyPI에 개별 배포하고 싶을 때
- 엔진별 독립 버전 관리가 필요할 때
- 모듈식 구조로 전환하고 싶을 때

---

**Author**: GNJz (Qquarts)  
**Version**: 2.0.1  
**Last Updated**: 2026-01-30

