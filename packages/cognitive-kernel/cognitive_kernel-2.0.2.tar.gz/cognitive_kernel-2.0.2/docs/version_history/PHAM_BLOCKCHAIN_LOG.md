# PHAM 블록체인 로그

> **Proof of Authorship & Merit - 코드 기여 및 버전 추적**

**최종 업데이트**: 2026-01-31

---

## Dynamics Engine v2.0.2 (2026-01-31)

### 파일별 해시

#### config.py
**경로**: `src/cognitive_kernel/engines/dynamics/config.py`  
**변경 내용**: 시간축 분리 파라미터 추가
- `old_memory_decay_rate`
- `new_memory_decay_rate`
- `memory_age_threshold`

**해시**: (실행 시 계산)

#### models.py
**경로**: `src/cognitive_kernel/engines/dynamics/models.py`  
**변경 내용**: 변경 없음

**해시**: (실행 시 계산)

#### dynamics_engine.py
**경로**: `src/cognitive_kernel/engines/dynamics/dynamics_engine.py`  
**변경 내용**:
- `generate_torque()`: CognitiveMode 의존성 제거, 문자열 모드 지원
- `calculate_core_strength()`: 시간축 분리 로직 추가

**해시**: (실행 시 계산)

#### __init__.py
**경로**: `src/cognitive_kernel/engines/dynamics/__init__.py`  
**변경 내용**: 변경 없음

**해시**: (실행 시 계산)

---

## 해시 계산 방법

```python
import hashlib

def calculate_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()
```

---

## 버전별 체인

### v2.0.2 → (다음 버전)
- 이전 해시: (v2.0.1 해시)
- 현재 해시: (계산 필요)
- 변경 사항: 독립 배포 개선, 시간축 분리 구현

---

**작성자**: GNJz (Qquarts)  
**작성일**: 2026-01-31
