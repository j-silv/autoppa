module task5_ref (
    input clk, resetn,
    input             pcpi_valid,
    input      [31:0] pcpi_insn,
    input      [31:0] pcpi_rs1,
    input      [31:0] pcpi_rs2,
    output reg        pcpi_wr,
    output reg [31:0] pcpi_rd,
    output reg        pcpi_wait,
    output reg        pcpi_ready
);
    reg instr_div, instr_divu, instr_rem, instr_remu;
    wire instr_any_div_rem = |{instr_div, instr_divu, instr_rem, instr_remu};

    reg pcpi_wait_q;
    wire start = pcpi_wait && !pcpi_wait_q;

    always @(posedge clk) begin
        if (!resetn) begin
            instr_div <= 0; instr_divu <= 0; instr_rem <= 0; instr_remu <= 0;
            pcpi_wait <= 0; pcpi_wait_q <= 0;
        end else begin
            if (pcpi_valid && !pcpi_ready &&
                pcpi_insn[6:0] == 7'b0110011 &&
                pcpi_insn[31:25] == 7'b0000001) begin
                instr_div  <= (pcpi_insn[14:12] == 3'b100);
                instr_divu <= (pcpi_insn[14:12] == 3'b101);
                instr_rem  <= (pcpi_insn[14:12] == 3'b110);
                instr_remu <= (pcpi_insn[14:12] == 3'b111);
            end else begin
                instr_div  <= 0; instr_divu <= 0; instr_rem <= 0; instr_remu <= 0;
            end
            pcpi_wait <= instr_any_div_rem;
            pcpi_wait_q <= pcpi_wait;
        end
    end

    reg [31:0] dividend;
    reg [31:0] divisor;
    reg [31:0] quotient;
    reg [31:0] remainder;
    reg [31:0] quotient_mask;
    reg running;
    reg outsign, remsign;

    wire div_by_zero = (pcpi_rs2 == 0);
    wire div_overflow = (instr_div && pcpi_rs1 == 32'h80000000 && pcpi_rs2 == -1);

    always @(posedge clk) begin
        if (!resetn) begin
            running <= 0;
            pcpi_ready <= 0;
            pcpi_wr <= 0;
            pcpi_rd <= 0;
        end else begin
            pcpi_ready <= 0;
            pcpi_wr <= 0;
            pcpi_rd <= 'bx;

            if (start) begin
                if (div_by_zero) begin
                    running <= 0;
                    pcpi_ready <= 1;
                    pcpi_wr <= 1;
                    if (instr_div || instr_divu)
                        pcpi_rd <= instr_div ? -1 : 32'hFFFFFFFF;
                    else
                        pcpi_rd <= pcpi_rs1;
                end else if (div_overflow) begin
                    running <= 0;
                    pcpi_ready <= 1;
                    pcpi_wr <= 1;
                    pcpi_rd <= instr_div ? 32'h80000000 : 0;
                end else begin
                    running <= 1;

                    // ---- prepare absolute operands ----
                    if (instr_div || instr_rem) begin
                        dividend <= pcpi_rs1[31] ? -pcpi_rs1 : pcpi_rs1;
                        divisor <= pcpi_rs2[31] ? -pcpi_rs2 : pcpi_rs2;
                        outsign <= instr_div && (pcpi_rs1[31] ^ pcpi_rs2[31]);
                        remsign <= instr_rem && pcpi_rs1[31];
                    end else begin
                        dividend <= pcpi_rs1;
                        divisor <= pcpi_rs2;
                        outsign <= 0;
                        remsign <= 0;
                    end
                    quotient <= 0;
                    remainder <= 0;
                    quotient_mask <= 1 << 31;
                end
            end else if (running) begin
                if (quotient_mask == 0) begin
                    running <= 0;
                    pcpi_ready <= 1;
                    pcpi_wr <= 1;
                    if (instr_div || instr_divu)
                        pcpi_rd <= outsign ? -quotient : quotient;
                    else
                        pcpi_rd <= remsign ? -remainder : remainder;
                end else begin
                    // Shift-subtract division algorithm
                    remainder = (remainder << 1) | (dividend[31]);
                    dividend = dividend << 1;
                    if (remainder >= divisor) begin
                        remainder = remainder - divisor;
                        quotient = quotient | quotient_mask;
                    end
                    quotient_mask = quotient_mask >> 1;
                end
            end
        end
    end
endmodule
