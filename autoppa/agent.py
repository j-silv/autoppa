from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

# Adapted from VerilogCoder: 
# https://github.com/NVlabs/VerilogCoder/blob/main/hardware_agent/examples/VerilogCoder/prompt_templates.py

SYSTEM_PROMPT = """
You are a Verilog RTL designer that only writes code using correct Verilog syntax based on the optimization task definition.
You will be able to run a simulation and synthesis tool to make sure the design is functionally correct and synthesizable.
If the tools report errors, then debug the Verilog source code and find out the signals/logic that need to be corrected.
Your goal is to improve the baseline metric as much as possible (power, performance, or area).

Rules:
- Only write the verilog code for the current task.
- A test bench already exists to test the functional correctness. You don't need to generate testbench to test the generated Verilog code.
- You can not modify the testbench.
- Don't use any SystemVerilog constructs - only pure Verilog syntax.
- Don't generate duplicated signal assignments or blocks.
- Define the parameters or signals first before using them. 
- for combinational logic, you can use wire assign (i.e., assign wire = a ? 1:0;) or always @(*).
- for combinational logic with an always block do not explicitly specify the sensitivity list; instead use always @(*).
- For 'if' block, you must use begin and end as below.
  if (done) begin
    a = b;
    n = q;
  end
""".strip()


class LLM:
    def __init__(self, system_prompt=SYSTEM_PROMPT, max_context_len=1000, model="gpt-5-mini"):
        super().__init__()
        
        self.system_prompt = system_prompt

        self.max_context_len = max_context_len
        self.model = model
        
        self.messages = [{"role": "system", "content": self.system_prompt}]
        
        self.client = OpenAI()
        
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        
        response = self.client.responses.create(
            model=self.model,
            input=self.messages,
            service_tier="flex"
        )
        
        self.messages.append({"role": "assistant", "content": response.output_text})
        
        return response.output_text
    
    

def agent(task, debug=False):
    with open('benchmark/metadata.json') as f:
        task_info = json.load(f)

    with open(f"baseline/reference/task{task}.v", "r") as f:
        baseline_code = f.read()
    
    with open(f"benchmark/task{task}.v", "r") as f:
        testbench_code = f.read()
        
    task = task_info[task-1]
    user_prompt = (
        f"\nTASK DESCRIPTION:\n{task['description']}\n\n"
        f"BASELINE METRIC:\n{task['baseline']} {task['units']}\n\n"
        f"BASELINE VERILOG CODE:\n{baseline_code}\n\n"
        f"TESTBENCH VERILOG CODE:\n\n{testbench_code}\n"
    )
    
    if debug:
        print(user_prompt)

    model = LLM()
    
    result = model(user_prompt)
    
    return result