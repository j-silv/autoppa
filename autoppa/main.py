import argparse
import sys
import os 
from .sim import sim
from .synth import synth
from .agent import agent


def main():
    parser = argparse.ArgumentParser(
        description="PPAgent for RTL code optimization",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="Print additional output for debugging purposes")    

    subparsers = parser.add_subparsers(dest="step", metavar="STEP", help="Step to run (run STEP -h for more info)",
                                       required=True)
    
    # because some subparsers use the same arguments
    
    file_arg = dict(
        type=str,
        default=None,
        metavar="FILE",
        help="Path to Verilog source code file for optimization"
    )
    
    tasks = range(1, 6)
    task_arg = dict(
        type=int,
        default=None,
        choices=tasks,
        metavar="TASK",
        help=f"Benchmark task to run. Choices: {list(tasks)}"
    )
    
    #############
    # Simulation
    #############
    
    subparser = subparsers.add_parser('sim', help='Simulate with Icarus Verilog')
    subparser.add_argument("task", **task_arg)
    subparser.add_argument("file", **file_arg)

    #############
    # Synthesis
    #############

    subparser = subparsers.add_parser('synth', help='Synthesize with Yosys')
    subparser.add_argument("file", **file_arg)

    #############
    # Agent
    #############
    
    subparser = subparsers.add_parser('agent', help='Optimize a design with an LLM')
    subparser.add_argument("task", **task_arg)

    
    # if no arguments specified, then print help 
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    

    # because LLM will call tools with just strings,
    # but if we call these from command lines we have filepaths
    if hasattr(args, "file"):
        if not os.path.isfile(args.file):
            raise Exception("Not a valid source code file")
        
        with open(args.file, "r") as f:
            code = f.read()
            

    if args.step == "sim":
        result = sim(code, task=args.task, debug=args.debug)
        
    elif args.step == "synth":
        result = synth(code, debug=args.debug)
    
    elif args.step == "agent":
        result = agent(args.task, debug=args.debug)
    
        
    print(result)
        

if __name__ == "__main__":
    main()
    
