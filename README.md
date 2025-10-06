# AutoPPA - automatic RTL code optimization

## Introduction

This repository introduces AutoPPA - an AI agent which optimizes RTL code for Power, Performance, Area (PPA). In addition to the agent, a benchmark containing 10 optimization tasks is included. Finally, several baselines are provided to see how the AI's performance compares.

## Pre-requisites

[Download Icarus Verilog](https://steveicarus.github.io/iverilog/usage/installation.html) for simulation.

```
sudo apt install iverilog
```

[Download Yosys](https://github.com/YosysHQ/yosys/blob/main/README.md#installation) for synthesis.


## Benchmark

The benchmark uses RTL code gathered from the [PicoRV32 project](https://github.com/YosysHQ/picorv32). This repo is used because the core is configurable with respect to PPA, and thus useful benchmarks can be created from non-optimized (one particular configuration) vs. optimized RTL (a different configuration).

The following configurations (verilog module parameters) are worth noting from the PicoRV32 README:

### ENABLE_FAST_MUL
0: Performance -, Area -
1: Performance +, Area +

### ~~ENABLE_REGS_DUALPORT~~ not used because too messy to untangle
0: Performance -, Area -
1: Performance +, Area +

### TWO_STAGE_SHIFT
0: Performance -, Area +, 
1: Performance +, Area -

### TWO_CYCLE_COMPARE
0: Performance +
1: Performance -

### TWO_CYCLE_ALU
0: Performance +
1: Performance -


The effect these configs have on power is not explicitly shown yet, as there are no available power numbers to compare. However, it is assumed that if the area increases, the power is likely to increase as well.

Here is an example of how to run one of the benchmarks:

```
mkdir build 
cd build
iverilog -o task1 -DDUT_ORIG ../benchmark/tb/task1.v ../benchmark/orig/task1.v
vvp task1
```

To get metrics from synthesis (i.e. area) you will run the following yosys commands:

```
cd build
yosys -p 'read_verilog ../benchmark/orig/task1.v' -p 'synth' -p 'write_verilog synth.v' -l synth.log
```


## Technology

- OpenAI `gpt-5-mini` model as the LLM brain
- Icarus Verilog for simulation
- Yosys for RTL synthesis
- Python for everything else