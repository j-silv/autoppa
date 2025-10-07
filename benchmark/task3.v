`timescale 1ns / 1ps

`define STRINGIFY(str, DEFINE) $sformatf(str, `"DEFINE`")

module task3_tb;

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

   `DUT_NAME dut (
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
        $dumpfile(`STRINGIFY("build/task3/%s.vcd", `DUT_NAME));
        $dumpvars(0, task3_tb);
        #1000000; // 1,000,000 ns = 1 ms, adjust as needed
        $display("TIMEOUT: Simulation FAILED due to exceeded maximum time");
        $finish;
    end

    //----------------------------------------------------------
    // Helper task
    //----------------------------------------------------------
    task do_op(
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
            3'b100: begin // DIV
                if (rs2 == 0)
                    expected = -1; // div by zero → -1 per RISC-V spec
                else if ((rs1 == 32'h80000000) && (rs2 == -1))
                    expected = 32'h80000000; // overflow
                else
                    expected = $signed(rs1) / $signed(rs2);
            end
            3'b101: begin // DIVU
                if (rs2 == 0)
                    expected = 32'hFFFFFFFF;
                else
                    expected = $unsigned(rs1) / $unsigned(rs2);
            end
            3'b110: begin // REM
                if (rs2 == 0)
                    expected = rs1;
                else if ((rs1 == 32'h80000000) && (rs2 == -1))
                    expected = 0;
                else
                    expected = $signed(rs1) % $signed(rs2);
            end
            3'b111: begin // REMU
                if (rs2 == 0)
                    expected = rs1;
                else
                    expected = $unsigned(rs1) % $unsigned(rs2);
            end
            default: expected = 0;
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
        $display("Starting testbench...");
        resetn = 0;
        pcpi_valid = 0;
        #8 resetn = 1;

        // ---- SIGNED DIV ----
        do_op( 20,   3, 3'b100, "DIV 20 / 3");
        do_op(-20,   3, 3'b100, "DIV -20 / 3");
        do_op( 20,  -3, 3'b100, "DIV 20 / -3");
        do_op(-20,  -3, 3'b100, "DIV -20 / -3");
        do_op(32'h80000000, -1, 3'b100, "DIV overflow");
        do_op(20,   0, 3'b100, "DIV divide-by-zero");

        // ---- UNSIGNED DIV ----
        do_op( 20,   3, 3'b101, "DIVU 20 / 3");
        do_op( 20,   0, 3'b101, "DIVU divide-by-zero");
        do_op(32'hFFFFFFFF, 2, 3'b101, "DIVU max/2");

        // ---- SIGNED REM ----
        do_op( 20,   3, 3'b110, "REM 20 % 3");
        do_op(-20,   3, 3'b110, "REM -20 % 3");
        do_op( 20,  -3, 3'b110, "REM 20 % -3");
        do_op(-20,  -3, 3'b110, "REM -20 % -3");
        do_op(32'h80000000, -1, 3'b110, "REM overflow");
        do_op(20,   0, 3'b110, "REM divide-by-zero");

        // ---- UNSIGNED REM ----
        do_op( 20,   3, 3'b111, "REMU 20 % 3");
        do_op( 20,   0, 3'b111, "REMU divide-by-zero");
        do_op(32'hFFFFFFFF, 2, 3'b111, "REMU max%2");
            
        repeat (10) @(posedge clk);
        if (any_failures) begin
            $display("\nSome tests FAILED!");
        end else begin
            $display("\nAll tests PASSED successfully!");
            $display("TIME: %0d (ns)", cycles*10);
        end
        $finish;

    end

endmodule
