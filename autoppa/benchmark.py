from .sim import sim
from .synth import synth
from .power import power
import json 

def benchmark(task_num=1, baseline="reference", debug=False):
    """Runs the specified benchmark task and associated baseline"""
    
    if task_num not in range(1, 6):
        raise ValueError("Invalid task number", task_num)
    
    if baseline not in {"optimized", "reference"}:
        raise ValueError("Invalid baseline", baseline)
    
    
    with open('benchmark/metadata.json') as f:
        task_info = json.load(f)[task_num-1]

    print("==========================================================================")
    print("Task number:", task_num)
    print("Description:", task_info['description'])
    print("Metric:", task_info['metric'])
    print("Reference performance:", task_info['baseline'], task_info['units'])
    print("==========================================================================")
            
    print(f"\n-------- BASELINE {baseline} --------\n")
            
    with open(f"baseline/{baseline}/task{task_num}.v", "r") as f:
        code = f.read()
                
    print(sim(code, task=task_num, debug=debug))
    print()
    print(synth(code, debug=debug))
    print()
    print(power(code, task=task_num, debug=debug))
    