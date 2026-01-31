# Cognitive Kernel - Theoretical Architecture

> **Version**: 1.0.0  
> **Date**: 2025-01-29  
> **Author**: GNJz (Qquarts)

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Theoretical Foundations](#theoretical-foundations)
3. [Module Specifications](#module-specifications)
4. [Mathematical Formulations](#mathematical-formulations)
5. [Inter-Module Communication](#inter-module-communication)
6. [References](#references)

---

## Overview

Cognitive Kernel is a **computational neuroscience-inspired** cognitive architecture that models key brain systems as interacting software modules.

### Design Principles

1. **Biological Plausibility**: Each module corresponds to a real brain region
2. **Mathematical Rigor**: All dynamics are governed by established equations
3. **Modularity**: Independent, testable components with clear interfaces
4. **Emergent Behavior**: Complex cognition emerges from simple module interactions

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COGNITIVE KERNEL                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐             │
│  │  THALAMUS   │───▶│  AMYGDALA   │───▶│  HYPOTHALAMUS   │             │
│  │  (Gating)   │    │  (Emotion)  │    │  (Homeostasis)  │             │
│  └──────┬──────┘    └──────┬──────┘    └────────┬────────┘             │
│         │                  │                    │                       │
│         │    ┌─────────────┴─────────────┐      │                       │
│         │    │                           │      │                       │
│         ▼    ▼                           ▼      ▼                       │
│  ┌─────────────────┐              ┌─────────────────┐                   │
│  │    PANORAMA     │◀────────────▶│   MEMORYRANK    │                   │
│  │ (Episodic Mem.) │              │   (Importance)  │                   │
│  └────────┬────────┘              └────────┬────────┘                   │
│           │                                │                            │
│           └────────────┬───────────────────┘                            │
│                        ▼                                                │
│               ┌─────────────────┐                                       │
│               │       PFC       │                                       │
│               │  (Decision)     │                                       │
│               └────────┬────────┘                                       │
│                        │                                                │
│                        ▼                                                │
│               ┌─────────────────┐                                       │
│               │  BASALGANGLIA   │                                       │
│               │    (Action)     │                                       │
│               └─────────────────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Theoretical Foundations

### 1. Thalamus - Sensory Gating

**Biological Basis**:
- Thalamus acts as the "relay station" for sensory information
- Filters and routes signals to appropriate cortical areas
- Modulated by attention and arousal states

**Key Concepts**:
- **Sensory Gating**: Selective filtering of incoming stimuli
- **Reticular Nucleus (TRN)**: Inhibitory control over thalamic relay
- **Attention Modulation**: Top-down control from PFC

**References**:
- Sherman, S. M., & Guillery, R. W. (2006). *Exploring the Thalamus and Its Role in Cortical Function*
- Crick, F. (1984). Function of the thalamic reticular complex: The searchlight hypothesis

---

### 2. Amygdala - Fear Learning & Emotion

**Biological Basis**:
- Central role in fear conditioning and emotional memory
- Receives inputs from sensory cortices and thalamus
- Projects to hypothalamus (stress response) and PFC (regulation)

**Key Concepts**:
- **Fear Conditioning**: Association between neutral stimulus (CS) and aversive outcome (US)
- **Fear Extinction**: Gradual reduction of fear response through repeated non-reinforced exposure
- **Valence-Arousal Model**: Two-dimensional emotional space

**Core Model: Rescorla-Wagner (1972)**

The Rescorla-Wagner model describes associative learning:

```
ΔV = α × β × (λ - V)
```

Where:
- `V`: Associative strength (current fear level)
- `ΔV`: Change in associative strength
- `α`: CS salience (0-1, how noticeable the stimulus is)
- `β`: US learning rate (0-1, how quickly learning occurs)
- `λ`: Maximum associative strength (asymptote)

**Fear Acquisition**:
```python
def fear_acquisition(V, alpha, beta, lambda_max):
    """
    Rescorla-Wagner fear learning update.
    """
    delta_V = alpha * beta * (lambda_max - V)
    return V + delta_V
```

**Fear Extinction**:
```python
def fear_extinction(V, extinction_rate, context_safety):
    """
    Fear extinction during safety/sleep.
    """
    delta_V = -extinction_rate * V * context_safety
    return max(0, V + delta_V)
```

**References**:
- Rescorla, R. A., & Wagner, A. R. (1972). A theory of Pavlovian conditioning
- LeDoux, J. E. (2000). Emotion circuits in the brain. *Annual Review of Neuroscience*
- Phelps, E. A., & LeDoux, J. E. (2005). Contributions of the amygdala to emotion processing

---

### 3. Hypothalamus - Homeostasis & Stress Response

**Biological Basis**:
- Controls autonomic nervous system
- Regulates HPA (Hypothalamic-Pituitary-Adrenal) axis
- Manages energy, temperature, sleep-wake cycles

**Key Concepts**:
- **Homeostasis**: Maintaining internal equilibrium
- **Allostasis**: Adaptive changes in setpoints under stress
- **HPA Axis**: Cortisol release in response to stressors

**Core Model: HPA Axis Dynamics**

Cortisol dynamics under stress:

```
dC/dt = -k₁ × C + k₂ × S × (1 - C/C_max)
```

Where:
- `C`: Cortisol level (0-1)
- `S`: Stress input (0-1)
- `k₁`: Decay rate (natural cortisol clearance)
- `k₂`: Production rate (stress-induced release)
- `C_max`: Maximum cortisol capacity

**Energy Dynamics**:
```
dE/dt = E_input - E_consumption × activity - E_stress × stress_level
```

**Implementation**:
```python
def update_homeostasis(energy, stress, dt, config):
    """
    Hypothalamus homeostasis update.
    """
    # Energy decay
    energy_decay = config.energy_decay * dt
    # Stress-induced drain
    stress_drain = stress * config.stress_energy_cost * dt
    # Recovery
    recovery = config.recovery_rate * (1 - energy) * dt
    
    new_energy = energy - energy_decay - stress_drain + recovery
    return np.clip(new_energy, 0, 1)
```

**References**:
- McEwen, B. S. (1998). Stress, adaptation, and disease: Allostasis and allostatic load
- Sapolsky, R. M. (2004). *Why Zebras Don't Get Ulcers*
- Ulrich-Lai, Y. M., & Herman, J. P. (2009). Neural regulation of endocrine and autonomic stress responses

---

### 4. Panorama - Episodic Memory

**Biological Basis**:
- Hippocampus encodes episodic memories (what, where, when)
- Temporal organization of experiences
- Memory consolidation during sleep

**Key Concepts**:
- **Episodic Memory**: Personal experiences with temporal context
- **Memory Consolidation**: Transfer from hippocampus to neocortex
- **Temporal Binding**: Linking events in time

**Core Model: Temporal Context Model (Howard & Kahana, 2002)**

Memory retrieval probability based on temporal context:

```
P(recall) = f(similarity(context_now, context_encoding))
```

**Forgetting Curve (Ebbinghaus)**:
```
R(t) = e^(-t/S)
```

Where:
- `R(t)`: Retention at time t
- `S`: Memory strength (stability)
- `t`: Time since encoding

**Implementation**:
```python
def get_memory_strength(encoding_time, current_time, half_life):
    """
    Exponential decay memory model.
    """
    dt = current_time - encoding_time
    lambda_decay = np.log(2) / half_life
    return np.exp(-lambda_decay * dt)
```

**References**:
- Tulving, E. (1972). Episodic and semantic memory
- Eichenbaum, H. (2017). Memory: Organization and Control. *Annual Review of Psychology*
- Howard, M. W., & Kahana, M. J. (2002). A distributed representation of temporal context

---

### 5. MemoryRank - Memory Importance

**Theoretical Basis**:
- Inspired by Google PageRank algorithm
- Memory importance = connectivity + recency + emotion + frequency

**Core Model: Personalized PageRank**

```
r^(t+1) = α × M × r^(t) + (1 - α) × v
```

Where:
- `r`: Rank vector (memory importance scores)
- `M`: Transition matrix (memory associations)
- `α`: Damping factor (0.85 typical)
- `v`: Personalization vector (bias towards recent/emotional memories)

**Personalization Vector**:
```
v_i = w_r × recency_i + w_e × emotion_i + w_f × frequency_i
v = normalize(v)
```

**References**:
- Brin, S., & Page, L. (1998). The anatomy of a large-scale hypertextual Web search engine
- Anderson, J. R. (1990). The Adaptive Character of Thought

---

### 6. PFC - Executive Function & Decision Making

**Biological Basis**:
- Prefrontal cortex is the "executive" of the brain
- Working memory maintenance
- Goal-directed behavior and inhibition

**Key Concepts**:
- **Working Memory**: Limited capacity buffer (Miller's Law: 7±2)
- **Executive Control**: Goal maintenance, task switching
- **Inhibition**: Suppression of inappropriate responses (Go/No-Go)

**Core Model: Expected Utility Theory**

Action utility calculation:

```
U(a) = E[reward] - cost(effort) - risk × risk_aversion
```

**Softmax Action Selection**:
```
P(a_i) = exp(β × U_i) / Σ_j exp(β × U_j)
```

Where:
- `β`: Inverse temperature (decision determinism)
- Higher β → more deterministic choice

**Working Memory Capacity (Miller, 1956)**:
```
Capacity = 7 ± 2 items
```

**Implementation**:
```python
def select_action(utilities, temperature):
    """
    Softmax action selection.
    """
    exp_u = np.exp(utilities / temperature)
    probabilities = exp_u / np.sum(exp_u)
    return np.random.choice(len(utilities), p=probabilities)

def evaluate_action(reward, cost, risk, risk_aversion):
    """
    Expected utility calculation.
    """
    return reward - cost - risk * risk_aversion
```

**References**:
- Miller, G. A. (1956). The magical number seven, plus or minus two
- Baddeley, A. D. (2003). Working memory: Looking back and looking forward. *Nature Reviews Neuroscience*
- Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk

---

### 7. Basal Ganglia - Action Selection & Habit Learning

**Biological Basis**:
- Basal ganglia: striatum, globus pallidus, substantia nigra
- Direct pathway (Go) vs Indirect pathway (No-Go)
- Dopamine modulates learning and motivation

**Key Concepts**:
- **Reinforcement Learning**: Learning from reward/punishment
- **Habit Formation**: Transition from goal-directed to automatic behavior
- **Dopamine Signal**: Reward prediction error

**Core Model: Temporal Difference Learning (Sutton & Barto)**

**TD Error (Dopamine Signal)**:
```
δ = r + γ × V(s') - V(s)
```

Where:
- `δ`: TD error (prediction error)
- `r`: Immediate reward
- `γ`: Discount factor (future reward importance)
- `V(s)`: Value of current state
- `V(s')`: Value of next state

**Q-Learning Update**:
```
Q(s,a) ← Q(s,a) + α × [r + γ × max_a' Q(s',a') - Q(s,a)]
```

Where:
- `Q(s,a)`: Action-value for state s, action a
- `α`: Learning rate

**Dopamine Modulation**:
```
α_effective = α × (1 + dopamine_boost × δ)
```

**Habit Formation**:
```
H = H + β × (success - H)
```

When `H > threshold`, action becomes habitual (automatic).

**Implementation**:
```python
def td_error(reward, gamma, V_next, V_current):
    """
    Temporal difference error (dopamine signal).
    """
    return reward + gamma * V_next - V_current

def q_learning_update(Q, state, action, reward, next_state, alpha, gamma):
    """
    Q-learning update rule.
    """
    max_Q_next = max(Q[next_state].values()) if Q[next_state] else 0
    td = reward + gamma * max_Q_next - Q[state][action]
    Q[state][action] += alpha * td
    return Q
```

**References**:
- Schultz, W. (1998). Predictive reward signal of dopamine neurons. *Journal of Neurophysiology*
- Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction*
- Gurney, K., Prescott, T. J., & Redgrave, P. (2001). A computational model of action selection in the basal ganglia

---

## Mathematical Formulations Summary

| Module | Core Equation | Parameters |
|--------|---------------|------------|
| **Amygdala** | ΔV = α × β × (λ - V) | α: CS salience, β: learning rate, λ: max strength |
| **Hypothalamus** | dC/dt = -k₁C + k₂S(1 - C/C_max) | k₁: decay, k₂: production, S: stress |
| **Panorama** | R(t) = e^(-t/S) | t: time, S: memory strength |
| **MemoryRank** | r = αMr + (1-α)v | α: damping, M: transition, v: personalization |
| **PFC** | P(a) = exp(βU)/Σexp(βU) | β: temperature, U: utility |
| **BasalGanglia** | Q ← Q + α[r + γmax(Q') - Q] | α: learning rate, γ: discount |

---

## Inter-Module Communication

### Signal Flow

```
Input Signal → Thalamus
                 │
                 ├──▶ Amygdala (emotional tagging)
                 │        │
                 │        ▼
                 │    Hypothalamus (stress/energy update)
                 │
                 ▼
             Panorama (event recording)
                 │
                 ▼
            MemoryRank (importance calculation)
                 │
                 ▼
               PFC (decision making)
                 │
                 ▼
           BasalGanglia (action execution)
                 │
                 ▼
              Output
```

### Data Contracts

**Thalamus → Amygdala**:
```python
@dataclass
class FilteredSignal:
    content: str
    intensity: float  # 0-1
    modality: str
    salience: float   # 0-1
```

**Amygdala → Hypothalamus**:
```python
@dataclass
class EmotionalState:
    threat_level: float  # 0-1
    arousal: float       # 0-1
    valence: float       # -1 to +1
```

**Hypothalamus → PFC**:
```python
@dataclass
class InternalState:
    energy: float   # 0-1
    stress: float   # 0-1
```

**MemoryRank → PFC**:
```python
top_memories: List[Tuple[str, float]]  # (memory_id, importance)
```

**PFC → BasalGanglia**:
```python
@dataclass
class ActionCommand:
    action_id: str
    confidence: float
    inhibit: bool
```

---

## References

### Foundational Papers

1. **Rescorla-Wagner Model**  
   Rescorla, R. A., & Wagner, A. R. (1972). A theory of Pavlovian conditioning: Variations in the effectiveness of reinforcement and nonreinforcement. In *Classical Conditioning II: Current Research and Theory*.

2. **Temporal Difference Learning**  
   Sutton, R. S. (1988). Learning to predict by the methods of temporal differences. *Machine Learning*, 3(1), 9-44.

3. **Dopamine as Reward Prediction Error**  
   Schultz, W., Dayan, P., & Montague, P. R. (1997). A neural substrate of prediction and reward. *Science*, 275(5306), 1593-1599.

4. **Working Memory**  
   Baddeley, A. D., & Hitch, G. (1974). Working memory. In *Psychology of Learning and Motivation* (Vol. 8, pp. 47-89).

5. **PageRank**  
   Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). The PageRank citation ranking: Bringing order to the web. *Stanford InfoLab*.

6. **Basal Ganglia Action Selection**  
   Gurney, K., Prescott, T. J., & Redgrave, P. (2001). A computational model of action selection in the basal ganglia. *Biological Cybernetics*, 84(6), 401-423.

7. **HPA Axis**  
   McEwen, B. S. (1998). Stress, adaptation, and disease: Allostasis and allostatic load. *Annals of the New York Academy of Sciences*, 840(1), 33-44.

### Textbooks

- Kandel, E. R., et al. (2021). *Principles of Neural Science* (6th ed.). McGraw-Hill.
- Dayan, P., & Abbott, L. F. (2001). *Theoretical Neuroscience*. MIT Press.
- Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-29 | Initial architecture document |

---

**Author**: GNJz (Qquarts)  
**License**: MIT  
**PHAM Blockchain**: Signed

