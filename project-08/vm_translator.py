import glob
import os


class VMTranslator:
    SEGMENTS = {"argument": "ARG", "local": "LCL", "this": "THIS", "that": "THAT"}

    def __init__(self):
        self.lines: list[str] = []
        self.label_index = 0
        self.call_return_index = 0
        self.current_file = "NO_FILE_SELECTED"

    def write(self, code: list[str]):
        """Append assembly code lines."""
        self.lines.extend(code)

    def generate_label(self, base: str) -> str:
        """Generates a unique label based on a given base name."""
        self.label_index += 1
        return f"{base}_{self.label_index}"

    def comparison(self, condition: str):
        true_label = self.generate_label(f"{condition}_TRUE")
        end_label = self.generate_label(f"{condition}_END")
        self.write(
            [
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
        )

    def arithmetic(self, command: str):
        if command == "add":
            self.write(["@SP", "AM=M-1", "D=M", "A=A-1", "M=D+M"])
        elif command == "sub":
            self.write(["@SP", "AM=M-1", "D=M", "A=A-1", "M=M-D"])
        elif command == "and":
            self.write(["@SP", "AM=M-1", "D=M", "A=A-1", "M=D&M"])
        elif command == "or":
            self.write(["@SP", "AM=M-1", "D=M", "A=A-1", "M=D|M"])
        elif command == "neg":
            self.write(["@SP", "A=M-1", "M=-M"])
        elif command == "not":
            self.write(["@SP", "A=M-1", "M=!M"])
        elif command in {"eq", "gt", "lt"}:
            self.comparison(command.upper())
        else:
            raise Exception(f"Unknown arithmetic command: {command}")

    def push(self, segment: str, index: str):
        if segment == "constant":
            self.write([f"@{index}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
        elif segment in self.SEGMENTS:
            seg = self.SEGMENTS[segment]
            self.write(
                [
                    f"@{index}",
                    "D=A",
                    f"@{seg}",
                    "A=D+M",
                    "D=M",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1",
                ]
            )
        elif segment == "temp":
            addr = 5 + int(index)
            self.write([f"@{addr}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
        elif segment == "pointer":
            pointer = "THIS" if index == "0" else "THAT"
            self.write([f"@{pointer}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
        elif segment == "static":
            self.write(
                [
                    f"@{self.current_file}.{index}",
                    "D=M",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1",
                ]
            )
        else:
            raise Exception(f"Invalid push operation: push {segment} {index}")

    def pop(self, segment: str, index: int):
        if segment in self.SEGMENTS:
            self.write(
                [
                    f"@{index}",
                    "D=A",
                    f"@{self.SEGMENTS[segment]}",
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
            )
        elif segment == "temp":
            self.write(["@SP", "AM=M-1", "D=M", f"@{5 + index}", "M=D"])
        elif segment == "pointer":
            pointer = "THIS" if index == 0 else "THAT"
            self.write(["@SP", "AM=M-1", "D=M", f"@{pointer}", "M=D"])
        elif segment == "static":
            self.write(["@SP", "AM=M-1", "D=M", f"@{self.current_file}.{index}", "M=D"])
        else:
            raise Exception(f"Invalid pop operation: pop {segment} {index}")

    def label(self, label_name: str):
        self.write([f"({label_name})"])

    def goto(self, label_name: str):
        self.write([f"@{label_name}", "0;JMP"])

    def if_goto(self, label_name: str):
        self.write(["@SP", "AM=M-1", "D=M", f"@{label_name}", "D;JNE"])

    def function(self, function_name: str, local_count: int):
        self.label(function_name)
        for _ in range(local_count):
            self.push("constant", "0")

    def translate_return(self):
        # store lcl in R14
        self.write(["@LCL", "D=M", "@R14", "M=D"])
        # store frame in R13
        self.write(["@5", "A=D-A", "D=M", "@R13", "M=D"])

        # place return value to arg 0
        self.write(["@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D"])

        # reposition sp to arg
        self.write(["@ARG", "D=M+1", "@SP", "M=D"])

        # restore segments
        self.write(["@R14", "D=M", "@4", "A=D-A", "D=M", "@LCL", "M=D"])
        self.write(["@R14", "D=M", "@3", "A=D-A", "D=M", "@ARG", "M=D"])
        self.write(["@R14", "D=M", "@2", "A=D-A", "D=M", "@THIS", "M=D"])
        self.write(["@R14", "D=M", "@1", "A=D-A", "D=M", "@THAT", "M=D"])

        # jump to stack frame
        self.write(["@R13", "A=M", "0;JMP"])

    def translate_call(self, function_name: str, arg_count: int):
        self.call_return_index += 1
        ret_addr = f"ret.{self.call_return_index}"
        push_seq = ["@SP", "A=M", "M=D", "@SP", "M=M+1"]
        self.write([f"@{ret_addr}", "D=A"] + push_seq)  # push return address
        self.write(["@LCL", "D=M"] + push_seq)  # push LCL
        self.write(["@ARG", "D=M"] + push_seq)  # push ARG
        self.write(["@THIS", "D=M"] + push_seq)  # push THIS
        self.write(["@THAT", "D=M"] + push_seq)  # push THAT
        # reposition ARG
        self.write([f"@{5 + arg_count}", "D=A", "@SP", "D=M-D", "@ARG", "M=D"])
        self.write(["@SP", "D=M", "@LCL", "M=D"])  # LCL = SP
        self.write([f"@{function_name}", "0;JMP"])  # goto function
        self.lines.append(f"({ret_addr})")  # declare return label

    def bootstrap(self):
        """Write bootstrap code to initialize SP and call Sys.init."""
        self.write(["@256", "D=A", "@SP", "M=D"])
        self.translate_call("Sys.init", 0)

    # --- Translation Routines ---

    def translate_vm_code(self, code: list[str]):
        for line in code:
            self.lines.append(f"// {line}")
            parts = line.split()
            cmd = parts[0]
            if cmd in {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}:
                self.arithmetic(cmd)
            elif cmd == "push":
                self.push(parts[1], parts[2])
            elif cmd == "pop":
                self.pop(parts[1], int(parts[2]))
            elif cmd == "label":
                self.label(parts[1])
            elif cmd == "goto":
                self.goto(parts[1])
            elif cmd == "if-goto":
                self.if_goto(parts[1])
            elif cmd == "function":
                self.function(parts[1], int(parts[2]))
            elif cmd == "call":
                self.translate_call(parts[1], int(parts[2]))
            elif cmd == "return":
                self.translate_return()
            else:
                raise Exception(f"Unsupported command: {line}")

    def translate_file(self, file_name: str, code: list[str]):
        """Translate a single VM file given only the file name."""
        self.current_file = file_name
        self.translate_vm_code(code)

    def get_translated_code(self) -> list[str]:
        """Return the translated assembly code."""
        return self.lines


def clean(lines: list[str]) -> list[str]:
    """Removes empty lines, full-line comments, and inline comments."""
    return [
        line.split("//")[0].strip()
        for line in lines
        if line.strip() and not line.strip().startswith("//")
    ]


def main():
    base_dir = "files"  # Top-level directory
    if not os.path.isdir(base_dir):
        print(f"Error: '{base_dir}' is not a valid directory.")
        return

    # Process each subdirectory as an independent VM project
    for subdir in sorted(os.listdir(base_dir)):
        subdir_path = os.path.join(base_dir, subdir)
        if os.path.isdir(subdir_path):  # Ensure it's a directory
            vm_files = sorted(glob.glob(os.path.join(subdir_path, "*.vm")))
            if vm_files:
                translator = VMTranslator()
                translator.bootstrap()

                for vm_file in vm_files:
                    with open(vm_file, "r", encoding="utf-8") as f:
                        code = f.readlines()
                        cleaned_code = clean(code)

                    file_name = os.path.splitext(os.path.basename(vm_file))[0]
                    translator.translate_file(file_name, cleaned_code)

                output_path = os.path.join(subdir_path, f"{subdir}.asm")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(translator.get_translated_code()))
                print(f"Created {output_path}")

    # Process each .vm file inside base_dir independently
    for vm_file in sorted(glob.glob(os.path.join(base_dir, "*.vm"))):
        translator = VMTranslator()
        # translator.bootstrap()

        with open(vm_file, "r", encoding="utf-8") as f:
            code = f.readlines()
            cleaned_code = clean(code)

        file_name = os.path.splitext(os.path.basename(vm_file))[0]
        translator.translate_file(file_name, cleaned_code)

        output_filename = os.path.splitext(vm_file)[0] + ".asm"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(translator.get_translated_code()))
        print(f"Created {output_filename}")


if __name__ == "__main__":
    main()
