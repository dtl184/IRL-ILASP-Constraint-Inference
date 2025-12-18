# Constraint Discovery in the Tower of Hanoi: A Hybrid IRL-ILP Approach

This project implements a hybrid framework that combines **Inverse Reinforcement Learning (IRL)** and **Inductive Logic Programming (ILP)** to discover physical laws from expert demonstrations.

## 1. Methodology Overview

The environment is defined as a Markov Decision Process (MDP) without a predefined reward function: $\mathcal{M} \setminus R = (S, A, T, \gamma)$. The goal is to induce the symbolic rules of the environment by observing expert behavior.

### 2. Maximum Entropy IRL (Numerical Discovery)
We employ a Maximum Entropy IRL approach to estimate the **State-Action Visitation Frequency** $D_{sa}$. This value represents how often an unconstrained agent would take a specific action to reach a goal efficiently.

$$D_{sa} = \sum_{t=0}^{H} P(s_t = s, a_t = a \mid \pi)$$



The system identifies "informational gaps" where the unconstrained agent's visitation frequency is high, but the expert's is zero. A candidate violation $c^*$ is selected as:

$$c^* = \arg\max_{(s,a) \notin \mathcal{T}_{ex}} D_{sa}(s, a)$$

### 3. Symbolic Induction (Logic Bridge)
Once a candidate $c^*$ is identified, it is featurized into logical atoms. We use **ILASP** to find a hypothesis $H$ that explains why the candidate is a violation while the expert's moves are not:

$$B \cup H \models E^+ \quad \text{and} \quad B \cup H \not\models E^-$$



### 4. Results
Through this iterative process, the framework successfully induces the physical law of the Tower of Hanoi:

**Learned Rule:**
`violation :- moving_disk(V1), disk_below(V2), smaller(V2, V1).`

This rule generalizes across all 162 possible transitions, effectively "pruning" the MDP to match the physical constraints of the real world.
