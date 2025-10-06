`timescale 1ns / 1ps

module tb_mul_top;

    reg clk;
    reg resetn;
    reg pcpi_valid;
    reg [31:0] pcpi_insn;
    reg [31:0] pcpi_rs1;
    reg [31:0] pcpi_rs2;
    wire pcpi_wr;
    wire [31:0] pcpi_rd;
    wire pcpi_wait;
    wire pcpi_ready;

    //----------------------------------------------------------
    // DUT selection — choose which module to instantiate
    //----------------------------------------------------------
`ifdef DUT_CANDIDATE
    // Candidate optimized version
    picorv32_pcpi_mul_candidate dut (
        .clk(clk),
        .resetn(resetn),
        .pcpi_valid(pcpi_valid),
        .pcpi_insn(pcpi_insn),
        .pcpi_rs1(pcpi_rs1),
        .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr),
        .pcpi_rd(pcpi_rd),
        .pcpi_wait(pcpi_wait),
        .pcpi_ready(pcpi_ready)
    );
    initial $display("=== Running test with: picorv32_pcpi_mul_candidate ===");

`elsif DUT_ORIG
    // Reference non-optimized version
    picorv32_pcpi_mul_orig dut (
        .clk(clk),
        .resetn(resetn),
        .pcpi_valid(pcpi_valid),
        .pcpi_insn(pcpi_insn),
        .pcpi_rs1(pcpi_rs1),
        .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr),
        .pcpi_rd(pcpi_rd),
        .pcpi_wait(pcpi_wait),
        .pcpi_ready(pcpi_ready)
    );
    initial $display("=== Running test with: picorv32_pcpi_mul_orig ===");

`elsif DUT_OPT
    // Ground-truth optimized version
    picorv32_pcpi_mul_opt dut (
        .clk(clk),
        .resetn(resetn),
        .pcpi_valid(pcpi_valid),
        .pcpi_insn(pcpi_insn),
        .pcpi_rs1(pcpi_rs1),
        .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr),
        .pcpi_rd(pcpi_rd),
        .pcpi_wait(pcpi_wait),
        .pcpi_ready(pcpi_ready)
    );
    initial $display("=== Running test with: picorv32_pcpi_mul_opt ===");

`else
    // Default (reference) version
    DUT_CANDIDATE dut (
        .clk(clk),
        .resetn(resetn),
        .pcpi_valid(pcpi_valid),
        .pcpi_insn(pcpi_insn),
        .pcpi_rs1(pcpi_rs1),
        .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr),
        .pcpi_rd(pcpi_rd),
        .pcpi_wait(pcpi_wait),
        .pcpi_ready(pcpi_ready)
    );
    initial $display("=== Running test with: picorv32_pcpi_mul_candidate ===");
`endif

    //----------------------------------------------------------
    // Clock generation
    //----------------------------------------------------------
    initial clk = 0;
    initial resetn = 0;
    always #5 clk = ~clk; // 100 MHz


    `ifdef DEBUG
        initial begin
            $display("time ns:        pcpi_valid pcpi_wait pcpi_ready pcpi_wr pcpi_rd");
            $monitor("%0t:            %b         %b         %b        %b    %h",
                 $time, pcpi_valid, pcpi_wait, pcpi_ready, pcpi_wr, pcpi_rd);
        end
    `endif


    reg any_failures;
    integer cycles = 0;
    initial any_failures = 0;


    initial begin
        #1000000; // 1,000,000 ns = 1 ms, adjust as needed
        $display("*** TIMEOUT: Simulation exceeded maximum time ***");
        $finish;
    end

    //----------------------------------------------------------
    // Helper task
    //----------------------------------------------------------
    task do_mul(
        input [31:0] rs1,
        input [31:0] rs2,
        input [2:0] funct3,
        input [127:0] name
    );
        reg [63:0] expected;
        reg passed;
 
    begin
        pcpi_rs1 = rs1;
        pcpi_rs2 = rs2;
        pcpi_insn = {7'b0000001, rs2[4:0], rs1[4:0], funct3, 5'b00000, 7'b0110011};

        // Start the handshake
        @(posedge clk);
        pcpi_valid = 1;

        // Wait for ready
        while (pcpi_ready != 1'b1) begin
            @(negedge clk);
            cycles = cycles + 1;
        end

        // One more clock to latch result
        @(posedge clk);
        pcpi_valid = 0;


        case (funct3)
            3'b000: expected = $signed({{32{rs1[31]}}, rs1}) * 
                            $signed({{32{rs2[31]}}, rs2});
            3'b001: expected = ($signed({{32{rs1[31]}}, rs1}) *
                                $signed({{32{rs2[31]}}, rs2})) >> 32;
            3'b010: expected = ($signed({{32{rs1[31]}}, rs1}) *
                                $unsigned({32'b0, rs2})) >> 32;
            3'b011: expected = ($unsigned({32'b0, rs1}) *
                                $unsigned({32'b0, rs2})) >> 32;
        endcase


        passed = (pcpi_rd === expected[31:0]);
        if (!passed) any_failures = 1;

        $display("%s: rs1=%0d rs2=%0d -> DUT=%0d expected=%0d %s",
                name, rs1, rs2, pcpi_rd, expected[31:0],
                passed ? "PASS" : "FAIL");

    end
    endtask

    //----------------------------------------------------------
    // Test sequence
    //----------------------------------------------------------
    initial begin
        $display("Starting multiply testbench...");
        resetn = 0;
        pcpi_valid = 0;
        #8 resetn = 1;

        do_mul(32'd3, 32'd7, 3'b000, "MUL");
        do_mul(-32'd3, 32'd7, 3'b000, "MUL negative");
        do_mul(32'd1000, 32'd1000, 3'b000, "MUL large");
        do_mul(-32'd10, -32'd4, 3'b001, "MULH signed");
        do_mul(-32'd10, 32'd4, 3'b010, "MULHSU mixed");
        do_mul(32'hFFFFFFFF, 32'hFFFFFFFF, 3'b011, "MULHU unsigned");

        repeat (10) @(posedge clk);
        if (any_failures)
            $display("\nSome tests FAILED!\n");
        else
            $display("\nAll tests PASSED successfully!");
            $display("DUT time (ns): %0d", cycles*10);
        $finish;
    end

endmodule
