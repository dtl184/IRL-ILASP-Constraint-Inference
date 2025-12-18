import numpy as np
import re


def convert_state_to_facts(state, action_str):
    """
    Translates a numerical MDP state and action string into symbolic logic predicates.
    Identifies the smallest disk at the source peg (the moving disk) and the 
    smallest disk at the destination peg (the disk that will be below).
    """
    match = re.match(r'move\((\d+), (\d+)\)', action_str)
    if not match: return ["moving_disk(none).", "disk_below(none)."]
    
    from_p, to_p = int(match.group(1)), int(match.group(2))
    p1_disks = [d_idx for d_idx, peg in enumerate(state, 1) if peg == from_p]
    moving_disk = min(p1_disks) if p1_disks else "none"
    
    p2_disks = [d_idx for d_idx, peg in enumerate(state, 1) if peg == to_p]
    target_disk = min(p2_disks) if p2_disks else "none"

    return [f"moving_disk({moving_disk})", f"disk_below({target_disk})"]

def trajectory_to_logic_examples(expert_trajectories, C):
    """
    Generates ILASP-formatted positive and negative learning examples.
    Expert transitions are labeled as negative examples (they do not violate constraints), 
    while IRL-generated candidates C are labeled as positive examples (they do violate constraints).
    """
    E_plus, E_minus = [], []
    bg = "disk(1..3). smaller(1,2). smaller(1,3). smaller(2,3)."
    
    for traj in expert_trajectories:
        for s, a, _ in traj:
            f = convert_state_to_facts(s, a)
            context = f"{' '.join([x + '.' for x in f])} {bg}"
            E_minus.append(f"#neg({{violation}}, {{}}, {{ {context} }}).")

    for s, a in C:
        f = convert_state_to_facts(s, a)
        context = f"{' '.join([x + '.' for x in f])} {bg}"
        E_plus.append(f"#pos({{violation}}, {{}}, {{ {context} }}).")
        
    return E_plus, E_minus


