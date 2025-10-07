import subprocess
import os
from .utils import extract_module_name


def extract_power(string):
    """Extract total power (mW) from OpenSTA power report table"""
    lines = string.splitlines()

    for line in lines:
        if line.strip().startswith("Total"):
            parts = line.split()
            total_power = f"{float(parts[4])*1000:.4f}"
            return total_power
        
    raise Exception("Couldn't find total power")

def power(code: str, *, task:int=1, debug:bool=False) -> str:
    """Runs OpenSTA power analysis on input code string (synth must be ran first)
    
    Args:
        task: Which benchmark optimization task to run
        code: A string representing the Verilog code to be analyzed
        
    Kwargs:
        debug: Output additional information from OpenSTA
        
    Returns a string indicating either success with
    power estimation (mW), or failure with an error message
    """    
    
    dut_name = extract_module_name(code)
    
    build_dir = os.path.join("build", f"task{task}")
    
    if not os.path.isfile(f"{build_dir}/{dut_name}.vcd"):
        raise FileNotFoundError(f"Simulation must be ran first before power analysis")
    
    if not os.path.isfile(f"build/synth/synth_{dut_name}.v"):
        raise FileNotFoundError(f"Synthesis must be ran first before power analysis")

    # because we can't specify commands to opensta via command line
    with open("benchmark/power.tcl", "r") as f:
        content = f.read()

    content = content.replace("{MODULE_NAME}", dut_name)
    content = content.replace("{TASK_NUM}", str(task))
    
    with open(f"{build_dir}/{dut_name}.tcl", "w") as f:
        f.write(content)    
    
    try:
        command = ["docker",
                   "run",
                   "--rm",
                   "-v",
                   f"{os.getcwd()}:/autoppa",
                   "opensta",
                   "-no_init",
                   "-no_splash",
                   f"autoppa/{build_dir}/{dut_name}.tcl"]
        
        if debug:
            print(" ".join(command))
            
        power_result = subprocess.run(command,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           check=True, encoding="utf-8")
        
        
        power = extract_power(power_result.stdout)
        
        return (f"The power analysis completed successfully\n"
                f"Power (mW) == {power}")
        
    except subprocess.CalledProcessError as e:
        return f"OpenSTA gave an error during power analysis. Please investigate and fix:\n{e.stdout}"
          