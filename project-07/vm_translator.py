import glob
import os

LABEL_INDEX = 0

CURRENT_FILE_NAME = "NO_FILE_SELECTED"

SEGMENTS = {"argument": "ARG", "local": "LCL", "this": "THIS", "that": "THAT"}


def clean(lines: list[str]) -> list[str]:
    """Removes comments and empty lines."""
    return [
        line.split("//")[0].strip()
        for line in lines
        if line.strip() and not line.startswith("//")
    ]


def generate_label(name: str) -> str:
    """Generates unique labels for comparisons."""
    global LABEL_INDEX
    LABEL_INDEX += 1
    return f"{name}_{LABEL_INDEX}"


def comparison(condition: str) -> list[str]:
    """Handles eq, gt, lt."""
    true_label = generate_label(f"{condition}_TRUE")
    end_label = generate_label(f"{condition}_END")

    return [
        "@SP",
        "AM=M-1",
        "D=M",
        "A=A-1",
        "D=M-D",
        f"@{true_label}",
        f"D;J{condition}",
        "@SP",
        "A=M-1",
        "M=0",
        f"@{end_label}",
        "0;JMP",
        f"({true_label})",
        "@SP",
        "A=M-1",
        "M=-1",
        f"({end_label})",
    ]


def arithmetic(command: str) -> list[str]:
    """Handles arithmetic commands"""

    if command == "add":
        return ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D+M"]
    elif command == "sub":
        return ["@SP", "AM=M-1", "D=M", "A=A-1", "M=M-D"]
    elif command == "and":
        return ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D&M"]
    elif command == "or":
        return ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D|M"]

    elif command == "neg":
        return ["@SP", "A=M-1", "M=-M"]
    elif command == "not":
        return ["@SP", "A=M-1", "M=!M"]

    elif command in {"eq", "gt", "lt"}:
        return comparison(command.upper())

    raise Exception(f"Unknown arithmetic command: {command}")


def push(segment: str, index: str) -> list[str]:
    """Handles push commands."""
    if segment == "constant":
        return [f"@{index}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
    elif segment in SEGMENTS:
        return [
            f"@{index}",
            "D=A",
            f"@{SEGMENTS[segment]}",
            "A=D+M",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]
    elif segment == "temp":
        return [f"@{5 + int(index)}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
    elif segment == "pointer":
        return [
            f"@{'THIS' if index == '0' else 'THAT'}",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]
    elif segment == "static":
        return [
            f"@{CURRENT_FILE_NAME}.{index}",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        ]

    raise Exception(f"Invalid push operation: push {segment} {index}")


def pop(segment: str, index: str) -> list[str]:
    """Handles pop commands."""
    if segment in SEGMENTS:
        return [
            f"@{index}",
            "D=A",
            f"@{SEGMENTS[segment]}",
            "D=D+M",
            "@R13",
            "M=D",
            "@SP",
            "AM=M-1",
            "D=M",
            "@R13",
            "A=M",
            "M=D",
        ]
    elif segment == "temp":
        return ["@SP", "AM=M-1", "D=M", f"@{5 + int(index)}", "M=D"]
    elif segment == "pointer":
        return ["@SP", "AM=M-1", "D=M", f"@{'THIS' if index == '0' else 'THAT'}", "M=D"]
    elif segment == "static":
        return ["@SP", "AM=M-1", "D=M", f"@{CURRENT_FILE_NAME}.{index}", "M=D"]
    raise Exception(f"Invalid pop operation: pop {segment} {index}")


def translate(vm_code: list[str]) -> list[str]:
    """Converts VM to Hack assembly."""
    cleaned_vm_code = clean(vm_code)

    asm_code = []

    for line in cleaned_vm_code:
        asm_code.append("// " + line)

        parts = line.split(" ")
        command = parts[0]

        if command in {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}:
            asm_code.extend(arithmetic(command))
        elif command == "push":
            asm_code.extend(push(parts[1], parts[2]))
        elif command == "pop":
            asm_code.extend(pop(parts[1], parts[2]))

    return asm_code


def main():
    global CURRENT_FILE_NAME

    vm_files = glob.glob("files/*.vm")

    for vm_file in vm_files:
        with open(vm_file, "r", encoding="utf-8") as f_in:
            vm_code = f_in.readlines()
        assembly_code = translate(vm_code)

        base_path = os.path.splitext(vm_file)[0]
        CURRENT_FILE_NAME = base_path.replace("files/", "")

        asm_file = base_path + ".asm"
        with open(asm_file, "w", encoding="utf-8") as f_out:
            f_out.writelines("\n".join(assembly_code))

        print(f"Converted {vm_file} -> {asm_file}")


if __name__ == "__main__":
    main()
