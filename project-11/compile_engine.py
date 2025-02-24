from io import TextIOWrapper
from typing import Optional
from symbol_table import SymbolTable
from tokenizer import Token, TokenType
from vm_writer import VMWriter


class CompileEngine:
    def __init__(self, tokens: list[Token], output_stream: TextIOWrapper):
        self.tokens = iter(tokens)
        self.current_token: Token
        self.class_name = "NO_CLASS_NAME"
        self.symbol_table = SymbolTable()
        self.vm_writer = VMWriter(output_stream)
        self.label_counter: int = 0
        self.compile()

    # -----------------------------------
    # Initialization & Helper Functions
    # -----------------------------------

    @staticmethod
    def kind_to_segment(kind: str):
        mapping = {"static": "static", "field": "this", "argument": "argument", "local": "local"}
        segment = mapping.get(kind)
        if not segment:
            raise ValueError(f"Invalid segment: {segment}")
        return segment

    def advance(self):
        self.current_token = next(self.tokens, None)  # type: ignore

    def expect(
        self,
        expected_type: Optional[TokenType | list[TokenType]] = None,
        expected_value: Optional[str] = None,
    ) -> str:
        """Expect optional token type(s) and optional value. Return the token value."""
        if isinstance(expected_type, list):
            expected_types = expected_type
        elif expected_type:
            expected_types = [expected_type]
        else:
            expected_types = []

        if expected_types and self.current_token.type not in expected_types:
            raise ValueError(
                f"Expected type {expected_types}, got {self.current_token.type} ({self.current_token.value})"
            )

        if expected_value and self.current_token.value != expected_value:
            raise ValueError(f"Expected value {expected_value}, got '{self.current_token.value}'")

        token = self.current_token
        self.advance()
        return token.value

    def generate_label(self, label: str) -> str:
        label = f"{label}_{self.label_counter}"
        self.label_counter += 1
        return label

    # -----------------------------------
    # Entry Point
    # -----------------------------------

    def compile(self):
        self.advance()
        self.compile_class()

    # -----------------------------------
    # Class
    # -----------------------------------

    def compile_class(self):
        self.expect(TokenType.KEYWORD, "class")
        class_name = self.expect(TokenType.IDENTIFIER)
        self.class_name = class_name
        self.expect(TokenType.SYMBOL, "{")

        while self.current_token.value in ("static", "field"):
            self.compile_class_var_dec()

        while self.current_token.value in ("constructor", "function", "method"):
            self.compile_class_subroutine()

        self.expect(TokenType.SYMBOL, "}")

    # -----------------------------------
    # Variable & Parameter Declarations
    # -----------------------------------

    def compile_class_var_dec(self):
        kind = self.expect(TokenType.KEYWORD)  # static or field
        var_type = self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])
        var_name = self.expect(TokenType.IDENTIFIER)

        self.symbol_table.define(var_name, var_type, kind)

        while self.current_token.value == ",":
            self.expect(TokenType.SYMBOL, ",")
            var_name = self.expect(TokenType.IDENTIFIER)
            self.symbol_table.define(var_name, var_type, kind)

        self.expect(TokenType.SYMBOL, ";")

    def compile_var_dec(self):
        self.expect(TokenType.KEYWORD, "var")

        var_type = self.expect(expected_type=[TokenType.KEYWORD, TokenType.IDENTIFIER])
        var_name = self.expect(TokenType.IDENTIFIER)
        self.symbol_table.define(var_name, var_type, "local")

        while self.current_token.value == ",":
            self.expect(TokenType.SYMBOL, ",")
            var_name = self.expect(TokenType.IDENTIFIER)
            self.symbol_table.define(var_name, var_type, "local")

        self.expect(TokenType.SYMBOL, ";")

    def compile_parameter_list(self):
        if self.current_token.value == ")":
            return

        var_type = self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])
        var_name = self.expect(TokenType.IDENTIFIER)
        self.symbol_table.define(var_name, var_type, "argument")

        while self.current_token.value == ",":
            self.expect(TokenType.SYMBOL, ",")
            var_type = self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])
            var_name = self.expect(TokenType.IDENTIFIER)
            self.symbol_table.define(var_name, var_type, "argument")

    # -----------------------------------
    # Subroutine Declarations
    # -----------------------------------

    def compile_class_subroutine(self):
        self.symbol_table.start_subroutine()

        subroutine_type = self.expect(TokenType.KEYWORD)  # constructor, function, method

        if subroutine_type == "method":
            self.symbol_table.define("this", self.class_name, "argument")

        self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])  # return type
        subroutine_name = self.expect(TokenType.IDENTIFIER)  # subroutine name

        self.expect(TokenType.SYMBOL, "(")
        self.compile_parameter_list()
        self.expect(TokenType.SYMBOL, ")")

        self.expect(TokenType.SYMBOL, "{")
        while self.current_token.value == "var":
            self.compile_var_dec()

        nLocals = self.symbol_table.var_count("local")
        self.vm_writer.write_function(f"{self.class_name}.{subroutine_name}", nLocals)

        if subroutine_type == "constructor":
            nFields = self.symbol_table.var_count("field")
            self.vm_writer.write_push("constant", nFields)
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)
        elif subroutine_type == "method":
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)

        self.compile_statements()
        self.expect(TokenType.SYMBOL, "}")

    def compile_subroutine_call(self, identifier: Optional[str] = None):
        """
        Handles subroutine calls in two forms:
        1. subroutineName(expressionList)
        2. (className | varName).subroutineName(expressionList)
        For method calls on objects (when varName is found in the symbol table),
        pushes the object pointer and adjusts the subroutine name to use the object's type.
        """
        identifier = identifier or self.expect(TokenType.IDENTIFIER)
        n_args = 0

        if self.current_token.value == ".":
            self.expect(TokenType.SYMBOL, ".")
            subroutine_name = self.expect(TokenType.IDENTIFIER)
            if self.symbol_table.has(identifier):
                symbol = self.symbol_table.get(identifier)
                self.vm_writer.write_push(self.kind_to_segment(symbol.kind), symbol.index)
                n_args += 1
                callee = f"{symbol.type}.{subroutine_name}"
            else:
                callee = f"{identifier}.{subroutine_name}"
        else:
            self.vm_writer.write_push("pointer", 0)
            n_args += 1
            callee = f"{self.class_name}.{identifier}"

        self.expect(TokenType.SYMBOL, "(")
        n_args += self.compile_expression_list()
        self.expect(TokenType.SYMBOL, ")")
        self.vm_writer.write_call(callee, n_args)

    # -----------------------------------
    # Expression Parsing
    # -----------------------------------

    def compile_expression_list(self) -> int:
        if self.current_token.value == ")":
            return 0
        expression_count = 1
        self.compile_expression()
        while self.current_token.value == ",":
            self.expect(TokenType.SYMBOL, ",")
            self.compile_expression()
            expression_count += 1
        return expression_count

    def compile_expression(self):
        self.compile_term()
        while self.current_token.value in ("+", "-", "*", "/", "&", "|", "<", ">", "="):
            op = self.expect(TokenType.SYMBOL)
            self.compile_term()
            if op == "+":
                self.vm_writer.write_arithmetic("add")
            elif op == "-":
                self.vm_writer.write_arithmetic("sub")
            elif op == "*":
                self.vm_writer.write_call("Math.multiply", 2)
            elif op == "/":
                self.vm_writer.write_call("Math.divide", 2)
            elif op == "&":
                self.vm_writer.write_arithmetic("and")
            elif op == "|":
                self.vm_writer.write_arithmetic("or")
            elif op == "<":
                self.vm_writer.write_arithmetic("lt")
            elif op == ">":
                self.vm_writer.write_arithmetic("gt")
            elif op == "=":
                self.vm_writer.write_arithmetic("eq")

    def compile_term(self):
        if self.current_token.type == TokenType.INTEGER_CONSTANT:
            number = self.expect(TokenType.INTEGER_CONSTANT)
            self.vm_writer.write_push("constant", int(number))
            return

        if self.current_token.type == TokenType.STRING_CONSTANT:
            string = self.expect(TokenType.STRING_CONSTANT)
            self.vm_writer.write_push("constant", len(string))
            self.vm_writer.write_call("String.new", 1)
            for char in string:
                self.vm_writer.write_push("constant", ord(char))
                self.vm_writer.write_call("String.appendChar", 2)
            return

        if self.current_token.type == TokenType.KEYWORD:
            keyword = self.expect(TokenType.KEYWORD)
            if keyword == "true":
                self.vm_writer.write_push("constant", 1)
                self.vm_writer.write_arithmetic("neg")
                return
            if keyword in ("false", "null"):
                self.vm_writer.write_push("constant", 0)
                return
            if keyword == "this":
                self.vm_writer.write_push("pointer", 0)
                return
            return

        if self.current_token.type == TokenType.IDENTIFIER:
            identifier = self.expect(TokenType.IDENTIFIER)
            if self.current_token.value == "[":
                symbol = self.symbol_table.get(identifier)
                self.vm_writer.write_push(self.kind_to_segment(symbol.kind), symbol.index)
                self.expect(TokenType.SYMBOL, "[")
                self.compile_expression()
                self.expect(TokenType.SYMBOL, "]")
                self.vm_writer.write_arithmetic("add")
                self.vm_writer.write_pop("pointer", 1)
                self.vm_writer.write_push("that", 0)
                return
            if self.current_token.value in ("(", "."):
                self.compile_subroutine_call(identifier)
                return
            symbol = self.symbol_table.get(identifier)
            self.vm_writer.write_push(self.kind_to_segment(symbol.kind), symbol.index)
            return

        if self.current_token.value == "(":
            self.expect(TokenType.SYMBOL, "(")
            self.compile_expression()
            self.expect(TokenType.SYMBOL, ")")
            return

        if self.current_token.value in ("-", "~"):
            op = self.expect(TokenType.SYMBOL)
            self.compile_term()
            if op == "-":
                self.vm_writer.write_arithmetic("neg")
            else:
                self.vm_writer.write_arithmetic("not")
            return

        raise Exception(f"Unexpected term: {self.current_token}")

    # -----------------------------------
    # Statement Parsing
    # -----------------------------------

    def compile_statements(self):
        while self.current_token.value in ("let", "if", "while", "do", "return"):
            match self.current_token.value:
                case "let":
                    self.compile_let_statement()
                case "if":
                    self.compile_if_statement()
                case "while":
                    self.compile_while_statement()
                case "do":
                    self.compile_do_statement()
                case "return":
                    self.compile_return_statement()
                case _:
                    raise ValueError(f"Unexpected statement: {self.current_token}")

    def compile_let_statement(self):
        self.expect(TokenType.KEYWORD, "let")
        var_name = self.expect(TokenType.IDENTIFIER)
        is_array = self.current_token.value == "["
        if is_array:
            symbol = self.symbol_table.get(var_name)
            self.vm_writer.write_push(self.kind_to_segment(symbol.kind), symbol.index)
            self.expect(TokenType.SYMBOL, "[")
            self.compile_expression()
            self.expect(TokenType.SYMBOL, "]")
            self.vm_writer.write_arithmetic("add")
        self.expect(TokenType.SYMBOL, "=")
        self.compile_expression()
        self.expect(TokenType.SYMBOL, ";")
        if is_array:
            self.vm_writer.write_pop("temp", 0)
            self.vm_writer.write_pop("pointer", 1)
            self.vm_writer.write_push("temp", 0)
            self.vm_writer.write_pop("that", 0)
        else:
            symbol = self.symbol_table.get(var_name)
            self.vm_writer.write_pop(self.kind_to_segment(symbol.kind), symbol.index)

    def compile_if_statement(self):
        self.expect(TokenType.KEYWORD, "if")
        if_label_start = self.generate_label(f"{self.class_name.upper()}_IF_START")
        if_label_end = self.generate_label(f"{self.class_name.upper()}_IF_END")
        self.expect(TokenType.SYMBOL, "(")
        self.compile_expression()
        self.expect(TokenType.SYMBOL, ")")
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if(if_label_start)
        self.expect(TokenType.SYMBOL, "{")
        self.compile_statements()
        self.expect(TokenType.SYMBOL, "}")
        self.vm_writer.write_goto(if_label_end)
        self.vm_writer.write_label(if_label_start)
        if self.current_token.value == "else":
            self.expect(TokenType.KEYWORD, "else")
            self.expect(TokenType.SYMBOL, "{")
            self.compile_statements()
            self.expect(TokenType.SYMBOL, "}")
        self.vm_writer.write_label(if_label_end)

    def compile_while_statement(self):
        self.expect(TokenType.KEYWORD, "while")
        while_label_start = self.generate_label(f"{self.class_name.upper()}_WHILE_START")
        while_label_end = self.generate_label(f"{self.class_name.upper()}_WHILE_END")
        self.vm_writer.write_label(while_label_start)
        self.expect(TokenType.SYMBOL, "(")
        self.compile_expression()
        self.expect(TokenType.SYMBOL, ")")
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if(while_label_end)
        self.expect(TokenType.SYMBOL, "{")
        self.compile_statements()
        self.expect(TokenType.SYMBOL, "}")
        self.vm_writer.write_goto(while_label_start)
        self.vm_writer.write_label(while_label_end)

    def compile_do_statement(self):
        self.expect(TokenType.KEYWORD, "do")
        self.compile_subroutine_call()
        self.expect(TokenType.SYMBOL, ";")
        self.vm_writer.write_pop("temp", 0)

    def compile_return_statement(self):
        self.expect(TokenType.KEYWORD, "return")
        if self.current_token.value == ";":
            self.vm_writer.write_push("constant", 0)
        else:
            self.compile_expression()
        self.expect(TokenType.SYMBOL, ";")
        self.vm_writer.write_return()
