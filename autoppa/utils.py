import re

def extract_module_name(code):
    """Parse Verilog module code to get the module name"""
    module_re = re.compile(r"^\s*module\s+(\S+)")

    try: 
        result = re.search(module_re, code).group(1)
    except:
        raise Exception("Module name could not be extracted from code")
    
    return result.strip()
