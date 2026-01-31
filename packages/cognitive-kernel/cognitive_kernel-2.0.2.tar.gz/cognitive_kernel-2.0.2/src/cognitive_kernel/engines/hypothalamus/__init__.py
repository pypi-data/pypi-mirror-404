"""
Hypothalamus Engine Package
시상하부 엔진 - 산업용 동기 부여 및 에너지 관리 시스템 (소프트웨어 벤치마킹 단계)

⚠️ 현재 상태:
- 소프트웨어 시뮬레이션 및 벤치마킹 단계
- 물리적 하드웨어 테스트는 아직 완료되지 않음
- 계속 발전하는 구조 (테스트 과정과 계획된 업그레이드로 확장)

🔗 PHAM 블록체인 서명:
    이 패키지는 PHAM (Proof of Authorship & Merit) 블록체인 시스템으로 서명되어 있습니다.
    - 블록체인 체인: blockchain/pham_chain_*.json
    - 4-Signal Scoring: Byte(25%) + Text(35%) + AST(30%) + Exec(10%)
    - 수익 분배: 기여도에 따라 자동 분배
    - IPFS 저장: 모든 버전이 IPFS에 영구 보존됨
    - 자세한 내용: BLOCKCHAIN_INFO.md 참조

💰 기여도 원칙 (블록체인 기반):
    이 엔진은 오픈소스로 제공되며, 코드 재사용 시 로열티를 요구하지 않습니다.
    수익 발생 시점부터 코드/제품 기여도(상용화, 홍보, 마케팅, 판매 등)가 블록체인에 기록되어 합산되어 분배됩니다.
    이 시스템은 계속 업그레이드되어가는 구조입니다.
    ⚠️ GNJz의 기여도 원칙: 최초 코드 작성자 GNJz는 자신의 기여도가 총 기여도 중 6%를 넘지 않도록 제한합니다. 이것은 블록체인으로 검증 가능한 기여도 상한선입니다.

Author: GNJz (Qquarts)
Version: 1.0.0-alpha (Software Benchmarking Stage)
License: MIT License
Blockchain: PHAM v4 (Signed)
"""

from .hypothalamus_engine import HypothalamusEngine
from .config import HypothalamusConfig
from .data_types import (
    InternalState,
    DriveSignal,
    DriveType,
)
from .hpa_dynamics import (
    HPADynamics,
    HPAConfig,
    HPAState,
)

__all__ = [
    # 기존 엔진 (실용적 에너지/동기 관리)
    'HypothalamusEngine',
    'HypothalamusConfig',
    'InternalState',
    'DriveSignal',
    'DriveType',
    # 이론적 HPA 동역학 모듈
    'HPADynamics',
    'HPAConfig',
    'HPAState',
]

__version__ = '1.0.0-alpha'

