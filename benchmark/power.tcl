read_liberty autoppa/benchmark/sky130hd_tt.lib
read_verilog autoppa/build/synth/synth_{MODULE_NAME}.v
link_design {MODULE_NAME}

# Define the clock domain
create_clock -name clk -period 10 {clk}

# (Optional) Specify input/output delays relative to the clock
# set_input_delay 0.5 -clock clk [all_inputs]
# set_output_delay 0.5 -clock clk [all_outputs]

# Load switching activity from simulation
read_vcd autoppa/build/task{TASK_NUM}/{MODULE_NAME}.vcd -scope task{TASK_NUM}_tb
report_power
report_power > autoppa/build/task{TASK_NUM}/{MODULE_NAME}.rpt