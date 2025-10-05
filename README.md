# AutoPPA - automatic RTL code optimization

## Introduction

This repository introduces AutoPPA - an AI agent which optimizes RTL code for Power, Performance, Area (PPA). In addition to the agent, a benchmark containing 10 optimization tasks is included. Finally, several baselines are provided to see how the AI's performance compares.

## Technology

- OpenAI `gpt-5-mini` model as the LLM brain
- Icarus Verilog for simulation
- Yosys for RTL synthesis
- Python for everything else