"""
Dynamics Engine 테스트
Dynamics Engine Tests

산업용/상업용 독립 모듈
Industrial/Commercial Standalone Module
"""

import time
import pytest
from dynamics_engine import DynamicsEngine, DynamicsConfig, DynamicsState


class TestDynamicsEngine:
    """Dynamics Engine 테스트 클래스"""
    
    def test_initialization(self):
        """초기화 테스트"""
        dynamics = DynamicsEngine()
        assert dynamics.config is not None
        assert dynamics.state is not None
    
    def test_calculate_entropy(self):
        """엔트로피 계산 테스트"""
        dynamics = DynamicsEngine()
        
        # 균등 분포
        entropy = dynamics.calculate_entropy([0.5, 0.5])
        assert entropy > 0
        
        # 확정적 분포
        entropy = dynamics.calculate_entropy([1.0, 0.0])
        assert entropy == 0.0
    
    def test_calculate_core_strength(self):
        """코어 강도 계산 테스트"""
        dynamics = DynamicsEngine()
        
        memories = [
            {"importance": 0.9, "timestamp": time.time()},
            {"importance": 0.8, "timestamp": time.time()},
        ]
        
        core = dynamics.calculate_core_strength(memories)
        assert 0.0 <= core <= 1.0
    
    def test_generate_torque(self):
        """회전 토크 생성 테스트"""
        dynamics = DynamicsEngine()
        
        entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
        options = ["rest", "work", "exercise"]
        
        torque = dynamics.generate_torque(options, entropy, mode="adhd")
        assert len(torque) == len(options)
        assert all(isinstance(v, float) for v in torque.values())
    
    def test_check_cognitive_distress(self):
        """인지적 절규 확인 테스트"""
        dynamics = DynamicsEngine()
        
        # 정상 상태
        is_distress, message = dynamics.check_cognitive_distress(
            entropy=0.5,
            core_strength=0.8,
            num_options=3
        )
        assert is_distress == False
        
        # 절규 상태
        is_distress, message = dynamics.check_cognitive_distress(
            entropy=2.0,
            core_strength=0.2,
            num_options=3
        )
        assert is_distress == True
        assert message == "기억이 안 나..."
    
    def test_update_history(self):
        """히스토리 업데이트 테스트"""
        dynamics = DynamicsEngine()
        
        dynamics.update_history(entropy=1.0, core_strength=0.5)
        assert len(dynamics.state.entropy_history) == 1
        assert len(dynamics.state.core_strength_history) == 1
    
    def test_reset(self):
        """상태 초기화 테스트"""
        dynamics = DynamicsEngine()
        
        dynamics.update_history(entropy=1.0, core_strength=0.5)
        dynamics.reset()
        
        assert len(dynamics.state.entropy_history) == 0
        assert len(dynamics.state.core_strength_history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

