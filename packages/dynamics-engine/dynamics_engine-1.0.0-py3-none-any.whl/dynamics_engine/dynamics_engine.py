"""
Dynamics Engine - Cognitive Dynamics Engine
동역학 엔진 - 인지 동역학 엔진

산업용/상업용 독립 모듈
Industrial/Commercial Standalone Module

엔트로피, 코어 강도, 회전 토크 계산 및 Core Decay 동역학 처리.
Entropy, Core Strength, Rotational Torque calculation and Core Decay dynamics.

핵심 개념 (Core Concepts):
- 엔트로피 (Entropy): 선택의 불확실성 측정
- 코어 강도 (Core Strength): 기억의 중력 (엔트로피를 수렴시키는 힘)
- 회전 토크 (Rotational Torque): 엔트로피 기반 자동 회전
- Core Decay: 시간에 따른 중력 붕괴 (치매/알츠하이머 모델링)
- 시간축 분리 (Time-axis Separation): 오래된 기억 vs 새 기억

수학적 기반 (Mathematical Foundation):
- 정보 이론 (Information Theory): 엔트로피 계산
- 동역학 시스템 (Dynamical Systems): Core Decay 모델링
- 회전 운동 (Rotational Motion): 세차운동 (Precession)
- 지수 감쇠 (Exponential Decay): 시간축 분리

Author: GNJz (Qquarts)
License: MIT
Version: 1.0.0
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Tuple, Any, Union

from .config import DynamicsConfig
from .models import DynamicsState


class DynamicsEngine:
    """
    동역학 엔진 (Dynamics Engine)
    
    산업용/상업용 독립 모듈
    Industrial/Commercial Standalone Module
    
    역할 (Roles):
    - 엔트로피 계산 (Entropy Calculation)
    - 코어 강도 계산 (Core Strength Calculation) - Core Decay 포함
    - 회전 토크 생성 (Rotational Torque Generation)
    - 인지적 절규 확인 (Cognitive Distress Detection)
    - 상태 관리 (State Management) - 히스토리 포함
    
    수학적 기반 (Mathematical Foundation):
    - 정보 이론: E = -Σ P(k) ln P(k)
    - 동역학 시스템: C(t) = C(0) * exp(-λ * Δt)
    - 회전 운동: T(k) = γ * E_norm * cos(φ - ψ_k)
    - 지수 감쇠: importance *= exp(-λ * age)
    
    독립 배포 가능 (Standalone Deployment):
    - 표준 라이브러리만 사용 (Standard library only)
    - 외부 의존성 없음 (No external dependencies)
    - Edge AI 지원 (Edge AI compatible)
    """
    
    def __init__(self, config: Optional[DynamicsConfig] = None):
        """
        동역학 엔진 초기화
        
        Args:
            config: 동역학 엔진 설정 (None이면 기본값 사용)
                   Dynamics engine configuration (default if None)
        """
        self.config = config or DynamicsConfig()
        self.config.validate()
        self.state = DynamicsState()
    
    def calculate_entropy(self, probabilities: List[float]) -> float:
        """
        엔트로피 계산 (Entropy Calculation)
        
        정보 이론 기반 엔트로피 계산
        Information-theoretic entropy calculation
        
        수식 (Formula):
            E = -Σ P(k) ln P(k)
        
        여기서:
            E: 엔트로피 (Entropy)
            P(k): k번째 선택의 확률 (Probability of k-th choice)
            ln: 자연 로그 (Natural logarithm)
        
        물리적 의미 (Physical Meaning):
            - 엔트로피가 높음 = 선택이 불확실함 (High entropy = uncertain choice)
            - 엔트로피가 낮음 = 선택이 확정적임 (Low entropy = certain choice)
            - 최대 엔트로피 = ln(N) (균등 분포) (Max entropy = ln(N) for uniform distribution)
        
        Args:
            probabilities: 확률 분포 리스트 (List of probabilities)
                          각 값은 0~1 사이, 합은 1에 가까워야 함
                          Each value should be between 0 and 1, sum should be close to 1
            
        Returns:
            엔트로피 값 (Entropy value)
            범위: 0 ~ ln(N), 여기서 N은 선택 수
            Range: 0 ~ ln(N), where N is the number of choices
        
        Example:
            >>> dynamics = DynamicsEngine()
            >>> entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
            >>> print(f"Entropy: {entropy:.3f}")
            Entropy: 1.089
        """
        entropy = 0.0
        for prob in probabilities:
            if prob > 0:
                entropy -= prob * math.log(prob)
        
        self.state.entropy = entropy
        return entropy
    
    def calculate_core_strength(
        self,
        memories: List[Dict[str, Any]],
        memory_update_failure: float = 0.0,
        alpha: Optional[float] = None,
    ) -> float:
        """
        코어 강도 계산 (Core Strength Calculation)
        
        Core Decay 동역학 적용 및 시간축 분리
        Core Decay dynamics with time-axis separation
        
        핵심 개념 (Core Concept):
            코어 강도 = 기억의 중력 (Core Strength = Memory Gravity)
            엔트로피를 다시 모이게 하는 힘 (Force that reconverges entropy)
        
        수식 (Formulas):
            1. 원시 코어 (Raw Core):
                C_raw = α * (Σ importance) / N
            
            2. Core Decay (시간에 따른 중력 붕괴):
                C(t) = C(0) * exp(-λ * Δt)
            
            3. 시간축 분리 (Time-axis Separation):
                오래된 기억 감쇠: importance *= exp(-λ_old * age)
                새 기억 감쇠: importance *= exp(-λ_new * age)
            
            4. Memory Update Failure (알츠하이머):
                total_importance *= (1.0 - memory_update_failure)
        
        여기서:
            C: 코어 강도 (Core Strength)
            α: 기억 영향 계수 (Memory influence coefficient)
            λ: 감쇠율 (Decay rate, 초당)
            Δt: 시간 경과 (Time elapsed, 초)
            age: 기억 나이 (Memory age, 초)
            λ_old: 오래된 기억 감쇠율 (Old memory decay rate)
            λ_new: 새 기억 감쇠율 (New memory decay rate)
        
        물리적 의미 (Physical Meaning):
            - 코어 강도가 높음 = 기억이 강함, 엔트로피를 수렴시킬 수 있음
              (High core strength = strong memory, can reconverge entropy)
            - 코어 강도가 낮음 = 기억이 약함, 엔트로피가 퍼짐 (치매/알츠하이머)
              (Low core strength = weak memory, entropy spreads - dementia/Alzheimer's)
        
        치매/알츠하이머 모델링 (Dementia/Alzheimer's Modeling):
            - 치매 (Dementia): 오래된 기억 감쇠 (λ_old > 0), 새 기억 정상 (λ_new = 0)
            - 알츠하이머 (Alzheimer's): 새 기억 즉시 감쇠 (λ_new >> 0), 오래된 기억 느리게 감쇠
        
        Args:
            memories: 기억 리스트 (List of memories)
                     각 기억은 다음 키를 포함해야 함:
                     Each memory should contain:
                     - importance: 중요도 (0~1) (Importance, 0~1)
                     - timestamp: 타임스탬프 (초) (Timestamp in seconds)
            
            memory_update_failure: 새 기억 중요도 반영 실패율 (0~1)
                                  New memory importance reflection failure rate (0~1)
                                  0 = 정상 (Normal)
                                  1 = 새 기억이 코어에 전혀 기여하지 못함 (New memories don't contribute)
            
            alpha: 기억 영향 계수 (None이면 config에서 가져옴)
                   Memory influence coefficient (from config if None)
        
        Returns:
            코어 강도 (0~1) (Core Strength, 0~1)
        
        Example:
            >>> memories = [
            ...     {"importance": 0.9, "timestamp": time.time() - 3600},
            ...     {"importance": 0.8, "timestamp": time.time() - 300},
            ... ]
            >>> core = dynamics.calculate_core_strength(memories)
            >>> print(f"Core Strength: {core:.3f}")
            Core Strength: 0.425
        """
        if alpha is None:
            alpha = self.config.memory_alpha
        
        # 1. 현재 원시 코어 강도 계산 (시간축 분리 적용)
        # Calculate raw core strength with time-axis separation
        current_raw_core = 0.0
        if memories:
            current_time = time.time()
            total_importance = 0.0
            
            for m in memories:
                importance = m.get("importance", 0.0)
                
                # 시간축 분리: 오래된 기억 vs 새 기억
                # Time-axis separation: old memories vs new memories
                memory_timestamp = m.get("timestamp", current_time)
                memory_age = current_time - memory_timestamp
                
                # 오래된 기억 감쇠 (치매 특성: 최근 기억부터 지워짐)
                # Old memory decay (Dementia characteristic: recent memories erased first)
                if self.config.old_memory_decay_rate > 0 and memory_age > self.config.memory_age_threshold:
                    # 오래된 기억: 더 빠른 감쇠
                    # Old memories: faster decay
                    # 수식: importance *= exp(-λ_old * age)
                    decay_factor = math.exp(-self.config.old_memory_decay_rate * memory_age)
                    importance *= decay_factor
                
                # 새 기억 감쇠 (알츠하이머 특성: 새 기억이 전혀 저장되지 않음)
                # New memory decay (Alzheimer's characteristic: new memories not stored)
                if self.config.new_memory_decay_rate > 0 and memory_age <= self.config.memory_age_threshold:
                    # 새 기억: 매우 빠른 감쇠 (거의 즉시 소실)
                    # New memories: very fast decay (almost immediate loss)
                    # 수식: importance *= exp(-λ_new * age)
                    decay_factor = math.exp(-self.config.new_memory_decay_rate * memory_age)
                    importance *= decay_factor
                
                total_importance += importance
            
            # 새 기억의 중요도 반영 차단 (알츠하이머)
            # Block new memory importance reflection (Alzheimer's)
            if memory_update_failure > 0:
                total_importance *= (1.0 - memory_update_failure)
            
            current_raw_core = min(
                1.0, alpha * total_importance / len(memories) if memories else 0.0
            )
        
        # 2. Core Decay (물리적 시간 붕괴 항 적용)
        # Core Decay (Physical time decay term)
        # 수식: C(t) = C(0) * exp(-λ * Δt)
        # Formula: C(t) = C(0) * exp(-λ * Δt)
        if self.config.core_decay_rate > 0:
            # 초기화 (Initialization)
            if self.state.persistent_core is None:
                self.state.persistent_core = current_raw_core
                self.state.last_decay_time = time.time()
            
            # 시간 경과 계산 (Time elapsed calculation)
            delta_t = time.time() - self.state.last_decay_time
            lambda_decay = self.config.core_decay_rate
            
            # 지수 감쇠 적용 (Exponential decay application)
            # 수식: C(t) = C(0) * exp(-λ * Δt)
            self.state.persistent_core *= math.exp(-lambda_decay * delta_t)
            core_strength = self.state.persistent_core
            self.state.last_decay_time = time.time()
        else:
            # 정상 모드: 원시 코어 강도 사용
            # Normal mode: use raw core strength
            core_strength = current_raw_core
            self.state.persistent_core = None
            self.state.last_decay_time = None
        
        self.state.core_strength = core_strength
        return core_strength
    
    def generate_torque(
        self,
        options: List[str],
        entropy: float,
        mode: Optional[Union[str, Any]] = None,
        base_gamma: Optional[float] = None,
        omega: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        회전 토크 생성 (Rotational Torque Generation)
        
        엔트로피 기반 자동 회전 토크 생성
        Entropy-based automatic rotational torque generation
        
        핵심 개념 (Core Concept):
            엔트로피가 높을수록 더 강한 회전 토크 생성
            Higher entropy generates stronger rotational torque
            선택 분포를 회전시켜 탐색을 유도
            Rotates choice distribution to induce exploration
        
        수식 (Formulas):
            1. 정규화된 엔트로피 (Normalized Entropy):
                E_norm = E / E_max
                여기서 E_max = ln(N) (균등 분포)
                where E_max = ln(N) (uniform distribution)
            
            2. 토크 세기 (Torque Strength):
                T = γ * E_norm
                여기서 γ는 회전 토크 세기 계수
                where γ is the rotational torque strength coefficient
            
            3. 회전 토크 (Rotational Torque):
                T(k) = T * cos(φ - ψ_k)
                여기서:
                    φ: 세차 위상 (Precession phase)
                    ψ_k: k번째 옵션의 위상 (Phase of k-th option)
                    cos: 코사인 함수 (Cosine function)
            
            4. 위상 업데이트 (Phase Update):
                φ(t+1) = φ(t) + ω
                여기서 ω는 세차 속도 (Precession angular velocity)
                where ω is the precession angular velocity
        
        물리적 의미 (Physical Meaning):
            - 토크가 양수 = 해당 옵션을 선택하도록 유도
              (Positive torque = induces selection of that option)
            - 토크가 음수 = 해당 옵션을 피하도록 유도
              (Negative torque = induces avoidance of that option)
            - 세차운동 (Precession): 선택 분포가 느리게 회전하는 현상
              (Precession: slow rotation of choice distribution)
        
        모드별 차이 (Mode Differences):
            - ADHD 모드: 더 강한 회전 (γ × 1.5)
              (ADHD mode: stronger rotation, γ × 1.5)
            - ASD 모드: 약한 회전 (γ × 0.5)
              (ASD mode: weaker rotation, γ × 0.5)
            - Normal 모드: 기본 회전 (γ)
              (Normal mode: default rotation, γ)
        
        Args:
            options: 옵션 리스트 (List of options)
            
            entropy: 현재 엔트로피 (Current entropy)
            
            mode: 인지 모드 (Cognitive mode)
                 문자열: "adhd", "asd", "normal" 등
                 또는 CognitiveMode 객체 (선택적 의존성)
                 String: "adhd", "asd", "normal", etc.
                 Or CognitiveMode object (optional dependency)
            
            base_gamma: 기본 회전 토크 세기 (None이면 config에서 가져옴)
                        Base rotational torque strength (from config if None)
            
            omega: 세차 속도 (None이면 config에서 가져옴)
                   Precession angular velocity (from config if None)
        
        Returns:
            옵션별 회전 토크 딕셔너리 (Dictionary of rotational torques per option)
            {option: torque_value}
        
        Example:
            >>> entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
            >>> torque = dynamics.generate_torque(
            ...     ["rest", "work", "exercise"],
            ...     entropy,
            ...     mode="adhd"
            ... )
            >>> print(torque)
            {'rest': 0.446, 'work': -0.223, 'exercise': -0.223}
        """
        if len(options) <= 1:
            return {}
        
        if base_gamma is None:
            base_gamma = self.config.base_gamma
        if omega is None:
            omega = self.config.omega
        
        # 모드별 gamma 조정 (100% 독립 배포 - CognitiveMode 의존성 완전 제거)
        # Mode-based gamma adjustment (100% standalone - CognitiveMode dependency completely removed)
        gamma = base_gamma
        if mode is not None:
            # 문자열 모드 처리 (String mode processing)
            if isinstance(mode, str):
                mode_str = mode.lower()
                if mode_str == "adhd" or "adhd" in mode_str:
                    gamma = base_gamma * 1.5  # ADHD: 더 강한 회전 (Stronger rotation)
                elif mode_str == "asd" or "asd" in mode_str:
                    gamma = base_gamma * 0.5  # ASD: 약한 회전 (Weaker rotation)
            # 객체 모드 처리 (객체의 문자열 표현 사용)
            # Object mode processing (use string representation of object)
            else:
                # 객체를 문자열로 변환하여 처리 (Convert object to string for processing)
                mode_str = str(mode).lower()
                if "adhd" in mode_str:
                    gamma = base_gamma * 1.5
                elif "asd" in mode_str:
                    gamma = base_gamma * 0.5
                # CognitiveMode 객체도 문자열로 변환되면 "CognitiveMode.ADHD" 형태가 되므로
                # "adhd" 또는 "asd"가 포함되어 있으면 자동으로 처리됨
                # CognitiveMode objects convert to strings like "CognitiveMode.ADHD",
                # so they are automatically processed if "adhd" or "asd" is contained
        
        # 이론적 최대 엔트로피 (균등 분포)
        # Theoretical maximum entropy (uniform distribution)
        # 수식: E_max = ln(N)
        max_entropy = math.log(len(options))
        
        # 정규화된 엔트로피 (0~1)
        # Normalized entropy (0~1)
        # 수식: E_norm = E / E_max
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        
        # 토크 세기
        # Torque strength
        # 수식: T = γ * E_norm
        torque_strength = gamma * normalized_entropy
        
        # 옵션별 위상 (균등 분포)
        # Phase per option (uniform distribution)
        # 수식: ψ_k = k * 2π / N
        psi = {
            opt: i * 2 * math.pi / len(options)
            for i, opt in enumerate(options)
        }
        
        # 회전 토크 계산: T(k) = torque_strength * cos(φ - ψ_k)
        # Rotational torque calculation: T(k) = torque_strength * cos(φ - ψ_k)
        auto_torque = {}
        for opt in options:
            auto_torque[opt] = torque_strength * math.cos(
                self.state.precession_phi - psi[opt]
            )
        
        # 위상 업데이트 (느린 시간척도)
        # Phase update (slow timescale)
        # 수식: φ(t+1) = φ(t) + ω
        self.state.precession_phi += omega
        
        # 2π 주기로 정규화
        # Normalize to 2π period
        if self.state.precession_phi >= 2 * math.pi:
            self.state.precession_phi -= 2 * math.pi
        
        return auto_torque
    
    def check_cognitive_distress(
        self,
        entropy: float,
        core_strength: float,
        num_options: int,
    ) -> Tuple[bool, str]:
        """
        인지적 절규 확인 (Cognitive Distress Detection)
        
        엔트로피가 높은데 코어 강도가 낮은 상태 감지
        Detects state where entropy is high but core strength is low
        
        핵심 개념 (Core Concept):
            "기억이 안 나..." 상태를 감지
            Detects "I can't remember..." state
        
        수식 (Formula):
            조건 (Condition):
                E > E_threshold AND C < C_threshold
            
            여기서:
                E_threshold = E_max * ratio
                E_max = ln(N)
                C_threshold = 0.3 (기본값)
        
        물리적 의미 (Physical Meaning):
            - 엔트로피가 높음 = 선택이 불확실함
              (High entropy = uncertain choice)
            - 코어 강도가 낮음 = 기억이 약함
              (Low core strength = weak memory)
            - 둘 다 만족 = "기억이 안 나는" 상태 (치매/알츠하이머)
              (Both satisfied = "can't remember" state - dementia/Alzheimer's)
        
        Args:
            entropy: 현재 엔트로피 (Current entropy)
            
            core_strength: 현재 코어 강도 (Current core strength)
            
            num_options: 옵션 수 (Number of options)
        
        Returns:
            (절규 여부, 메시지) 튜플
            (distress_status, message) tuple
            - distress_status: True = 절규 상태, False = 정상
            - message: 절규 메시지 (절규 상태일 때만)
        
        Example:
            >>> is_distress, message = dynamics.check_cognitive_distress(
            ...     entropy=1.5,
            ...     core_strength=0.2,
            ...     num_options=3
            ... )
            >>> print(f"Distress: {is_distress}, Message: '{message}'")
            Distress: True, Message: '기억이 안 나...'
        """
        if num_options <= 1:
            self.state.cognitive_distress = False
            return False, ""
        
        # 최대 엔트로피 계산
        # Calculate maximum entropy
        # 수식: E_max = ln(N)
        max_entropy = math.log(num_options)
        
        # 엔트로피 임계값 계산
        # Calculate entropy threshold
        # 수식: E_threshold = E_max * ratio
        entropy_threshold = max_entropy * self.config.entropy_threshold_ratio
        
        # 절규 조건 확인
        # Check distress condition
        # 조건: E > E_threshold AND C < C_threshold
        if entropy > entropy_threshold and core_strength < self.config.core_distress_threshold:
            self.state.cognitive_distress = True
            return True, "기억이 안 나..."
        else:
            self.state.cognitive_distress = False
            return False, ""
    
    def update_history(self, entropy: float, core_strength: float) -> None:
        """
        히스토리 업데이트 (History Update)
        
        엔트로피와 코어 강도의 시간 변화 추적
        Tracks time evolution of entropy and core strength
        
        최근 N개 값만 유지 (기본 100개)
        Maintains only recent N values (default 100)
        
        Args:
            entropy: 엔트로피 값 (Entropy value)
            
            core_strength: 코어 강도 값 (Core strength value)
        
        Example:
            >>> dynamics.update_history(entropy=1.2, core_strength=0.5)
            >>> print(f"History length: {len(dynamics.state.entropy_history)}")
            History length: 1
        """
        self.state.entropy_history.append(entropy)
        if len(self.state.entropy_history) > self.config.history_size:
            self.state.entropy_history = self.state.entropy_history[-self.config.history_size:]
        
        self.state.core_strength_history.append(core_strength)
        if len(self.state.core_strength_history) > self.config.history_size:
            self.state.core_strength_history = self.state.core_strength_history[-self.config.history_size:]
    
    def reset(self) -> None:
        """
        상태 초기화 (State Reset)
        
        모든 상태 변수를 초기값으로 리셋
        Resets all state variables to initial values
        """
        self.state.reset()
    
    def get_state(self) -> DynamicsState:
        """
        상태 조회 (Get State)
        
        Returns:
            현재 상태 객체 (Current state object)
        """
        return self.state
    
    def get_status(self) -> Dict[str, Any]:
        """
        상태 정보 조회 (Get Status)
        
        Returns:
            상태 정보 딕셔너리 (Status information dictionary)
        """
        return {
            "entropy": self.state.entropy,
            "core_strength": self.state.core_strength,
            "precession_phi": self.state.precession_phi,
            "cognitive_distress": self.state.cognitive_distress,
            "entropy_history_length": len(self.state.entropy_history),
            "core_strength_history_length": len(self.state.core_strength_history),
        }
