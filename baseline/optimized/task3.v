module picorv32_pcpi_div (
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
		instr_div  <= 0;
		instr_divu <= 0;
		instr_rem  <= 0;
		instr_remu <= 0;

		if (resetn && pcpi_valid && !pcpi_ready &&
		    pcpi_insn[6:0] == 7'b0110011 &&
		    pcpi_insn[31:25] == 7'b0000001) begin
			case (pcpi_insn[14:12])
				3'b100: instr_div  <= 1;
				3'b101: instr_divu <= 1;
				3'b110: instr_rem  <= 1;
				3'b111: instr_remu <= 1;
			endcase
		end

		pcpi_wait   <= instr_any_div_rem && resetn;
		pcpi_wait_q <= pcpi_wait && resetn;
	end

	// internal state
	reg [31:0] dividend, divisor, quotient;
	reg [63:0] u_dividend_ext, u_divisor_ext;
	reg [5:0] bit;
	reg running;
	reg outsign;

	always @(posedge clk) begin
		pcpi_ready <= 0;
		pcpi_wr    <= 0;
		pcpi_rd    <= 'bx;

		if (!resetn) begin
			running <= 0;
			bit <= 0;
		end else if (start) begin
			if (pcpi_rs2 == 0) begin
				// divide by zero
				running <= 0;
				pcpi_ready <= 1;
				pcpi_wr <= 1;
				if (instr_div || instr_divu)
					pcpi_rd <= 32'hFFFF_FFFF;
				else
					pcpi_rd <= pcpi_rs1;
			end else begin
				running <= 1;
				bit <= 31;
				quotient <= 0;

				if (instr_div || instr_rem) begin
					// signed
					dividend <= pcpi_rs1[31] ? -pcpi_rs1 : pcpi_rs1;
					divisor  <= pcpi_rs2[31] ? -pcpi_rs2 : pcpi_rs2;
					outsign  <= (instr_div && (pcpi_rs1[31] != pcpi_rs2[31])) || (instr_rem && pcpi_rs1[31]);
				end else begin
					// unsigned
					u_dividend_ext <= {32'b0, pcpi_rs1};
					u_divisor_ext  <= {32'b0, pcpi_rs2};
					outsign        <= 0;
				end
			end
		end else if (running) begin
			if (bit == 6'd63) begin
				// finished
				running <= 0;
				pcpi_ready <= 1;
				pcpi_wr <= 1;

				if (instr_div)
					pcpi_rd <= outsign ? -quotient : quotient;
				else if (instr_rem)
					pcpi_rd <= outsign ? -dividend : dividend;
				else if (instr_divu)
					pcpi_rd <= quotient;
				else // REMU
					pcpi_rd <= u_dividend_ext[31:0];
			end else begin
				if (instr_div || instr_rem) begin
					// signed shift-subtract
					if ((divisor << bit) <= dividend) begin
						dividend <= dividend - (divisor << bit);
						quotient <= quotient | (1 << bit);
					end
				end else begin
					// unsigned shift-subtract using 64-bit
					if ((u_divisor_ext << bit) <= u_dividend_ext) begin
						u_dividend_ext <= u_dividend_ext - (u_divisor_ext << bit);
						quotient <= quotient | (1 << bit);
					end
				end
				bit <= bit - 1;
			end
		end
	end
endmodule
