// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

//// Replace this comment with your code.

@R2
M=0 //set RAM[2] to 0

(LOOP)
    @R1
    D=M //get RAM[1], or the amount of times to iterate

    @END
    D;JEQ //end if no iterations left

    @R0
    D=M //get value you want to be added repeatedly

    @R2
    M=D+M //add value to RAM[2]

    @R1
    M=M-1 //decrease iterator

    @LOOP
    0;JMP //jump to top of loop

(END)
    @END
    0;JMP