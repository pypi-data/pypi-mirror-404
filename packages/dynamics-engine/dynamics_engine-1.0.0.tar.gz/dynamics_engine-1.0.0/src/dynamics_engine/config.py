"""
Dynamics Engine Configuration
동역학 엔진 설정 클래스

산업용/상업용 독립 모듈
Industrial/Commercial Standalone Module

Author: GNJz (Qquarts)
License: MIT
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DynamicsConfig:
    """
    동역학 엔진 설정 (Dynamics Engine Configuration)
    
    산업용/상업용 설정 클래스
    Industrial/Commercial Configuration Class
    
    파라미터 설명 (Parameter Description):
    
    1. 회전 토크 설정 (Rotational Torque Settings):
        - base_gamma: 기본 회전 토크 세기 (Base rotational torque strength)
        - omega: 세차 속도 (Precession angular velocity)
    
    2. Core Decay 설정 (Core Decay Settings):
        - core_decay_rate: 코어 감쇠율 (초당) (Core decay rate, per second)
        - memory_update_failure: 새 기억 중요도 반영 실패율 (0~1)
          (New memory importance reflection failure rate, 0~1)
        - loop_integrity_decay: 루프 무결성 감쇠율 (0~1)
          (Loop integrity decay rate, 0~1)
    
    3. 시간축 분리 설정 (Time-axis Separation Settings):
        - old_memory_decay_rate: 오래된 기억 감쇠율 (초당)
          (Old memory decay rate, per second)
        - new_memory_decay_rate: 새 기억 감쇠율 (초당)
          (New memory decay rate, per second)
        - memory_age_threshold: 기억 나이 임계값 (초)
          (Memory age threshold, seconds)
    
    4. 인지적 절규 설정 (Cognitive Distress Settings):
        - entropy_threshold_ratio: 엔트로피 임계값 비율 (0~1)
          (Entropy threshold ratio, 0~1)
        - core_distress_threshold: 코어 절규 임계값 (0~1)
          (Core distress threshold, 0~1)
    
    5. 히스토리 설정 (History Settings):
        - history_size: 히스토리 최대 크기 (Maximum history size)
    
    6. 기억 영향 계수 (Memory Influence Coefficient):
        - memory_alpha: 기억 영향 계수 (0~1)
          (Memory influence coefficient, 0~1)
    
    수식 참고 (Formula Reference):
        - Core Decay: C(t) = C(0) * exp(-λ * Δt)
        - Old Memory Decay: importance *= exp(-λ_old * age)
        - New Memory Decay: importance *= exp(-λ_new * age)
    """
    
    # 회전 토크 설정 (Rotational Torque Settings)
    base_gamma: float = 0.3  # 기본 회전 토크 세기 (Base rotational torque strength)
    omega: float = 0.05  # 세차 속도 (Precession angular velocity)
    
    # Core Decay 설정 (Core Decay Settings)
    core_decay_rate: float = 0.0  # 코어 감쇠율 (초당) (Core decay rate, per second)
    memory_update_failure: float = 0.0  # 새 기억 중요도 반영 실패율 (0~1)
    loop_integrity_decay: float = 0.0  # 루프 무결성 감쇠율 (0~1)
    
    # 시간축 분리 (Time-axis Separation)
    old_memory_decay_rate: float = 0.0  # 오래된 기억 감쇠율 (초당)
    new_memory_decay_rate: float = 0.0  # 새 기억 감쇠율 (초당)
    memory_age_threshold: float = 3600.0  # 기억 나이 임계값 (초, 1시간)
    
    # 인지적 절규 설정 (Cognitive Distress Settings)
    entropy_threshold_ratio: float = 0.8  # 엔트로피 임계값 비율 (0~1)
    core_distress_threshold: float = 0.3  # 코어 절규 임계값 (0~1)
    
    # 히스토리 설정 (History Settings)
    history_size: int = 100  # 히스토리 최대 크기 (Maximum history size)
    
    # 기억 영향 계수 (Memory Influence Coefficient)
    memory_alpha: float = 0.5  # 기억 영향 계수 (코어 강도 계산용)
    
    def validate(self) -> None:
        """
        설정 유효성 검증 (Configuration Validation)
        
        모든 파라미터가 유효한 범위 내에 있는지 확인
        Checks if all parameters are within valid ranges
        """
        assert 0.0 <= self.base_gamma <= 1.0, "base_gamma must be in [0, 1]"
        assert self.omega > 0, "omega must be positive"
        assert self.core_decay_rate >= 0, "core_decay_rate must be non-negative"
        assert 0.0 <= self.memory_update_failure <= 1.0, "memory_update_failure must be in [0, 1]"
        assert 0.0 <= self.loop_integrity_decay <= 1.0, "loop_integrity_decay must be in [0, 1]"
        assert self.old_memory_decay_rate >= 0, "old_memory_decay_rate must be non-negative"
        assert self.new_memory_decay_rate >= 0, "new_memory_decay_rate must be non-negative"
        assert self.memory_age_threshold > 0, "memory_age_threshold must be positive"
        assert 0.0 <= self.entropy_threshold_ratio <= 1.0, "entropy_threshold_ratio must be in [0, 1]"
        assert 0.0 <= self.core_distress_threshold <= 1.0, "core_distress_threshold must be in [0, 1]"
        assert self.history_size > 0, "history_size must be positive"
        assert 0.0 <= self.memory_alpha <= 1.0, "memory_alpha must be in [0, 1]"
