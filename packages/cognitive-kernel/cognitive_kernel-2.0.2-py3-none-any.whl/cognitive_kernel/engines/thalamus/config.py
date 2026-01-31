"""
Thalamus Engine Configuration
시상 엔진 설정 클래스

모든 튜닝 가능한 파라미터는 여기에 집중
하드코딩 금지 원칙

Author: GNJz (Qquarts)
Version: 1.0.0
License: MIT License
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ThalamusConfig:
    """
    시상 엔진 설정
    
    모든 튜닝 가능한 파라미터는 여기에 집중
    하드코딩 금지 원칙
    """
    # 게이팅 설정
    gate_threshold: float = 0.3  # 게이트 임계값 (0~1)
    
    # 현저성 설정
    salience_boost: float = 1.5  # 현저성 부스트 배수
    novelty_bonus: float = 0.3  # 신규성 보너스 (0~1)
    
    # 주의 설정
    attention_decay: float = 0.1  # 주의 감쇠율
    focus_boost: float = 1.5  # 포커스 부스트 배수
    auto_decay_scale: float = 0.1  # 자동 감쇠 스케일
    
    # 채널 제한
    max_channels: int = 3  # 최대 통과 채널 수
    
    # 입력 기록
    recent_inputs_maxlen: int = 50  # 최근 입력 기록 최대 길이
    
    # 에너지 기반 게이팅 (선택적)
    energy_deficit_threshold: float = 0.5  # 에너지 부족 임계값
    energy_deficit_boost: float = 0.5  # 에너지 부족 시 임계값 증가율
    
    # 현저성 패턴 (주의를 끄는 키워드)
    salient_patterns: Optional[Dict[str, List[str]]] = None
    
    def __post_init__(self):
        """기본 패턴 설정"""
        if self.salient_patterns is None:
            self.salient_patterns = {
                'threat': ['위험', '죽', '공격', 'danger', 'kill', 'attack'],
                'name': ['이름', '너', '당신', 'name', 'you'],
                'question': ['?', '뭐', '왜', '어떻게', 'what', 'why', 'how'],
                'reward': ['좋아', '칭찬', '감사', 'good', 'thanks', 'great'],
            }
    
    def validate(self) -> None:
        """
        설정 유효성 검증
        
        Raises:
            AssertionError: 설정이 유효하지 않은 경우
        """
        assert 0.0 <= self.gate_threshold <= 1.0, "gate_threshold must be in [0, 1]"
        assert self.salience_boost > 0, "salience_boost must be positive"
        assert 0.0 <= self.novelty_bonus <= 1.0, "novelty_bonus must be in [0, 1]"
        assert 0.0 <= self.attention_decay <= 1.0, "attention_decay must be in [0, 1]"
        assert self.focus_boost > 0, "focus_boost must be positive"
        assert self.max_channels > 0, "max_channels must be positive"
        assert self.recent_inputs_maxlen > 0, "recent_inputs_maxlen must be positive"
        assert 0.0 <= self.energy_deficit_threshold <= 1.0, "energy_deficit_threshold must be in [0, 1]"
        assert self.energy_deficit_boost >= 0, "energy_deficit_boost must be non-negative"

