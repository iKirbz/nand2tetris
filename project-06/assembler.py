SYMBOL_TABLE = {
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
}

DEST_TABLE = {
    "": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}

COMP_TABLE = {
    # a = 0
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "!D": "0001101",
    "!A": "0110001",
    "-D": "0001111",
    "-A": "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    # a = 1
    "M": "1110000",
    "!M": "1110001",
    "-M": "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}

JUMP_TABLE = {
    "": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

VARIABLE_ADDRESS = 16


def cleanup_lines(lines: list[str]) -> list[str]:
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line == "":
            continue
        if line.startswith("//"):
            continue
        cleaned_lines.append(line)

    return cleaned_lines


def first_pass(lines: list[str]):
    line_counter = 0

    for line in lines:
        if line.startswith("("):
            label = line[1:-1]
            SYMBOL_TABLE[label] = line_counter
        else:
            line_counter += 1


def parse_a_instruction(address):
    global VARIABLE_ADDRESS
    if address.isdigit():
        return format(int(address), "016b")

    if address not in SYMBOL_TABLE:
        SYMBOL_TABLE[address] = VARIABLE_ADDRESS
        VARIABLE_ADDRESS += 1

    return format(SYMBOL_TABLE[address], "016b")


def parse_c_instruction(line):
    dest, comp, jump = "", line, ""

    if "=" in line:
        dest, comp = line.split("=")

    if ";" in comp:
        comp, jump = comp.split(";")

    comp_bin = COMP_TABLE.get(comp, "0000000")
    dest_bin = DEST_TABLE.get(dest, "000")
    jump_bin = JUMP_TABLE.get(jump, "000")

    return "111" + comp_bin + dest_bin + jump_bin


def second_pass(lines: list[str]):
    out = []

    for line in lines:
        if line.startswith("("):
            continue
        if line.startswith("@"):
            out.append(parse_a_instruction(line[1:]))
        else:
            out.append(parse_c_instruction(line))

    return out


def assemble(file_name):
    with open(file_name, "r") as file:
        asm_code = file.readlines()
    clean_input = cleanup_lines(asm_code)
    first_pass(clean_input)
    machine_code = second_pass(clean_input)

    return machine_code
