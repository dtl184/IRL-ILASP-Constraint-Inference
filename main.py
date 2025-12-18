import numpy as np
import subprocess
import os
from mdp_helpers import trajectory_to_logic_examples

# MDP constants
PEGS = [1, 2, 3]
STATE_SPACE = [(d1, d2, d3) for d1 in PEGS for d2 in PEGS for d3 in PEGS]
ACTS = [f"move({p1}, {p2})" for p1 in PEGS for p2 in PEGS if p1 != p2]

def calculate_maxent_svf(T, action_names, constraints, horizon=30):
    """
    Computes expected state visitation frequency 
    T shape: (27, 6, 27) -> (States, Actions, Next_States)
    """
    n_s, n_a, _ = T.shape
    pi = np.ones((n_s, n_a))
    
    for s_idx in range(n_s):
        state = STATE_SPACE[s_idx]
        for a_idx in range(n_a):
            action = action_names[a_idx]
            if (state, action) in constraints:
                pi[s_idx, a_idx] = 0.0
        
        if pi[s_idx].sum() > 0:
            pi[s_idx] /= pi[s_idx].sum()

    mu = np.ones(n_s) / n_s 
    svf = np.zeros(n_s)
    for _ in range(horizon):
        svf += mu
        next_mu = np.zeros(n_s)
        for s_idx in range(n_s):
            for a_idx in range(n_a):
                if pi[s_idx, a_idx] > 0:
                    next_mu += mu[s_idx] * pi[s_idx, a_idx] * T[s_idx, a_idx]
        mu = next_mu
        
    return pi * svf[:, np.newaxis]

def run_inference():
    """
    Executes IRL-ILASP loop to discover the hidden task constraints. 
    """
    T_prob = np.load('T_prob.npy') 
    n_states, n_actions = T_prob.shape[0], T_prob.shape[1]
    current_acts = ACTS[:n_actions]
    
    # load in expert trajectories
    with open('expert_trajectories.txt', 'r') as f:
        l_env = {}; exec(f.read(), {}, l_env)
        EXPERT_TRAJECTORIES = l_env.get('EXPERT_TRAJECTORIES', [])

    expert_sa = set((s, a) for traj in EXPERT_TRAJECTORIES for s, a, _ in traj)
    C = [] 


    for i in range(100):
        # 1. Forward Pass (IRL)
        D_sa = calculate_maxent_svf(T_prob, current_acts, set(C), horizon=50)
        
        # 2. Find the move with highest SVF not visited in an expert trajectory
        # this is a candidate constraint
        flat_indices = np.argsort(D_sa, axis=None)[::-1]
        c_star = None
        for idx in flat_indices:
            s_idx, a_idx = np.unravel_index(idx, D_sa.shape)
            candidate = (STATE_SPACE[s_idx], current_acts[a_idx])
            if candidate not in expert_sa and candidate not in C:
                c_star = candidate
                break

        if not c_star: break
        C.append(c_star)

        # 3. Generate negative and positive examples based on the candidate constraint
        E_plus, E_minus = trajectory_to_logic_examples(EXPERT_TRAJECTORIES, [c_star])
        
        with open('input.las', 'w') as f_out:
            if os.path.exists('ilasp_config.lp'):
                f_out.write(open('ilasp_config.lp').read() + "\n")
            f_out.write("\n".join(E_plus) + "\n" + "\n".join(E_minus))

        # 4. Run ILASP to find a rule that can perfectly separate the negative and positive examples 
        res = subprocess.run(['ilasp', '--version=4', '-q', 'input.las'], capture_output=True, text=True)
        
        # If a suitable constraint has been generated, stop.
        output = res.stdout.strip()
        if "violation" in output:
            print(f"\n" + "*"*40)
            print(f"Constraint Discovered")
            print(f"{output}")
            print("*"*40)
            break

if __name__ == "__main__":
    run_inference()