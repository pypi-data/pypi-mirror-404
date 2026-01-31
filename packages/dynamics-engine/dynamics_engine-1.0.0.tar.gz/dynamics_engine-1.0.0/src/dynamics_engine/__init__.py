"""
Dynamics Engine - Cognitive Dynamics Engine
동역학 엔진 - 인지 동역학 엔진

산업용/상업용 독립 모듈
Industrial/Commercial Standalone Module

엔트로피, 코어 강도, 회전 토크 계산 및 Core Decay 동역학 처리.
Entropy, Core Strength, Rotational Torque calculation and Core Decay dynamics.

🔗 Edge AI 지원:
    독립적으로 사용 가능한 동역학 엔진
    Standalone dynamics engine for Edge AI deployment

Author: GNJz (Qquarts)
License: MIT
Version: 1.0.0
"""

from .config import DynamicsConfig
from .models import DynamicsState
from .dynamics_engine import DynamicsEngine

__all__ = [
    "DynamicsConfig",
    "DynamicsState",
    "DynamicsEngine",
]

__version__ = "1.0.0"
__author__ = "GNJz (Qquarts)"
__license__ = "MIT"

