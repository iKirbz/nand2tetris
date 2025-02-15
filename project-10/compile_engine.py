from dataclasses import dataclass, field
from typing import Optional
from tokenizer import Token, TokenType


@dataclass
class AST:
    value: Optional[str | Token] = None
    children: list["AST"] = field(default_factory=list)

    def add(self, child: "AST"):
        self.children.append(child)

    def extend(self, child: list["AST"]):
        self.children.extend(child)


class CompileEngine:
    def __init__(self, tokens: list[Token]):
        self.tokens = iter(tokens)
        self.current_token: Token
        self.advance()

    # -----------------------------------
    # Entry point for compilation
    # -----------------------------------

    def generate_ast(self) -> AST:
        return self.compile_class()

    # -----------------------------------
    # Initialization & Helper Functions
    # -----------------------------------

    def advance(self):
        """Move to the next token, handling end of input."""
        self.current_token = next(self.tokens, None) # type: ignore
    def expect(
        self,
        expected_type: Optional[TokenType | list[TokenType]] = None,
        expected_value: Optional[str] = None,
    ) -> Token:
        """Expect a token of a specific type (or multiple types) and optionally a specific value.

        If no expected_type is provided, any token type is accepted.
        If no expected_value is provided, any token value is accepted.
        """

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
        return token

    # -----------------------------------
    # Class
    # -----------------------------------

    def compile_class(self) -> AST:
        """Compiles an entire class."""
        root = AST("class")

        root.add(AST(self.expect(TokenType.KEYWORD, "class")))
        root.add(AST(self.expect(TokenType.IDENTIFIER)))  # class name e.g. Main
        root.add(AST(self.expect(TokenType.SYMBOL, "{")))

        while self.current_token.value in {"static", "field"}:
            root.add(self.compile_class_var_dec())

        while self.current_token.value in {"constructor", "function", "method"}:
            root.add(self.compile_class_subroutine_dec())

        root.add(AST(self.expect(TokenType.SYMBOL, "}")))

        return root

    # -----------------------------------
    # Variable & Parameter Declarations
    # -----------------------------------

    def compile_class_var_dec(self) -> AST:
        """Compiles a static or field variable declaration."""

        var_dec = AST("classVarDec")
        var_dec.add(AST(self.expect(TokenType.KEYWORD)))  # static/field
        var_dec.add(AST(self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])))  # type
        var_dec.add(AST(self.expect(TokenType.IDENTIFIER)))  # variable name

        while self.current_token.value == ",":
            var_dec.add(AST(self.expect(TokenType.SYMBOL, ",")))
            var_dec.add(AST(self.expect(TokenType.IDENTIFIER)))

        var_dec.add(AST(self.expect(TokenType.SYMBOL, ";")))

        return var_dec

    def compile_var_dec(self) -> AST:
        """Compiles a local variable declaration."""

        var_dec = AST("varDec")
        var_dec.add(AST(self.expect(TokenType.KEYWORD, "var")))
        var_dec.add(AST(self.expect(expected_type=[TokenType.KEYWORD, TokenType.IDENTIFIER])))  # type
        var_dec.add(AST(self.expect(TokenType.IDENTIFIER)))  # varName

        while self.current_token.value == ",":
            var_dec.add(AST(self.expect(TokenType.SYMBOL, ",")))
            var_dec.add(AST(self.expect(TokenType.IDENTIFIER)))  # varName

        var_dec.add(AST(self.expect(TokenType.SYMBOL, ";")))
        
        return var_dec

    def compile_parameter_list(self) -> AST:
        """Compiles a parameter list for a function."""

        parameters = AST("parameterList")
        if self.current_token.value == ")":
            return parameters  # No parameters
        
        parameters.add(AST(self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])))  # type
        parameters.add(AST(self.expect(TokenType.IDENTIFIER)))  # varName

        while self.current_token.value == ",":
            parameters.add(AST(self.expect(TokenType.SYMBOL, ",")))
            parameters.add(AST(self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])))  # type
            parameters.add(AST(self.expect(TokenType.IDENTIFIER)))  # varName

        return parameters

    # -----------------------------------
    # Subroutine Declarations
    # -----------------------------------

    def compile_class_subroutine_dec(self) -> AST:
        """Compiles a constructor, function, or method declaration."""

        subroutine = AST("subroutineDec")
        subroutine.add(AST(self.expect(TokenType.KEYWORD)))  # constructor, function, method
        subroutine.add(AST(self.expect([TokenType.IDENTIFIER, TokenType.KEYWORD])))  # return type or class
        subroutine.add(AST(self.expect(TokenType.IDENTIFIER)))  # subroutine name or new
        subroutine.add(AST(self.expect(TokenType.SYMBOL, "(")))
        subroutine.add(self.compile_parameter_list())
        subroutine.add(AST(self.expect(TokenType.SYMBOL, ")")))
        subroutine.add(self.compile_subroutine_body())

        return subroutine

    def compile_subroutine_call(self, identifier=None) -> list[AST]:
        """Compiles a subroutine call without wrapping it in an XML tag."""

        nodes = []

        if not identifier:
            nodes.append(AST(self.expect(TokenType.IDENTIFIER)))
        else:
            nodes.append(identifier)

        if self.current_token.value == ".":
            nodes.append(AST(self.expect(TokenType.SYMBOL, ".")))
            nodes.append(AST(self.expect(TokenType.IDENTIFIER)))

        nodes.append(AST(self.expect(TokenType.SYMBOL, "(")))
        nodes.append(self.compile_expression_list())
        nodes.append(AST(self.expect(TokenType.SYMBOL, ")")))

        return nodes

    def compile_subroutine_body(self) -> AST:
        """Compiles the body of a subroutine."""

        body = AST("subroutineBody")
        body.add(AST(self.expect(TokenType.SYMBOL, "{")))

        while self.current_token.value == "var":
            body.add(self.compile_var_dec())

        body.add(self.compile_statements())
        body.add(AST(self.expect(TokenType.SYMBOL, "}")))

        return body

    # -----------------------------------
    # Expression Parsing
    # -----------------------------------

    def compile_term(self) -> AST:
        """Compiles a term (single unit in an expression)."""
        token = self.current_token
        term = AST("term")

        if token.type in {TokenType.INTEGER_CONSTANT, TokenType.STRING_CONSTANT, TokenType.KEYWORD}:
            term.add(AST(self.expect()))
            return term

        if token.type == TokenType.IDENTIFIER:
            identifier = AST(self.expect(TokenType.IDENTIFIER))

            if self.current_token.value == "[":
                term.add(identifier)
                term.add(AST(self.expect(TokenType.SYMBOL, "[")))
                term.add(self.compile_expression())
                term.add(AST(self.expect(TokenType.SYMBOL, "]")))
                return term

            if self.current_token.value in {"(", "."}:
                term.extend(self.compile_subroutine_call(identifier))
                return term

            term.add(identifier)
            return term

        if token.value == "(":
            term.add(AST(self.expect(TokenType.SYMBOL, "(")))
            term.add(self.compile_expression())
            term.add(AST(self.expect(TokenType.SYMBOL, ")")))
            return term

        if token.value in {"-", "~"}:
            term.add(AST(self.expect(TokenType.SYMBOL)))
            term.add(self.compile_term())
            return term

        raise Exception(f"Unexpected term: {token}")

    def compile_expression(self) -> AST:
        """Compiles an expression."""
        expression = AST("expression")
        expression.add(self.compile_term())
        while self.current_token.value in {"+", "-", "*", "/", "&", "|", "<", ">", "="}:
            expression.add(AST(self.expect(TokenType.SYMBOL)))
            expression.add(self.compile_term())
        return expression

    def compile_expression_list(self) -> AST:
        """Compiles a list of expressions (possibly empty)."""

        expr_list = AST("expressionList")

        if self.current_token.value == ")":
            return expr_list
        
        expr_list.add(self.compile_expression())

        while self.current_token.value == ",":
            expr_list.add(AST(self.expect(TokenType.SYMBOL, ",")))
            expr_list.add(self.compile_expression())

        return expr_list

    # -----------------------------------
    # Statement Parsing
    # -----------------------------------

    def compile_let_statement(self) -> AST:
        """Compiles a let statement."""

        let_stmt = AST("letStatement")
        let_stmt.add(AST(self.expect(TokenType.KEYWORD, "let")))
        let_stmt.add(AST(self.expect(TokenType.IDENTIFIER)))  # varName

        if self.current_token.value == "[":
            let_stmt.add(AST(self.expect(TokenType.SYMBOL, "[")))
            let_stmt.add(self.compile_expression())
            let_stmt.add(AST(self.expect(TokenType.SYMBOL, "]")))

        let_stmt.add(AST(self.expect(TokenType.SYMBOL, "=")))
        let_stmt.add(self.compile_expression())
        let_stmt.add(AST(self.expect(TokenType.SYMBOL, ";")))

        return let_stmt

    def compile_if_statement(self) -> AST:
        """Compiles an if statement."""

        if_stmt = AST("ifStatement")
        if_stmt.add(AST(self.expect(TokenType.KEYWORD, "if")))
        if_stmt.add(AST(self.expect(TokenType.SYMBOL, "(")))
        if_stmt.add(self.compile_expression())
        if_stmt.add(AST(self.expect(TokenType.SYMBOL, ")")))
        if_stmt.add(AST(self.expect(TokenType.SYMBOL, "{")))
        if_stmt.add(self.compile_statements())
        if_stmt.add(AST(self.expect(TokenType.SYMBOL, "}")))

        if self.current_token.value == "else":
            if_stmt.add(AST(self.expect(TokenType.KEYWORD, "else")))
            if_stmt.add(AST(self.expect(TokenType.SYMBOL, "{")))
            if_stmt.add(self.compile_statements())
            if_stmt.add(AST(self.expect(TokenType.SYMBOL, "}")))

        return if_stmt

    def compile_while_statement(self) -> AST:
        """Compiles a while statement."""

        while_stmt = AST("whileStatement")
        while_stmt.add(AST(self.expect(TokenType.KEYWORD, "while")))
        while_stmt.add(AST(self.expect(TokenType.SYMBOL, "(")))
        while_stmt.add(self.compile_expression())
        while_stmt.add(AST(self.expect(TokenType.SYMBOL, ")")))
        while_stmt.add(AST(self.expect(TokenType.SYMBOL, "{")))
        while_stmt.add(self.compile_statements())
        while_stmt.add(AST(self.expect(TokenType.SYMBOL, "}")))

        return while_stmt

    def compile_do_statement(self) -> AST:
        """Compiles a do statement."""

        do_stmt = AST("doStatement")
        do_stmt.add(AST(self.expect(TokenType.KEYWORD, "do")))
        do_stmt.extend(self.compile_subroutine_call())
        do_stmt.add(AST(self.expect(TokenType.SYMBOL, ";")))
        
        return do_stmt

    def compile_return_statement(self) -> AST:
        """Compiles a return statement."""
        return_stmt = AST("returnStatement")
        return_stmt.add(AST(self.expect(TokenType.KEYWORD, "return")))

        if self.current_token.value != ";":
            return_stmt.add(self.compile_expression())

        return_stmt.add(AST(self.expect(TokenType.SYMBOL, ";")))

        return return_stmt

    def compile_statements(self) -> AST:
        """Compiles a sequence of statements."""

        statements = AST("statements")

        while self.current_token.value in {"let", "if", "while", "do", "return"}:
            match self.current_token.value:
                case "let":
                    statements.add(self.compile_let_statement())
                case "if":
                    statements.add(self.compile_if_statement())
                case "while":
                    statements.add(self.compile_while_statement())
                case "do":
                    statements.add(self.compile_do_statement())
                case "return":
                    statements.add(self.compile_return_statement())

        return statements
