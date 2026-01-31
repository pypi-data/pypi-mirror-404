#!/usr/bin/env python3
"""
Dynamics Engine 기본 사용 예시
Basic Usage Example for Dynamics Engine

산업용/상업용 독립 모듈
Industrial/Commercial Standalone Module
"""

import time
from dynamics_engine import DynamicsEngine, DynamicsConfig


def main():
    """기본 사용 예시"""
    print("=" * 60)
    print("Dynamics Engine - Basic Usage Example")
    print("=" * 60)
    
    # 1. 엔진 생성
    print("\n1. 엔진 생성 (Engine Creation)")
    config = DynamicsConfig(
        base_gamma=0.3,
        omega=0.05,
    )
    dynamics = DynamicsEngine(config)
    print("   ✅ Dynamics Engine 생성 완료")
    
    # 2. 엔트로피 계산
    print("\n2. 엔트로피 계산 (Entropy Calculation)")
    probabilities = [0.3, 0.4, 0.3]
    entropy = dynamics.calculate_entropy(probabilities)
    print(f"   입력 (Input): {probabilities}")
    print(f"   출력 (Output): 엔트로피 = {entropy:.3f}")
    print(f"   수식 (Formula): E = -Σ P(k) ln P(k)")
    
    # 3. 코어 강도 계산
    print("\n3. 코어 강도 계산 (Core Strength Calculation)")
    memories = [
        {"importance": 0.9, "timestamp": time.time() - 3600},  # 1시간 전
        {"importance": 0.8, "timestamp": time.time() - 300},   # 5분 전
    ]
    core = dynamics.calculate_core_strength(memories)
    print(f"   입력 (Input): {len(memories)}개 기억")
    print(f"   출력 (Output): 코어 강도 = {core:.3f}")
    print(f"   수식 (Formula): C = α * (Σ importance) / N")
    
    # 4. 회전 토크 생성
    print("\n4. 회전 토크 생성 (Rotational Torque Generation)")
    options = ["rest", "work", "exercise"]
    torque = dynamics.generate_torque(options, entropy, mode="adhd")
    print(f"   입력 (Input): 옵션 {options}, 엔트로피 {entropy:.3f}, 모드 'adhd'")
    print(f"   출력 (Output): 회전 토크")
    for opt, t in torque.items():
        print(f"      {opt}: {t:+.3f}")
    print(f"   수식 (Formula): T(k) = γ * E_norm * cos(φ - ψ_k)")
    
    # 5. 인지적 절규 확인
    print("\n5. 인지적 절규 확인 (Cognitive Distress Detection)")
    is_distress, message = dynamics.check_cognitive_distress(
        entropy, core, len(options)
    )
    print(f"   입력 (Input): 엔트로피 {entropy:.3f}, 코어 강도 {core:.3f}")
    print(f"   출력 (Output): 절규 상태 = {is_distress}, 메시지 = '{message}'")
    
    # 6. 히스토리 관리
    print("\n6. 히스토리 관리 (History Management)")
    dynamics.update_history(entropy, core)
    print(f"   엔트로피 히스토리 길이: {len(dynamics.state.entropy_history)}")
    print(f"   코어 강도 히스토리 길이: {len(dynamics.state.core_strength_history)}")
    
    print("\n" + "=" * 60)
    print("✅ 모든 기능 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()

