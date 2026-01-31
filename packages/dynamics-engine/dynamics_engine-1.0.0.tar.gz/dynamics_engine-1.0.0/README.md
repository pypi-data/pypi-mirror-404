# Dynamics Engine

> **Decision Stability & Cognitive State Engine**  
> **의사결정 안정화 및 인지 상태 엔진**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/dynamics-engine)](https://pypi.org/project/dynamics-engine/)

**Dynamics Engine**은 AI 시스템의 핵심 문제를 해결합니다: **불확실성 하에서의 불안정한 의사결정**.

대부분의 AI 시스템은 확률을 계산할 수 있지만, 다음을 설명할 수 없습니다:
- ❌ 왜 의사결정이 불안정해지는가
- ❌ 왜 시스템이 진동하거나 멈추는가
- ❌ 왜 기억이 존재하지만 사용할 수 없는가

**Dynamics Engine**은 인지의 **물리학**을 모델링합니다: 엔트로피, 수렴력, 회전 안정화.

> **🇰🇷 한국어** (기본) | [🇺🇸 English Version](#english-version)

---

## 🎯 이 엔진은 누구를 위한 것인가?

**Dynamics Engine**은 다음을 위해 설계되었습니다:

### 1. 불안정한 의사결정을 가진 AI 시스템
- 일관되지 않은 응답을 하는 챗봇
- 진동하는 추천 시스템
- 불확실성 하에서 멈추는 자율 에이전트

### 2. 인지 시뮬레이션 & 디지털 트윈 연구
- 정신 상태 모델링 (집중, 과부하, 혼란)
- 인지 장애 연구 (ADHD, ASD, PTSD)
- 인간-AI 상호작용 연구

### 3. 헬스케어 & 의료 시뮬레이션
- **치매 / 알츠하이머 진행 시뮬레이션**
- 인지 저하 모델링
- 기억 상실 동역학 연구

### 4. 안정성이 필요한 의사결정 시스템
- 시장 불확실성 하에서 안정성이 필요한 거래 알고리즘
- 부드러운 상태 전환이 필요한 제어 시스템
- 일관된 행동이 필요한 게임 AI

---

## 🔥 이 엔진이 해결하는 문제는 무엇인가?

### 문제: 의사결정 불안정성

**기존 AI 시스템:**
```
입력 → 확률 계산 → 의사결정
         (정적, 피드백 없음)
```

**문제점:**
- 불확실성 하에서 의사결정이 불안정해짐
- 시스템이 선택 사이를 진동함
- 기억이 존재하지만 의사결정을 안정화하지 못함
- 의사결정이 변하는 이유를 설명할 수 없음

### 해결책: 인지 동역학

**Dynamics Engine:**
```
입력 → 엔트로피 계산 → 회전 토크 → 안정화된 의사결정
         (동적 피드백 루프)
```

**해결책:**
- ✅ **엔트로피 기반 탐색**: 불확실할 때 자동으로 탐색
- ✅ **코어 강도 수렴**: 메모리 중력이 의사결정을 안정화
- ✅ **회전 동역학**: 부드러운 상태 전환
- ✅ **인지적 절규 감지**: 시스템이 "혼란스러운" 상태를 식별

---

## 💡 실제 사용 사례

### 사용 사례 1: 챗봇 의사결정 안정성

**문제**: 챗봇이 같은 질문에 다른 응답을 함.

**해결책**:
```python
from dynamics_engine import DynamicsEngine

dynamics = DynamicsEngine()

# 엔트로피 계산 (불확실성)
entropy = dynamics.calculate_entropy(response_probabilities)

# 엔트로피가 높으면 시스템이 불확실함
if entropy > threshold:
    # 탐색을 위한 회전 토크 생성
    torque = dynamics.generate_torque(responses, entropy)
    # 토크를 사용하여 의사결정 안정화
    stabilized_response = apply_torque(responses, torque)
```

**결과**: 불확실성 하에서도 일관되고 안정적인 응답.

### 사용 사례 2: 치매/알츠하이머 시뮬레이션

**문제**: 연구를 위한 인지 저하 시뮬레이션 필요.

**해결책**:
```python
from dynamics_engine import DynamicsEngine, DynamicsConfig
import time

# 치매 설정
config = DynamicsConfig(
    old_memory_decay_rate=0.0001,  # 오래된 기억 감쇠
    new_memory_decay_rate=0.0,     # 새 기억 정상 유지
    core_decay_rate=0.001
)

dynamics = DynamicsEngine(config)

# 기억 노화 시뮬레이션
memories = [
    {"importance": 0.9, "timestamp": time.time() - 7200},  # 2시간 전 (오래된 기억)
    {"importance": 0.9, "timestamp": time.time() - 300},   # 5분 전 (새 기억)
]

core = dynamics.calculate_core_strength(memories)
# 오래된 기억 감쇠, 새 기억 유지 → 치매 패턴
```

**결과**: 인지 저하 패턴의 정확한 시뮬레이션.

### 사용 사례 3: 거래 알고리즘 안정성

**문제**: 거래 알고리즘이 매수/매도 결정 사이를 진동함.

**해결책**:
```python
# 시장 신호의 엔트로피 계산
entropy = dynamics.calculate_entropy(signal_probabilities)

# 코어 강도 확인 (과거 데이터로부터의 신뢰도)
core = dynamics.calculate_core_strength(historical_memories)

# 엔트로피 높고 코어 낮으면 → 불안정, 대기
if entropy > threshold and core < threshold:
    decision = "WAIT"  # 불안정할 때 거래하지 않음
else:
    # 안정화된 의사결정 생성
    torque = dynamics.generate_torque(["BUY", "SELL", "HOLD"], entropy)
    decision = apply_torque(torque)
```

**결과**: 변동성이 큰 시장에서도 안정적인 거래 결정.

---

## 🚀 빠른 시작

```python
from dynamics_engine import DynamicsEngine, DynamicsConfig
import time

# 엔진 생성
dynamics = DynamicsEngine()

# 1. 엔트로피 계산 (선택 불확실성)
entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
print(f"엔트로피: {entropy:.3f}")  # 1.089 (높은 불확실성)

# 2. 코어 강도 계산 (메모리 중력)
memories = [
    {"importance": 0.9, "timestamp": time.time() - 3600},  # 1시간 전
    {"importance": 0.8, "timestamp": time.time() - 300},   # 5분 전
]
core = dynamics.calculate_core_strength(memories)
print(f"코어 강도: {core:.3f}")  # 0.425 (중간 강도)

# 3. 회전 토크 생성 (자동 탐색)
options = ["rest", "work", "exercise"]
torque = dynamics.generate_torque(options, entropy, mode="adhd")
print(f"토크: {torque}")
# {'rest': 0.446, 'work': -0.223, 'exercise': -0.223}
# 양수 토크 = 권장, 음수 토크 = 비권장

# 4. 인지적 절규 확인 (기억 상실 감지)
is_distress, message = dynamics.check_cognitive_distress(entropy, core, len(options))
if is_distress:
    print(f"⚠️ {message}")  # "기억이 안 나..."
```

---

## 📊 핵심 기능

### 1. 엔트로피 계산
정보 이론을 사용하여 선택 불확실성 측정:
- **높은 엔트로피** = 불확실한 선택 (탐색 필요)
- **낮은 엔트로피** = 확정적인 선택 (착취)

### 2. 코어 강도 계산
메모리 중력 (수렴력) 계산:
- **높은 코어** = 강한 기억, 의사결정을 안정화할 수 있음
- **낮은 코어** = 약한 기억, 의사결정이 불안정해짐

### 3. 회전 토크 생성
엔트로피를 기반으로 자동 회전 생성:
- **양수 토크** = 선택을 권장
- **음수 토크** = 선택을 비권장
- 부드러운 상태 전환 생성

### 4. 인지적 절규 감지
"기억 상실" 또는 "혼란" 상태 감지:
- 높은 엔트로피 + 낮은 코어 강도 = 인지적 절규
- 모니터링을 위한 절규 메시지 반환

### 5. 코어 붕괴 동역학
치매와 알츠하이머 모델링:
- **치매**: 점진적 코어 감쇠 (오래된 기억부터 소실)
- **알츠하이머**: 급격한 코어 붕괴 (새 기억 저장 실패)

### 6. 시간축 분리
오래된 기억과 새 기억에 다른 감쇠율:
- 인지 저하 패턴의 정확한 시뮬레이션 가능

---

## 🔬 작동 원리 (기술적)

### 수학적 기반

**엔트로피 (정보 이론)**:
```
E = -Σ P(k) ln P(k)
```
- 선택 불확실성 측정 (0 ~ ln(N))

**코어 강도 (메모리 중력)**:
```
C(t) = C(0) * exp(-λ * Δt)
```
- 의사결정을 안정화하는 메모리 중력

**회전 토크 (세차운동)**:
```
T(k) = γ * E_norm * cos(φ - ψ_k)
```
- 엔트로피 기반 자동 회전

**시간축 분리**:
```
오래된 기억: importance *= exp(-λ_old * age)
새 기억: importance *= exp(-λ_new * age)
```
- 치매/알츠하이머 모델링을 위한 다른 감쇠율

### 아키텍처

```
Dynamics Engine
├── DynamicsConfig      (설정)
├── DynamicsState       (상태 관리)
└── DynamicsEngine      (핵심 엔진)
    ├── calculate_entropy()          # 불확실성 측정
    ├── calculate_core_strength()    # 메모리 중력
    ├── generate_torque()             # 자동 탐색
    ├── check_cognitive_distress()    # 혼란 감지
    └── update_history()             # 시간 변화 추적
```

---

## 📦 설치

```bash
pip install dynamics-engine
```

---

## 🧪 예시

### 예시 1: 의사결정 안정화

```python
from dynamics_engine import DynamicsEngine

dynamics = DynamicsEngine()

# 불안정한 의사결정 확률
probabilities = [0.33, 0.33, 0.34]  # 매우 불확실

# 엔트로피 계산
entropy = dynamics.calculate_entropy(probabilities)
print(f"엔트로피: {entropy:.3f}")  # 높은 엔트로피

# 안정화를 위한 토크 생성
options = ["option_A", "option_B", "option_C"]
torque = dynamics.generate_torque(options, entropy)

# 토크를 적용하여 의사결정 안정화
stabilized_decision = max(torque.items(), key=lambda x: x[1])[0]
print(f"안정화된 결정: {stabilized_decision}")
```

### 예시 2: 치매 시뮬레이션

```python
from dynamics_engine import DynamicsEngine, DynamicsConfig
import time

# 치매 설정
config = DynamicsConfig(
    old_memory_decay_rate=0.0001,  # 오래된 기억 감쇠
    new_memory_decay_rate=0.0,      # 새 기억 정상 유지
    core_decay_rate=0.001,
    memory_age_threshold=3600.0     # 1시간 임계값
)

dynamics = DynamicsEngine(config)

# 기억 노화 시뮬레이션
memories = [
    {"importance": 0.9, "timestamp": time.time() - 7200},  # 2시간 (오래된 기억)
    {"importance": 0.9, "timestamp": time.time() - 300},   # 5분 (새 기억)
]

# 코어 강도 계산
core = dynamics.calculate_core_strength(memories)
print(f"코어 강도: {core:.3f}")
# 오래된 기억 감쇠, 새 기억 유지 → 치매 패턴
```

### 예시 3: 알츠하이머 시뮬레이션

```python
# 알츠하이머 설정
config = DynamicsConfig(
    old_memory_decay_rate=0.0001,  # 오래된 기억 느리게 감쇠
    new_memory_decay_rate=0.1,      # 새 기억 급격히 감쇠
    core_decay_rate=0.01,
    memory_update_failure=0.8       # 80% 실패율
)

dynamics = DynamicsEngine(config)

# 기억 시뮬레이션
memories = [
    {"importance": 0.9, "timestamp": time.time() - 7200},  # 오래된 기억
    {"importance": 0.9, "timestamp": time.time() - 300},   # 새 기억
]

core = dynamics.calculate_core_strength(memories)
# 새 기억 급격히 감쇠 → 알츠하이머 패턴
```

---

## 🔗 Cognitive Kernel과의 관계

**Dynamics Engine**은 [Cognitive Kernel](https://github.com/qquartsco-svg/Cognitive_Kernel)의 **핵심 동역학 모듈**이지만, **독립적으로** 사용할 수 있습니다:

- ✅ **의존성 없음** (표준 라이브러리만 사용)
- ✅ **독립 배포** (Edge AI 호환)
- ✅ **경량** (~50KB)
- ✅ **빠름** (마이크로초 수준 계산)

---

## 📚 문서

- [API Reference](docs/API_REFERENCE.md) - 완전한 API 문서
- [수학적 기반](README.md#수학적-기반) - 상세한 수식
- [Cognitive Kernel 문서](https://github.com/qquartsco-svg/Cognitive_Kernel) - 통합 가이드

---

## 🏗️ 산업별 사용 사례

### 헬스케어 & 의료 연구
- 치매/알츠하이머 진행 시뮬레이션
- 인지 저하 모델링
- 기억 상실 동역학 연구

### AI & 머신러닝
- 챗봇의 의사결정 안정성
- 추천 시스템 안정화
- 자율 에이전트 행동 제어

### 금융 & 거래
- 거래 알고리즘 안정성
- 불확실성 하에서의 위험 평가
- 시장 신호 안정화

### 게임 & 시뮬레이션
- NPC 행동 일관성
- 게임 AI 의사결정 안정성
- 인지 상태 시뮬레이션

---

## 📄 라이선스

MIT License

---

## 👤 작성자

**GNJz (Qquarts)**

---

---

# English Version

> **🇰🇷 [한국어 버전](#-이-엔진은-누구를-위한-것인가) (기본)** | **🇺🇸 English**

## 🎯 Who is this for?

**Dynamics Engine** is designed for:

### 1. AI Systems with Unstable Decision-Making
- Chatbots that give inconsistent responses
- Recommendation systems that oscillate
- Autonomous agents that freeze under uncertainty

### 2. Cognitive Simulation & Digital Twin Research
- Mental state modeling (focus, overload, confusion)
- Cognitive disorder research (ADHD, ASD, PTSD)
- Human-AI interaction studies

### 3. Healthcare & Medical Simulation
- **Dementia / Alzheimer progression simulation**
- Cognitive decline modeling
- Memory loss dynamics research

### 4. Decision Systems Requiring Stability
- Trading algorithms needing stability under market uncertainty
- Control systems requiring smooth state transitions
- Game AI needing consistent behavior

## 🔥 What problem does this solve?

### The Problem: Decision Instability

**Traditional AI systems:**
```
Input → Probability Calculation → Decision
         (Static, no feedback)
```

**Problem:**
- Decisions become unstable under uncertainty
- Systems oscillate between choices
- Memory exists but doesn't stabilize decisions
- No explanation for why decisions change

### The Solution: Cognitive Dynamics

**Dynamics Engine:**
```
Input → Entropy Calculation → Rotational Torque → Stabilized Decision
         (Dynamic feedback loop)
```

**Solution:**
- ✅ **Entropy-based exploration**: Automatically explores when uncertain
- ✅ **Core strength convergence**: Memory gravity stabilizes decisions
- ✅ **Rotational dynamics**: Smooth state transitions
- ✅ **Cognitive distress detection**: Identifies when system is "confused"

## 🚀 Quick Start

```python
from dynamics_engine import DynamicsEngine, DynamicsConfig
import time

# Create engine
dynamics = DynamicsEngine()

# Calculate entropy (choice uncertainty)
entropy = dynamics.calculate_entropy([0.3, 0.4, 0.3])
print(f"Entropy: {entropy:.3f}")  # 1.089 (high uncertainty)

# Calculate core strength (memory gravity)
memories = [
    {"importance": 0.9, "timestamp": time.time() - 3600},  # 1 hour ago
    {"importance": 0.8, "timestamp": time.time() - 300},   # 5 minutes ago
]
core = dynamics.calculate_core_strength(memories)
print(f"Core Strength: {core:.3f}")  # 0.425 (moderate strength)

# Generate rotational torque (automatic exploration)
options = ["rest", "work", "exercise"]
torque = dynamics.generate_torque(options, entropy, mode="adhd")
print(f"Torque: {torque}")
# {'rest': 0.446, 'work': -0.223, 'exercise': -0.223}
# Positive torque = encourages, Negative = discourages

# Check cognitive distress (memory loss detection)
is_distress, message = dynamics.check_cognitive_distress(entropy, core, len(options))
if is_distress:
    print(f"⚠️ {message}")  # "기억이 안 나..."
```

## 📊 Core Features

### 1. Entropy Calculation
Measures choice uncertainty using information theory:
- **High entropy** = uncertain choices (exploration needed)
- **Low entropy** = certain choices (exploitation)

### 2. Core Strength Calculation
Calculates memory gravity (convergence force):
- **High core** = strong memory, can stabilize decisions
- **Low core** = weak memory, decisions become unstable

### 3. Rotational Torque Generation
Generates automatic rotation based on entropy:
- **Positive torque** = encourages selection
- **Negative torque** = discourages selection
- Creates smooth state transitions

### 4. Cognitive Distress Detection
Detects "memory loss" or "confusion" state:
- High entropy + Low core strength = Cognitive distress
- Returns distress message for monitoring

### 5. Core Decay Dynamics
Models dementia and Alzheimer's:
- **Dementia**: Gradual core decay (old memories fade first)
- **Alzheimer's**: Rapid core collapse (new memories fail to store)

### 6. Time-axis Separation
Different decay rates for old vs new memories:
- Enables accurate simulation of cognitive decline patterns

## 🔬 How It Works (Technical)

### Mathematical Foundation

**Entropy (Information Theory)**:
```
E = -Σ P(k) ln P(k)
```
- Measures choice uncertainty (0 ~ ln(N))

**Core Strength (Memory Gravity)**:
```
C(t) = C(0) * exp(-λ * Δt)
```
- Memory gravity that stabilizes decisions

**Rotational Torque (Precession)**:
```
T(k) = γ * E_norm * cos(φ - ψ_k)
```
- Automatic rotation based on entropy

**Time-axis Separation**:
```
Old memory: importance *= exp(-λ_old * age)
New memory: importance *= exp(-λ_new * age)
```
- Different decay rates for dementia/Alzheimer's modeling

## 📦 Installation

```bash
pip install dynamics-engine
```

## 📚 Documentation

- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Mathematical Foundation](README.md#mathematical-foundation) - Detailed formulas
- [Cognitive Kernel Docs](https://github.com/qquartsco-svg/Cognitive_Kernel) - Integration guide

## 📄 License

MIT License

## 👤 Author

**GNJz (Qquarts)**

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-31
