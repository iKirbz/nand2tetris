import glob
import os
from compile_engine import CompileEngine, AST
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
            print(f"Created {output_filename}")

            ast = CompileEngine(tokens).generate_ast()
            output_filename = os.path.splitext(jack_file)[0] + ".xml"
            with open(output_filename, "w", encoding="utf-8") as file:
                write_ast_as_xml(ast, file)
            print(f"Created {output_filename}")


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


def write_ast_as_xml(node: AST, file, level: int = 0):
    """Recursively writes the AST as an XML-like structure to a file."""
    indent = "  " * level  # Indentation for readability

    # If it's a token, write it as an XML tag with content
    if isinstance(node.value, Token):
        token_type = node.value.type.value  # Convert Enum to string
        token_value = node.value.value

        if token_value == "<":
            token_value = "&lt;"
        elif token_value == ">":
            token_value = "&gt;"
        elif token_value == '"':
            token_value = "&quot;"
        elif token_value == "&":
            token_value = "&amp;"

        file.write(f"{indent}<{token_type}> {token_value} </{token_type}>\n")

    elif isinstance(node.value, str):  # If it's a non-terminal node
        file.write(f"{indent}<{node.value}>\n")
        for child in node.children:
            write_ast_as_xml(child, file, level + 1)  # Recursively write children
        file.write(f"{indent}</{node.value}>\n")  # Closing tag


if __name__ == "__main__":
    main()
