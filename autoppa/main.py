import argparse
import sys
from .sim import sim
import os 

def main():
    parser = argparse.ArgumentParser(
        description="PPAgent for RTL code optimization",
        formatter_class=argparse.RawTextHelpFormatter
    )

    steps = ["sim", "synth"]
    parser.add_argument("step",
                        type=str,
                        default=None,
                        choices=steps,
                        metavar="STEP",
                        help=(f"Step to run. Choices: {steps}"))
    
    tasks = range(1, 2)
    parser.add_argument("task",
                        type=int,
                        default=None,
                        choices=tasks,
                        metavar="TASK",
                        help=f"Benchmark task to run. Choices: {list(tasks)}")


    parser.add_argument("file",
                        type=str,
                        default=None,
                        metavar="FILE",
                        help="Path to Verilog source code file for optimization")
    
    
    # if no arguments specified, then print help 
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    
    if not os.path.isfile(args.file):
        raise Exception("Not a valid source code file")
    
    
    if args.step == "sim":
        with open(args.file, "r") as f:
            code = f.read()
        
        result = sim(code, task=args.task)
        print(result)
        
    elif args.step == "synth":
        pass
        


if __name__ == "__main__":
    main()
    
