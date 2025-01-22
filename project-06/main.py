from assembler import assemble

if __name__ == "__main__":
    file_name = "files/pong"

    machine_code = assemble(file_name + ".asm")

    with open(file_name + ".hack", "r") as file:
        hack_machine_code = file.readlines()

    cleaned_hack_machine_code = [line.strip() for line in hack_machine_code]

    error_found = False

    for mine, theirs in zip(machine_code, cleaned_hack_machine_code):
        if mine != theirs:
            error_found = True

    print("Error found" if error_found else "No errors found!")
