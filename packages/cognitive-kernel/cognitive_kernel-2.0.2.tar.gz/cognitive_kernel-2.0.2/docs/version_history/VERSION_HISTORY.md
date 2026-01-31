# 버전 히스토리

> **Cognitive Kernel 버전 변경 이력**

**최종 업데이트**: 2026-01-31

---

## v2.0.2 (2026-01-31)

### 주요 변경사항

#### 1. Dynamics Engine 독립 배포 가능성 100% 달성

**변경 내용:**
- `generate_torque()` 메서드의 `CognitiveMode` 의존성 제거
- 문자열 모드 지원 추가 (`"adhd"`, `"asd"`, `"normal"` 등)
- 선택적 의존성으로 변경 (CognitiveMode가 없어도 작동)

**영향:**
- ✅ Dynamics Engine을 독립 모듈로 배포 가능
- ✅ 다른 프로젝트에서 즉시 사용 가능
- ✅ 기존 호환성 유지

#### 2. 치매/알츠하이머 동역학 확장

**새로운 기능:**
- 시간축 분리: 오래된 기억 vs 새 기억
- `old_memory_decay_rate`: 오래된 기억 감쇠율
- `new_memory_decay_rate`: 새 기억 감쇠율
- `memory_age_threshold`: 기억 나이 임계값

**치매 모드:**
- 오래된 기억 감쇠율: 0.0001 (느림)
- 새 기억 감쇠율: 0.0 (정상)
- 최근 기억부터 지워지는 특성 구현

**알츠하이머 모드:**
- 오래된 기억 감쇠율: 0.0001 (느림)
- 새 기억 감쇠율: 0.1 (매우 빠름, 거의 즉시 소실)
- 새 기억이 전혀 저장되지 않는 특성 구현

**수식:**
```
오래된 기억 감쇠: importance *= exp(-λ_old * age)
새 기억 감쇠: importance *= exp(-λ_new * age)
```

### 수정된 파일

- `src/cognitive_kernel/engines/dynamics/dynamics_engine.py`
- `src/cognitive_kernel/engines/dynamics/config.py`
- `src/cognitive_kernel/cognitive_modes.py`
- `src/cognitive_kernel/core.py`

### 새로 추가된 문서

- `docs/DYNAMICS_ENGINE_DEPLOYMENT_ANALYSIS.md`
- `docs/DYNAMICS_ENGINE_LOCATION.md`
- `docs/DYNAMICS_ENGINE_INTEGRATION_STATUS.md`
- `docs/DYNAMICS_ENGINE_FINAL_STATUS.md`
- `docs/development/WORK_LOG_2026_01_31.md`

---

## v2.0.1 (이전 버전)

### 주요 기능

- Dynamics Engine 엔진화 완료
- Pipeline 패턴 구현
- Core Decay 메커니즘 기본 구현
- 치매/알츠하이머 모드 기본 구현

---

**작성자**: GNJz (Qquarts)
