from io import TextIOWrapper


class VMWriter:
    def __init__(self, output_stream: TextIOWrapper):
        self.output_stream: TextIOWrapper = output_stream

    def write_push(self, segment: str, index: int):
        self.output_stream.write(f"push {segment} {index}\n")

    def write_pop(self, segment: str, index: int):
        self.output_stream.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command: str):
        self.output_stream.write(f"{command}\n")

    def write_label(self, label: str):
        self.output_stream.write(f"label {label}\n")

    def write_goto(self, label: str):
        self.output_stream.write(f"goto {label}\n")

    def write_if(self, label: str):
        self.output_stream.write(f"if-goto {label}\n")

    def write_call(self, name: str, n_args: int):
        self.output_stream.write(f"call {name} {n_args}\n")

    def write_function(self, name: str, n_locals: int):
        self.output_stream.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.output_stream.write("return\n")
