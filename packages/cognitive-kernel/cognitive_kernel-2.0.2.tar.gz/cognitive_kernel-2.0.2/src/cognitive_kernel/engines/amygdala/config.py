"""
Amygdala Engine Configuration
편도체 엔진 설정 클래스

모든 튜닝 가능한 파라미터는 여기에 집중
하드코딩 금지 원칙

Author: GNJz (Qquarts)
Version: 1.0.0-alpha
License: MIT License
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AmygdalaConfig:
    """
    편도체 엔진 설정
    
    모든 튜닝 가능한 파라미터는 여기에 집중
    하드코딩 금지 원칙
    """
    # 위협 감지 설정
    threat_threshold: float = 0.4  # 위협 임계값 (0~1)
    
    # 공포 학습 설정 (STDP)
    A_plus: float = 0.1  # LTP 강도
    A_minus: float = 0.05  # LTD 강도
    tau: float = 20.0  # 시간 상수 (ms)
    
    # 기억 강화 파라미터
    alpha: float = 0.5  # 감정-기억 연결 강도
    beta: float = 2.0  # 위협 민감도
    
    # 수면 소거 설정
    extinction_time_window: float = 3600.0  # 소거 시간 윈도우 (초, 기본 1시간)
    extinction_rate: float = 0.05  # 수면 중 소거율
    
    # 감정 관성 설정
    emotion_inertia: float = 0.3  # 이전 감정 유지 비율 (0~1)
    
    # 위협 키워드 (선택적 커스터마이징)
    threat_keywords: Optional[Dict] = None
    
    # 감정 맵 (선택적 커스터마이징)
    emotion_map: Optional[Dict] = None
    
    def __post_init__(self):
        """기본 키워드 및 감정 맵 설정"""
        if self.threat_keywords is None:
            self.threat_keywords = self._get_default_threat_keywords()
        
        if self.emotion_map is None:
            self.emotion_map = self._get_default_emotion_map()
    
    def _get_default_threat_keywords(self) -> Dict:
        """기본 위협 키워드"""
        return {
            'danger': {
                'words': ['위험', '죽고', '죽어', '죽을', '죽겠', '살인', '폭력', '공격', 
                         '위협', '무서', '두려', '공포', '겁나', '끔찍',
                         'danger', 'kill', 'death', 'die', 'attack', 'threat', 
                         'fear', 'scary', 'terrify', 'horror'],
                'weight': 1.0,
                'type': 'direct_threat'
            },
            'social': {
                'words': ['싫어', '미워', '혐오', '거부', '배신', '따돌림', '무시', 
                         '왕따', '욕', '비난', '모욕',
                         'hate', 'reject', 'betray', 'ignore', 'bully', 'insult'],
                'weight': 0.7,
                'type': 'social_threat'
            },
            'loss': {
                'words': ['잃어', '잃었', '손해', '실패', '망했', '끝났', '이별', '헤어',
                         '포기', '그만', '떠나',
                         'lose', 'lost', 'loss', 'fail', 'end', 'goodbye', 'leave'],
                'weight': 0.6,
                'type': 'loss_threat'
            },
            'uncertainty': {
                'words': ['불안', '걱정', '초조', '불확실', '혼란', '막막', '답답',
                         'anxious', 'worry', 'nervous', 'uncertain', 'confused'],
                'weight': 0.8,
                'type': 'uncertainty'
            },
            'self_harm': {
                'words': ['자살', '자해', '죽고싶', '죽고 싶', '살기싫', '살기 싫',
                         '사라지고싶', '사라지고 싶', '없어지고싶',
                         'suicide', 'self-harm', 'kill myself', 'want to die'],
                'weight': 1.5,
                'type': 'self_harm'
            }
        }
    
    def _get_default_emotion_map(self) -> Dict:
        """기본 감정 맵 (Russell's Circumplex Model)"""
        return {
            'excited': {'valence': 0.8, 'arousal': 0.8, 'words': ['신나', '흥분', '설레', 'excited', 'thrilled']},
            'happy': {'valence': 0.9, 'arousal': 0.5, 'words': ['행복', '기쁘', '좋아', '웃', 'happy', 'glad', 'joy']},
            'love': {'valence': 1.0, 'arousal': 0.6, 'words': ['사랑', '애정', '좋아해', 'love', 'adore']},
            'calm': {'valence': 0.5, 'arousal': 0.2, 'words': ['평화', '편안', '차분', 'calm', 'peaceful', 'relaxed']},
            'content': {'valence': 0.6, 'arousal': 0.3, 'words': ['만족', '충족', 'content', 'satisfied']},
            'angry': {'valence': -0.8, 'arousal': 0.9, 'words': ['화나', '화가', '분노', '짜증', '열받', '빡치', 'angry', 'furious', 'mad']},
            'fear': {'valence': -0.9, 'arousal': 0.8, 'words': ['무서', '두려', '공포', '겁', 'fear', 'scared', 'terrified']},
            'anxious': {'valence': -0.6, 'arousal': 0.7, 'words': ['불안', '걱정', '초조', 'anxious', 'worried', 'nervous']},
            'sad': {'valence': -0.8, 'arousal': 0.3, 'words': ['슬프', '우울', '눈물', '울', 'sad', 'depressed', 'cry']},
            'tired': {'valence': -0.3, 'arousal': 0.1, 'words': ['피곤', '지쳤', '힘들', 'tired', 'exhausted']},
            'bored': {'valence': -0.2, 'arousal': 0.2, 'words': ['지루', '심심', 'bored', 'boring']},
            'neutral': {'valence': 0.0, 'arousal': 0.3, 'words': []},
        }
    
    def validate(self) -> None:
        """
        설정 유효성 검증
        
        Raises:
            AssertionError: 설정이 유효하지 않은 경우
        """
        assert 0.0 <= self.threat_threshold <= 1.0, "threat_threshold must be in [0, 1]"
        assert self.A_plus > 0, "A_plus must be positive"
        assert self.A_minus > 0, "A_minus must be positive"
        assert self.tau > 0, "tau must be positive"
        assert 0.0 <= self.alpha <= 1.0, "alpha must be in [0, 1]"
        assert self.beta > 0, "beta must be positive"
        assert self.extinction_time_window > 0, "extinction_time_window must be positive"
        assert 0.0 <= self.extinction_rate <= 1.0, "extinction_rate must be in [0, 1]"
        assert 0.0 <= self.emotion_inertia <= 1.0, "emotion_inertia must be in [0, 1]"

