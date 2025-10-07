import subprocess
import os
from .utils import extract_module_name
import re

def extract_perf(string):
    """Parse the Icarus Verilog sim output to get time (performance) metric"""
    time_re = re.compile(r"TIME:\s*(\d+)")
    
    try: 
        time = re.search(time_re, string).group(1)
    except:
        raise Exception("Time could not be extracted from sim result")
    
    return time

def extract_failed_sim(string):
    """Parse Icarus Verilog sim output to see if simulation passed or failed"""
    
    failure = re.search("FAILED", string)
    success = re.search("PASSED", string)
    
    if failure:
        return True
    
    if success:
        return False
        
    raise Exception("Sim result could not be extracted from output")
    
    
def sim(code: str, *, task:int=1, debug:bool=False) -> str:
    """Runs Icarus Verilog simulation on input code string
    
    Args:
        code: A string representing the Verilog code to simulate
        
    Kwargs:
        task: Which benchmark optimization task to run
        debug: Output additional information from Icarus Verilog
        
    Returns a string indicating either success with
    performance estimation (time in nanoseconds),
    or failure with an error message
    """    
    dut_name = extract_module_name(code)
    
    # otherwise we will keep creating build directories
    ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    os.chdir(ROOT_DIR)
    os.makedirs("build", exist_ok=True)
    os.chdir("build")
    
    with open(f"{dut_name}.v", "w") as f:
        f.write(code)
    
    try:
        command = ["iverilog", "-o", dut_name,
                                 f"-DDUT_NAME={dut_name}", f"{dut_name}.v",
                                 f"../benchmark/task{task}.v"]
        if debug:
            print(" ".join(command))
        
        # no output if compilation passes successfully
        subprocess.run(command,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       check=True, encoding="utf-8")
        
    except subprocess.CalledProcessError as e:
        return f"Icarus Verilog gave an error during compilation. Please investigate and fix:\n{e.stdout}"
    
    else:
        try:
            command = ["vvp", dut_name]
            
            if debug:
                print(" ".join(command))
            
            sim_result = subprocess.run(command,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    check=True, encoding="utf-8")
            
            if debug:
                print(sim_result.stdout)
            
            # because we can only output error with $fatal, but that outputs
            # additional information from verilog testbench which is superfluous
            sim_fail = extract_failed_sim(sim_result.stdout)
            if sim_fail: 
                raise subprocess.CalledProcessError(1, command, sim_result.stdout)
            
            perf = extract_perf(sim_result.stdout)
            
            return (f"The simulation passed successfully\n"
                    f"Execution time (ns) == {perf}")
            
        except subprocess.CalledProcessError as e:
            return f"Icarus Verilog simulator gave an error during simulation. Please investigate and fix:\n{e.stdout}"
    
            