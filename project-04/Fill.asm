// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.


// ------------------------- ENTRY ------------------------- 

(ENTRY)

@KBD
D=M

@FILLWHITE
M=D // store pressed character key in @FILLWHITE, so it's either 0 or some value

// ------------------------- END ENTRY --------------------- 


// ------------------------- FILL ------------------------- 

@SCREEN
D=A // store screen address in D

@addr
M=D // store screen address in @addr

// idk weird workaround to store 8192
@8192
D=A 
@i
M=D

(LOOPBLACK)

    @FILLWHITE
    D=M

    @SETWHITE
    D;JEQ

    // -------- SET LINE TO BLACK
    @addr
    A=M // set register to @addr
    M=-1 // set that 16 screen block to black

    @CONTINUE
    0;JMP

    // ------- SET LINE TO WHITE
    (SETWHITE)
    @addr
    A=M // set register to @addr
    M=0 // set that 16 screen block to black

    (CONTINUE)

    @addr
    M=M+1

    @i
    M=M-1
    D=M

    @ENTRY
    D;JEQ // return to start if no iterations left

    @LOOPBLACK
    0;JEQ
    
// ------------------------- END FILL ---------------------