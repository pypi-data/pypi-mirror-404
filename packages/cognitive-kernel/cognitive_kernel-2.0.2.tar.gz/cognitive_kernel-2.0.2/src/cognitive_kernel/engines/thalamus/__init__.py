"""
Thalamus Engine
시상 엔진 - 산업용 센서 데이터 필터링 시스템 (소프트웨어 벤치마킹 단계)

⚠️ 현재 상태:
- 소프트웨어 시뮬레이션 및 벤치마킹 단계
- 물리적 하드웨어 테스트는 아직 완료되지 않음
- 계속 발전하는 구조 (테스트 과정과 계획된 업그레이드로 확장)

예상 핵심 기능:
- 감각 입력 필터링
- 주의 게이팅 (에너지 기반)
- 동적 임계값 조절
- 채널 제한

🔗 PHAM 블록체인 서명:
    이 패키지는 PHAM (Proof of Authorship & Merit) 블록체인 시스템으로 서명되어 있습니다.
    - 블록체인 체인: blockchain/pham_chain_*.json
    - 4-Signal Scoring: Byte(25%) + Text(35%) + AST(30%) + Exec(10%)
    - 기여도 분배: 오픈소스이며 코드 재사용 시 로열티 요구 없음. 수익 발생 시 블록체인으로 계산된 기여도에 따라 분배 (업그레이드 가능한 구조)
    - ⚠️ GNJz의 기여도 원칙: 최초 코드 작성자 GNJz는 자신의 기여도가 총 기여도 중 6%를 넘지 않도록 제한합니다 (블록체인 검증 가능)
    - IPFS 저장: 모든 버전이 IPFS에 영구 보존됨
    - 자세한 내용: BLOCKCHAIN_INFO.md 참조

Author: GNJz (Qquarts)
Version: 1.0.0-alpha (Software Benchmarking Stage)
License: MIT License
Blockchain: PHAM v4 (Signed)
"""

from .thalamus_engine import ThalamusEngine
from .config import ThalamusConfig
from .data_types import SensoryInput, FilteredOutput, ModalityType

__all__ = [
    'ThalamusEngine',
    'ThalamusConfig',
    'SensoryInput',
    'FilteredOutput',
    'ModalityType',
]

__version__ = "1.0.0"

