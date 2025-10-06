import argparse
import sys
from .sim import sim
from .synth import synth

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
    
    tasks = range(1, 6)
    parser.add_argument("task",
                        type=int,
                        default=None,
                        choices=tasks,
                        metavar="TASK",
                        help=f"Benchmark task to run (ignored if STEP != 'sim'). Choices: {list(tasks)}")


    parser.add_argument("file",
                        type=str,
                        default=None,
                        metavar="FILE",
                        help="Path to Verilog source code file for optimization")

    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="Print additional output for debugging purposes")
    

    
    # if no arguments specified, then print help 
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    
    if not os.path.isfile(args.file):
        raise Exception("Not a valid source code file")
    

    # because LLM will call tools with just strings,
    # but if we call these from command lines we have filepaths
    with open(args.file, "r") as f:
        code = f.read()

    if args.step == "sim":
        result = sim(code, task=args.task, debug=args.debug)
        print(result)
        
    elif args.step == "synth":
        result = synth(code, debug=args.debug)
        print(result)
        


if __name__ == "__main__":
    main()
    
