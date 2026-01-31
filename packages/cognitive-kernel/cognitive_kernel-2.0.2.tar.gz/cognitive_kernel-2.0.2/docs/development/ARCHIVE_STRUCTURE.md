# 🗂️ 버전별 아카이브 구조

> **"가라지 창고" - 과거 버전 보관소**

**작성일**: 2026-01-31  
**목적**: 버전 업데이트 시 예전 버전을 체계적으로 보관

---

## 🎯 목적

1. **과거 버전 복구 가능**
   - 언제든지 이전 버전으로 롤백
   - 버그 재현 및 디버깅

2. **개발 과정 추적**
   - 어떻게 만들어졌는지 기록
   - 버전별 변화 비교

3. **문서화**
   - 생소한 기술/코드 로직 이해
   - 체계적인 기록

---

## 📁 디렉토리 구조

```
archive/
├── v1.0.0/
│   ├── cognitive_kernel.py          # 원본 파일
│   ├── pham_chain.json               # PHAM 블록체인 기록
│   ├── README.md                     # 버전별 설명
│   ├── CHANGELOG.md                  # 변경사항
│   └── metadata.json                 # 메타데이터
│
├── v2.0.0/
│   ├── src/                          # 전체 소스 코드
│   │   └── cognitive_kernel/
│   │       ├── __init__.py
│   │       ├── core.py
│   │       └── engines/
│   ├── docs/                         # 문서
│   ├── examples/                     # 예제
│   ├── pham_chain.json
│   ├── README.md
│   ├── CHANGELOG.md
│   └── metadata.json
│
├── v2.0.1/
│   ├── src/
│   ├── docs/
│   ├── examples/
│   ├── pham_chain.json
│   ├── README.md
│   ├── CHANGELOG.md
│   └── metadata.json
│
└── current/                          # 현재 버전 (심볼릭 링크)
    └── -> ../                        # 프로젝트 루트로 링크
```

---

## 📋 버전별 아카이브 내용

### v1.0.0 (2026-01-29)

**파일:**
- `cognitive_kernel.py` (단일 파일)

**PHAM 기록:**
- Hash: `63a182f8a1420231ee3d45efd5d0b9d2800be6790619934f8f2f82daf3e57454`
- CID: `Qme2rgSYgFzmNszMVV5eMu9ShV7uMLCn8Uj26J9XeosCe9`

**주요 특징:**
- 통합 인지 엔진 초기 구현
- 4개 엔진 통합
- 자동 세션 관리

**README.md 내용:**
```markdown
# Cognitive Kernel v1.0.0

## 특징
- 통합 인지 엔진
- 자동 세션 관리
- 4개 엔진 통합

## 한계점
- 기억이 의사결정에 반영되지 않음
- 인지 모드 없음
```

---

### v2.0.0 (2026-01-30)

**파일:**
- `src/cognitive_kernel/` 전체 구조
- `docs/` 문서
- `examples/` 예제

**주요 변경사항:**
- PyPI 패키지 구조로 전환
- LangChain 통합
- LlamaIndex 통합
- Vector DB 통합

**CHANGELOG.md 내용:**
```markdown
# Changelog v2.0.0

## Added
- PyPI 패키지 구조
- LangChain 통합 예제
- LlamaIndex 통합 예제
- Vector DB 통합 (Chroma/FAISS)

## Changed
- 단일 파일 → 패키지 구조
- 경로 설정 방식 변경
```

---

### v2.0.1 (2026-01-30 ~ 2026-01-31)

**파일:**
- `src/cognitive_kernel/` (업데이트)
- `docs/` (물리적 동역학 문서 추가)
- `examples/` (세차운동 데모 추가)

**주요 변경사항:**
- 인지 모드 추가 (ADHD/ASD/PTSD)
- 기억 기반 의사결정 구현
- 엔트로피 기반 자동 회전 토크
- 질환 모드 6개 추가
- local_weight_boost 구현

**CHANGELOG.md 내용:**
```markdown
# Changelog v2.0.1

## Added
- 인지 모드 시스템 (CognitiveMode)
- 기억 기반 의사결정 (최소 차분 모델)
- 엔트로피 계산
- 자동 회전 토크 생성
- 질환 모드 6개 (PANIC, EPILEPSY, OCD, IED, DEPRESSION, BIPOLAR)
- local_weight_boost 파라미터

## Changed
- decide() 반환값 확장 (probability_distribution, entropy, core_strength)
- MemoryRank 그래프 구축 로직 (로컬 연결 부스트)
```

---

## 🔧 아카이브 생성 스크립트

### create_archive.sh

```bash
#!/bin/bash

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./create_archive.sh <version>"
    exit 1
fi

ARCHIVE_DIR="archive/v${VERSION}"
mkdir -p "$ARCHIVE_DIR"

# 소스 코드 복사
cp -r src "$ARCHIVE_DIR/"
cp -r docs "$ARCHIVE_DIR/" 2>/dev/null || true
cp -r examples "$ARCHIVE_DIR/" 2>/dev/null || true

# PHAM 체인 복사
cp pham_chain_cognitive_kernel.json "$ARCHIVE_DIR/" 2>/dev/null || true

# 메타데이터 생성
cat > "$ARCHIVE_DIR/metadata.json" <<EOF
{
  "version": "$VERSION",
  "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_commit": "$(git rev-parse HEAD)",
  "files": {
    "src": "$(find src -type f | wc -l) files",
    "docs": "$(find docs -type f 2>/dev/null | wc -l) files",
    "examples": "$(find examples -type f 2>/dev/null | wc -l) files"
  }
}
EOF

echo "Archive created: $ARCHIVE_DIR"
```

---

## 📝 버전별 README 템플릿

### archive/vX.Y.Z/README.md

```markdown
# Cognitive Kernel vX.Y.Z

**날짜**: YYYY-MM-DD  
**PHAM 해시**: `...`  
**Git 커밋**: `...`

## 주요 특징

- [특징 1]
- [특징 2]

## 핵심 수식

\`\`\`python
# 수식 설명
\`\`\`

## 한계점

- [한계점 1]
- [한계점 2]

## 다음 버전 계획

- [계획 1]
- [계획 2]
```

---

## 🔗 버전별 링크

### Git 태그와 연결

```bash
# 버전 태그 생성
git tag -a v1.0.0 -m "Cognitive Kernel v1.0.0"
git tag -a v2.0.0 -m "Cognitive Kernel v2.0.0"
git tag -a v2.0.1 -m "Cognitive Kernel v2.0.1"

# 태그 확인
git tag -l

# 특정 버전 체크아웃
git checkout v1.0.0
```

---

## 📊 버전별 비교표

| 항목 | v1.0.0 | v2.0.0 | v2.0.1 |
|------|--------|--------|--------|
| **엔진 수** | 4개 | 4개 | 7개 |
| **인지 모드** | ❌ | ❌ | ✅ |
| **기억 반영** | ❌ | ❌ | ✅ |
| **엔트로피** | ❌ | ❌ | ✅ |
| **자동 회전 토크** | ❌ | ❌ | ✅ |
| **PHAM 서명** | ✅ | ✅ | ✅ |

---

## 🎯 아카이브 사용 가이드

### 1. 특정 버전 복구

```bash
# 아카이브에서 복사
cp -r archive/v1.0.0/cognitive_kernel.py .

# 또는 Git 태그 사용
git checkout v1.0.0
```

### 2. 버전 비교

```bash
# Git diff 사용
git diff v1.0.0 v2.0.1

# 또는 파일 직접 비교
diff archive/v1.0.0/cognitive_kernel.py archive/v2.0.1/src/cognitive_kernel/core.py
```

### 3. 버전별 문서 확인

```bash
# 특정 버전 README 확인
cat archive/v1.0.0/README.md

# CHANGELOG 확인
cat archive/v2.0.1/CHANGELOG.md
```

---

## 📝 아카이브 유지보수

### 정기 작업

1. **버전 업데이트 시**
   - 새 버전 아카이브 생성
   - README.md 작성
   - CHANGELOG.md 업데이트
   - PHAM 체인 복사

2. **월별 점검**
   - 아카이브 무결성 확인
   - PHAM 해시 검증
   - 문서 업데이트

3. **분기별 정리**
   - 오래된 버전 압축
   - 불필요한 파일 제거
   - 인덱스 업데이트

---

## 🔐 보안 고려사항

### PHAM 해시 검증

```python
import hashlib
import json

def verify_archive(archive_dir):
    """아카이브 무결성 검증"""
    metadata_path = f"{archive_dir}/metadata.json"
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    # 파일 해시 검증
    for file_path in find_files(archive_dir):
        calculated_hash = calculate_hash(file_path)
        # PHAM 체인과 비교
        ...
```

---

**마지막 업데이트**: 2026-01-31

