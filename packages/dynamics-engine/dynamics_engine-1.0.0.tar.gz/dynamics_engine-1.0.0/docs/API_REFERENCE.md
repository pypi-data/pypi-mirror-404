# API Reference

> **Dynamics Engine API 문서**

**Version**: 1.0.0

---

## DynamicsEngine

### `calculate_entropy(probabilities: List[float]) -> float`

엔트로피 계산

**수식:** `E = -Σ P(k) ln P(k)`

**Parameters:**
- `probabilities`: 확률 분포 리스트

**Returns:**
- `entropy`: 엔트로피 값 (0 ~ ln(N))

---

### `calculate_core_strength(memories: List[Dict], ...) -> float`

코어 강도 계산

**수식:**
- `C_raw = α * (Σ importance) / N`
- `C(t) = C(0) * exp(-λ * Δt)`

**Parameters:**
- `memories`: 기억 리스트
- `memory_update_failure`: 새 기억 중요도 반영 실패율 (0~1)
- `alpha`: 기억 영향 계수

**Returns:**
- `core_strength`: 코어 강도 (0~1)

---

### `generate_torque(options: List[str], entropy: float, ...) -> Dict[str, float]`

회전 토크 생성

**수식:**
- `E_norm = E / E_max`
- `T = γ * E_norm`
- `T(k) = T * cos(φ - ψ_k)`

**Parameters:**
- `options`: 옵션 리스트
- `entropy`: 현재 엔트로피
- `mode`: 인지 모드 ("adhd", "asd", "normal")

**Returns:**
- `torque`: 옵션별 회전 토크 딕셔너리

---

### `check_cognitive_distress(entropy: float, core_strength: float, num_options: int) -> Tuple[bool, str]`

인지적 절규 확인

**조건:** `E > E_threshold AND C < C_threshold`

**Parameters:**
- `entropy`: 현재 엔트로피
- `core_strength`: 현재 코어 강도
- `num_options`: 옵션 수

**Returns:**
- `(is_distress, message)`: (절규 여부, 메시지) 튜플

---

## DynamicsConfig

설정 클래스

**주요 파라미터:**
- `base_gamma`: 기본 회전 토크 세기 (0~1)
- `omega`: 세차 속도 (> 0)
- `core_decay_rate`: 코어 감쇠율 (≥ 0)
- `old_memory_decay_rate`: 오래된 기억 감쇠율 (≥ 0)
- `new_memory_decay_rate`: 새 기억 감쇠율 (≥ 0)
- `memory_age_threshold`: 기억 나이 임계값 (> 0)

---

## DynamicsState

상태 클래스

**주요 상태:**
- `entropy`: 현재 엔트로피
- `core_strength`: 현재 코어 강도
- `precession_phi`: 세차 위상 (0 ~ 2π)
- `cognitive_distress`: 인지적 절규 여부

---

**작성자**: GNJz (Qquarts)  
**작성일**: 2026-01-31

