from openai import OpenAI
import json
import tiktoken
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from .sim import sim
from .synth import synth

load_dotenv()

# Adapted from VerilogCoder: 
# https://github.com/NVlabs/VerilogCoder/blob/main/hardware_agent/examples/VerilogCoder/prompt_templates.py

SYSTEM_PROMPT = """
You are a Verilog RTL designer that only writes code using correct Verilog syntax based on the optimization task definition.
You will be able to run a simulation and synthesis tool to make sure the design is functionally correct and synthesizable.
If the tools report errors, then debug the Verilog source code and find out the signals/logic that need to be corrected.
Your goal is to improve the baseline metric as much as possible (power, performance, or area).

Rules:
- Only write the verilog code for the current task. Don't generate any other non-verilog text when outputting.
- You shouldn't change the module port list.
- The first line of the output should be the module port list and the last line should be endmodule
- A test bench already exists to test the functional correctness and is provided for reference.
- You can not modify the testbench. Only focus on optimizing DUT.
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

class Role(Enum):
    """Simple enum for different message types"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    """Simple wrapper for when AI agent yields output"""
    role: Role
    content: str


class LLM:
    def __init__(self, system_prompt=SYSTEM_PROMPT, max_context_len=100000, model="gpt-5-mini"):
        """Wrapper around OpenAI model which keeps context (memory)"""
        
        super().__init__()
        
        self.system_prompt = system_prompt

        self.messages = []
        self.max_context_len = max_context_len
        self.curr_context_len = 0 
        
        self.model = model
        self.enc = tiktoken.encoding_for_model(model)
        
        self.add_to_context(self.system_prompt, "system")
        
        self.client = OpenAI()
        
    def add_to_context(self, message, role="user", update_len=True):
        """Helper function to add to context and truncate if necessary"""
        
        self.messages.append({"role": role, "content": message})
        
        if update_len:
            self.curr_context_len += len(self.enc.encode(message))
            
        if self.curr_context_len > self.max_context_len:
            self.truncate()
        
        
    def __call__(self, message):
        """Run the inference"""
        
        self.add_to_context(message)
        
        stream = self.client.responses.create(
            model=self.model,
            input=self.messages,
            stream=True
        )
        
        output_text = []
        for event in stream:
            
            if event.type == 'error':
                raise Exception("Error generating text during LLM inference", event)
            
            if event.type == "incomplete" and event.response.incomplete_details.reason == "max_output_tokens":
                raise Exception("Max output tokens reached when running inference")
                        
            if event.type == 'response.output_text.delta':
                output_text.append(event.delta)
                yield event.delta
            
            elif event.type == 'response.completed':
                # this includes reasoning tokens, so we can't just tokenize the output text
                # to get the token amount. also note that input_tokens length is slightly different than tiktoken expects
                # (probably due to assistant/user role tokens)
                self.curr_context_len += event.response.usage.output_tokens
        
        self.add_to_context("".join(output_text), "assistant", update_len=False)
        
        
    def truncate(self):
        """Chop off previous context if length exceeds limit"""
        
        curr_context_len = 0
        for i in range(len(self.messages)-1, -1, -1):
            
            tokenized_message = self.enc.encode(self.messages[i]['content'])
            curr_message_len = len(tokenized_message)
            
            curr_context_len += curr_message_len
            
            remaining_tokens = self.max_context_len - curr_context_len
            
            if remaining_tokens < 0 :
                
                # first truncate all messages before this index
                self.messages = self.messages[i:]
                
                # then partially truncate this message
                self.messages[-1]['content'] = self.enc.decode(tokenized_message[-remaining_tokens:])
                
                self.curr_context_len = self.max_context_len
                
                return

class Agent:
    def __init__(self, task_num, debug=False,
                 system_prompt=None,
                 initial_prompt=None, max_context_len=100000,
                 max_iters=5):
        
        """AI agent which tries to optimize Verilog HDL code for a given task
        
        In this initialization, we load the task information from the metadata,
        create the LLM model to perform inference, and then prepare the initial
        prompt passed which will kick off the AI agent loop
        """

        self.debug = debug
        self.max_iters = max_iters
        
        with open('benchmark/metadata.json') as f:
            task_info = json.load(f)

        self.task = task_info[task_num-1]
        self.task_num = task_num

        with open(f"baseline/reference/task{task_num}.v", "r") as f:
            baseline_code = f.read()
        
        with open(f"benchmark/task{task_num}.v", "r") as f:
            testbench_code = f.read()
        
        if initial_prompt:
            self.initial_prompt = initial_prompt
        else:
            self.initial_prompt = (
                f"\nTASK DESCRIPTION:\n{self.task['description']}\n\n"
                f"BASELINE METRIC:\n{self.task['baseline']} {self.task['units']}\n\n"
                f"BASELINE VERILOG CODE:\n{baseline_code}\n\n"
                f"TESTBENCH VERILOG CODE:\n\n{testbench_code}\n"
            )
            
        self.model = LLM(system_prompt=system_prompt if system_prompt else SYSTEM_PROMPT,
                         max_context_len=max_context_len)
        
    def __call__(self):
        """Run the optimization task with an LLM in a loop
        
        The LLM will output Verilog code which will then be tested with
        a simulation and a synthesis. If both pass, the LLM will be provided
        with PPA information. The agent will then decide whether or not to 
        keep iterating on the design so as to achieve the best optimization.
        
        The iterations stop when we reach 'max_iters' or the user manually 
        stops the loop.
        
        The best LLM output (with respect to PPA) is saved. At the end of the loop,
        we output this module again, along with the PPA metrics.
        
        This function is a generator which yields a tuple. The first element is the
        output 'role' (system/user/assistant/tool), and the second element is the 
        actual message.
        """

        yield Message(Role.SYSTEM, self.model.system_prompt) 

        user_prompt = self.initial_prompt
        
        for i in range(self.max_iters):
            
            if self.debug:
                print(f"ITERATION {i}/{self.max_iters}")
            
            result = []
            yield Message(Role.USER, user_prompt)

            messages = self.model(user_prompt)

            for message in messages:
                result.append(message)
                yield Message(Role.ASSISTANT, message)
                
            result = "".join(result)
            
            if self.debug:
                print(f"\nCURRENT CONTEXT WINDOW LENGTH: {self.model.curr_context_len} tokens\n")
            
            user_prompt = ["Feedback from compilation, simulation, and synthesis tools:\n\n"]
            yield Message(Role.TOOL, user_prompt[-1])
            
            sim_result = sim(result, task=self.task_num, debug=self.debug)
            user_prompt.append(sim_result + "\n")
            yield Message(Role.TOOL, user_prompt[-1])
            
            synth_result = synth(result, debug=self.debug)
            user_prompt.append(synth_result + "\n")
            yield Message(Role.TOOL, user_prompt[-1])
            
            user_prompt = "".join(user_prompt)

            print("Agent step done.")
            cont = input("Continue? [y/n] ")
            if cont.lower() != "y":
                break
            
        else:
            print("Max iters reached. Exiting agent loop.")    
        
