
import re
import subprocess
import os
from .utils import extract_module_name


def extract_area(string):
    """Parse the Yosys synthesis output log to get number of cells (area) metric"""
    
    area_re = re.compile(r"Number of cells:\s+(\d+)")
    
    try:
        area = re.search(area_re, string).group(1)
    except:
        raise Exception("Area could not be extracted from synthesis report")

    return area
                
                
def synth(code: str, *, debug:bool=False) -> str:
    """Runs Yosys Verilog synthesis on input code string
    
    Args:
        code: A string representing the Verilog code to synthesize
    
    Kwargs:
        debug: Output additional information from Yosys
    
    Returns a string indicating either success with area estimation (number of cells),
    or failure with an error message
    """ 
    
    dut_name = extract_module_name(code)
    
    os.makedirs("build", exist_ok=True)
    
    with open(f"build/{dut_name}.v", "w") as f:
        f.write(code)

    try:
        command = ["yosys",
                   "-p", f"read_verilog build/{dut_name}.v",
                   "-p", "synth",
                   "-p", f"write_verilog build/{dut_name}.v",
                   "-l", f"build/{dut_name}.log"]
        
        if debug:
            print(" ".join(command))
            
        synthesis_result = subprocess.run(command,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           check=True, encoding="utf-8")
        
        area = extract_area(synthesis_result.stdout)
        
        return (f"The synthesis completed successfully\n"
                f"Area (number of cells) == {area}")
        
    except subprocess.CalledProcessError as e:
        return f"Yosys gave an error during synthesis. Please investigate and fix:\n{e.stdout}"
          