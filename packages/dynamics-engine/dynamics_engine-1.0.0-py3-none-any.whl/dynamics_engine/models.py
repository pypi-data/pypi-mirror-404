"""
Dynamics Engine State Models
동역학 엔진 상태 모델

산업용/상업용 독립 모듈
Industrial/Commercial Standalone Module

Author: GNJz (Qquarts)
License: MIT
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DynamicsState:
    """
    동역학 엔진 상태 (Dynamics Engine State)
    
    산업용/상업용 상태 모델
    Industrial/Commercial State Model
    
    상태 변수 설명 (State Variable Description):
    
    1. 현재 상태 (Current State):
        - entropy: 현재 엔트로피 (Current entropy)
        - core_strength: 현재 코어 강도 (Current core strength)
        - precession_phi: 세차 위상 (0 ~ 2π) (Precession phase, 0 ~ 2π)
    
    2. Core Decay 상태 (Core Decay State):
        - persistent_core: 지속 코어 강도 (Core Decay용)
          (Persistent core strength, for Core Decay)
        - last_decay_time: 마지막 감쇠 시간 (초)
          (Last decay time, in seconds)
    
    3. 인지적 절규 상태 (Cognitive Distress State):
        - cognitive_distress: 인지적 절규 여부 (True/False)
          (Cognitive distress status, True/False)
    
    4. 히스토리 (History):
        - entropy_history: 엔트로피 히스토리 (Entropy history)
        - core_strength_history: 코어 강도 히스토리 (Core strength history)
    
    수식 참고 (Formula Reference):
        - 엔트로피: E = -Σ P(k) ln P(k)
        - 코어 강도: C(t) = C(0) * exp(-λ * Δt)
        - 세차 위상: φ(t+1) = φ(t) + ω
    """
    
    # 현재 상태 (Current State)
    entropy: float = 0.0  # 현재 엔트로피 (Current entropy)
    core_strength: float = 0.0  # 현재 코어 강도 (Current core strength)
    precession_phi: float = 0.0  # 세차 위상 (0 ~ 2π) (Precession phase, 0 ~ 2π)
    
    # Core Decay 상태 (Core Decay State)
    persistent_core: Optional[float] = None  # 지속 코어 강도 (Persistent core strength)
    last_decay_time: Optional[float] = None  # 마지막 감쇠 시간 (Last decay time)
    
    # 인지적 절규 상태 (Cognitive Distress State)
    cognitive_distress: bool = False  # 인지적 절규 여부 (Cognitive distress status)
    
    # 히스토리 (History)
    entropy_history: List[float] = field(default_factory=list)  # 엔트로피 히스토리
    core_strength_history: List[float] = field(default_factory=list)  # 코어 강도 히스토리
    
    def reset(self) -> None:
        """
        상태 초기화 (State Reset)
        
        모든 상태 변수를 초기값으로 리셋
        Resets all state variables to initial values
        """
        self.entropy = 0.0
        self.core_strength = 0.0
        self.precession_phi = 0.0
        self.persistent_core = None
        self.last_decay_time = None
        self.cognitive_distress = False
        self.entropy_history.clear()
        self.core_strength_history.clear()
    
    def to_dict(self) -> dict:
        """
        딕셔너리로 변환 (Convert to Dictionary)
        
        Returns:
            상태 정보 딕셔너리 (State information dictionary)
        """
        return {
            "entropy": self.entropy,
            "core_strength": self.core_strength,
            "precession_phi": self.precession_phi,
            "persistent_core": self.persistent_core,
            "last_decay_time": self.last_decay_time,
            "cognitive_distress": self.cognitive_distress,
            "entropy_history_length": len(self.entropy_history),
            "core_strength_history_length": len(self.core_strength_history),
        }
