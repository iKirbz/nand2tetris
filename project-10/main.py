import glob
import os
from tokenizer import Token, tokenize


def main():
    base_dir = "files"
    if not os.path.isdir(base_dir):
        raise Exception(f"Error: '{base_dir}' is not a valid directory.")

    for subdir in sorted(os.listdir(base_dir)):
        subdir_path = os.path.join(base_dir, subdir)

        for jack_file in sorted(glob.glob(os.path.join(subdir_path, "*.jack"))):
            tokens = tokenize(jack_file)
            output_filename = os.path.splitext(jack_file)[0] + "T.xml"
            write_tokens_xml(output_filename, tokens)


def write_tokens_xml(output_filename: str, tokens: list[Token]):
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("<tokens>\n")
        for token in tokens:
            value = token.value

            if value == "<":
                value = "&lt;"
            elif value == ">":
                value = "&gt;"
            elif value == '"':
                value = "&quot;"
            elif value == "&":
                value = "&amp;"

            f.write(
                f"\t<{token.type.value}> {value} </{token.type.value}>\n",
            )
        f.write("</tokens>")
        print(f"Created {output_filename}")


if __name__ == "__main__":
    main()
