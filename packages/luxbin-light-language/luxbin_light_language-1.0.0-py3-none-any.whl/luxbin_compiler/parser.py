"""
LUXBIN Parser

Recursive descent parser that builds an Abstract Syntax Tree from tokens.
Follows the EBNF grammar defined in LUXBIN_LIGHT_LANGUAGE_SPEC.md.
"""

from typing import List, Optional, Set
from .lexer import Token, TokenType
from .ast_nodes import *
from .errors import ParserError, SourceLocation


class Parser:
    """
    LUXBIN Recursive Descent Parser.

    Grammar overview:
        program        = { statement }
        statement      = declaration | assignment | conditional | loop |
                        function_def | return_stmt | expression
        expression     = or_expr
        or_expr        = and_expr { "or" and_expr }
        and_expr       = equality { "and" equality }
        equality       = comparison { ("==" | "!=") comparison }
        comparison     = addition { ("<" | ">" | "<=" | ">=") addition }
        addition       = multiplication { ("+" | "-") multiplication }
        multiplication = power { ("*" | "/" | "%") power }
        power          = unary { "^" unary }
        unary          = ("not" | "-") unary | call
        call           = primary { "(" args ")" | "[" index "]" }
        primary        = NUMBER | STRING | BOOLEAN | NIL | IDENTIFIER | "(" expression ")" | array
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token: Token = tokens[0] if tokens else Token(
            TokenType.EOF, '', 700.0, SourceLocation(1, 1)
        )

    def error(self, message: str) -> ParserError:
        """Create a parser error at current location."""
        return ParserError(message, self.current_token.location)

    def advance(self) -> Token:
        """Move to next token and return the previous one."""
        token = self.current_token
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        return token

    def peek(self, offset: int = 0) -> Token:
        """Peek at a token without advancing."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # Return EOF

    def check(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token.type in types

    def check_keyword(self, *keywords: str) -> bool:
        """Check if current token is a keyword matching any of the given values."""
        return (self.current_token.type == TokenType.KEYWORD and
                self.current_token.value in keywords)

    def match(self, *types: TokenType) -> Optional[Token]:
        """If current token matches, advance and return it."""
        if self.check(*types):
            return self.advance()
        return None

    def match_keyword(self, *keywords: str) -> Optional[Token]:
        """If current token is a matching keyword, advance and return it."""
        if self.check_keyword(*keywords):
            return self.advance()
        return None

    def expect(self, token_type: TokenType, message: str = None) -> Token:
        """Expect current token to be of given type, raise error otherwise."""
        if self.current_token.type != token_type:
            msg = message or f"Expected {token_type.name}, got {self.current_token.type.name}"
            raise self.error(msg)
        return self.advance()

    def expect_keyword(self, keyword: str, message: str = None) -> Token:
        """Expect current token to be a specific keyword."""
        if not self.check_keyword(keyword):
            msg = message or f"Expected '{keyword}', got '{self.current_token.value}'"
            raise self.error(msg)
        return self.advance()

    def skip_newlines(self):
        """Skip any newline tokens."""
        while self.check(TokenType.NEWLINE):
            self.advance()

    # ========================================================================
    # Parser Entry Point
    # ========================================================================

    def parse(self) -> Program:
        """Parse entire program."""
        statements = []
        self.skip_newlines()

        while not self.check(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        return Program(statements=statements)

    # ========================================================================
    # Statements
    # ========================================================================

    def parse_statement(self) -> Optional[Statement]:
        """Parse a single statement."""
        self.skip_newlines()

        if self.check(TokenType.EOF):
            return None

        # Declaration: let x = ... or const x = ...
        if self.check_keyword('let', 'const'):
            return self.parse_declaration()

        # Function definition: func name(...)
        if self.check_keyword('func'):
            return self.parse_function_def()

        # If statement: if ... then ... end
        if self.check_keyword('if'):
            return self.parse_if_statement()

        # While loop: while ... do ... end
        if self.check_keyword('while'):
            return self.parse_while_statement()

        # For loop: for x in ... do ... end
        if self.check_keyword('for'):
            return self.parse_for_statement()

        # Return statement: return ...
        if self.check_keyword('return'):
            return self.parse_return_statement()

        # Break statement
        if self.check_keyword('break'):
            loc = self.current_token.location
            self.advance()
            return BreakStatement(location=loc)

        # Continue statement
        if self.check_keyword('continue'):
            loc = self.current_token.location
            self.advance()
            return ContinueStatement(location=loc)

        # Quantum block: quantum ... end
        if self.check_keyword('quantum'):
            return self.parse_quantum_block()

        # Import statement: import module
        if self.check_keyword('import'):
            return self.parse_import_statement()

        # Export statement: export name
        if self.check_keyword('export'):
            return self.parse_export_statement()

        # Assignment or expression statement
        return self.parse_assignment_or_expression()

    def parse_declaration(self) -> Declaration:
        """Parse variable declaration: let x = expr or const x = expr"""
        token = self.advance()  # consume 'let' or 'const'
        is_const = token.value == 'const'

        name_token = self.expect(TokenType.IDENTIFIER, "Expected variable name")
        self.expect(TokenType.ASSIGN, "Expected '=' in declaration")
        value = self.parse_expression()

        return Declaration(
            name=name_token.value,
            value=value,
            is_const=is_const,
            location=token.location
        )

    def parse_function_def(self) -> FunctionDef:
        """Parse function definition: func name(params) ... end"""
        token = self.expect_keyword('func')
        name_token = self.expect(TokenType.IDENTIFIER, "Expected function name")

        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parse_parameters()
        self.expect(TokenType.RPAREN, "Expected ')' after parameters")

        self.skip_newlines()
        body = self.parse_block('end')
        self.expect_keyword('end', "Expected 'end' after function body")

        return FunctionDef(
            name=name_token.value,
            params=params,
            body=body,
            location=token.location
        )

    def parse_parameters(self) -> List[str]:
        """Parse function parameters."""
        params = []
        if self.check(TokenType.IDENTIFIER):
            params.append(self.advance().value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
        return params

    def parse_if_statement(self) -> IfStatement:
        """Parse if statement: if condition then ... [else ...] end"""
        token = self.expect_keyword('if')
        condition = self.parse_expression()
        self.expect_keyword('then', "Expected 'then' after if condition")

        self.skip_newlines()
        then_body = self.parse_block('else', 'end')

        else_body = None
        if self.check_keyword('else'):
            self.advance()
            self.skip_newlines()
            else_body = self.parse_block('end')

        self.expect_keyword('end', "Expected 'end' after if statement")

        return IfStatement(
            condition=condition,
            then_body=then_body,
            else_body=else_body,
            location=token.location
        )

    def parse_while_statement(self) -> WhileStatement:
        """Parse while loop: while condition do ... end"""
        token = self.expect_keyword('while')
        condition = self.parse_expression()
        self.expect_keyword('do', "Expected 'do' after while condition")

        self.skip_newlines()
        body = self.parse_block('end')
        self.expect_keyword('end', "Expected 'end' after while loop")

        return WhileStatement(
            condition=condition,
            body=body,
            location=token.location
        )

    def parse_for_statement(self) -> ForStatement:
        """Parse for loop: for var in iterable do ... end"""
        token = self.expect_keyword('for')
        var_token = self.expect(TokenType.IDENTIFIER, "Expected loop variable")
        self.expect_keyword('in', "Expected 'in' in for loop")
        iterable = self.parse_expression()
        self.expect_keyword('do', "Expected 'do' after for loop header")

        self.skip_newlines()
        body = self.parse_block('end')
        self.expect_keyword('end', "Expected 'end' after for loop")

        return ForStatement(
            variable=var_token.value,
            iterable=iterable,
            body=body,
            location=token.location
        )

    def parse_return_statement(self) -> ReturnStatement:
        """Parse return statement: return [expression]"""
        token = self.expect_keyword('return')

        # Check if there's an expression to return
        value = None
        if not self.check(TokenType.NEWLINE, TokenType.EOF) and not self.check_keyword('end'):
            value = self.parse_expression()

        return ReturnStatement(value=value, location=token.location)

    def parse_quantum_block(self) -> QuantumBlock:
        """Parse quantum block: quantum ... end"""
        token = self.expect_keyword('quantum')
        self.skip_newlines()
        body = self.parse_block('end')
        self.expect_keyword('end', "Expected 'end' after quantum block")

        return QuantumBlock(body=body, location=token.location)

    def parse_import_statement(self) -> ImportStatement:
        """Parse import statement: import module [as alias]"""
        token = self.expect_keyword('import')
        module_token = self.expect(TokenType.IDENTIFIER, "Expected module name")

        alias = None
        if self.check_keyword('as'):
            self.advance()
            alias = self.expect(TokenType.IDENTIFIER, "Expected alias name").value

        return ImportStatement(
            module=module_token.value,
            alias=alias,
            location=token.location
        )

    def parse_export_statement(self) -> ExportStatement:
        """Parse export statement: export name"""
        token = self.expect_keyword('export')
        name_token = self.expect(TokenType.IDENTIFIER, "Expected name to export")

        return ExportStatement(name=name_token.value, location=token.location)

    def parse_assignment_or_expression(self) -> Statement:
        """Parse assignment or expression statement."""
        loc = self.current_token.location
        expr = self.parse_expression()

        # Check for assignment
        if self.match(TokenType.ASSIGN):
            if isinstance(expr, Identifier):
                value = self.parse_expression()
                return Assignment(target=expr.name, value=value, location=loc)
            elif isinstance(expr, IndexExpression):
                value = self.parse_expression()
                return Assignment(target=expr, value=value, location=loc)
            else:
                raise self.error("Invalid assignment target")

        return ExpressionStatement(expression=expr, location=loc)

    def parse_block(self, *terminators: str) -> List[Statement]:
        """Parse a block of statements until a terminator keyword."""
        statements = []
        self.skip_newlines()

        while not self.check(TokenType.EOF) and not self.check_keyword(*terminators):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        return statements

    # ========================================================================
    # Expressions (Operator Precedence)
    # ========================================================================

    def parse_expression(self) -> Expression:
        """Parse an expression (entry point)."""
        return self.parse_or()

    def parse_or(self) -> Expression:
        """Parse logical OR: and_expr { "or" and_expr }"""
        left = self.parse_and()

        while self.check_keyword('or'):
            op = self.advance().value
            right = self.parse_and()
            left = BinaryOp(operator=op, left=left, right=right, location=left.location)

        return left

    def parse_and(self) -> Expression:
        """Parse logical AND: equality { "and" equality }"""
        left = self.parse_equality()

        while self.check_keyword('and'):
            op = self.advance().value
            right = self.parse_equality()
            left = BinaryOp(operator=op, left=left, right=right, location=left.location)

        return left

    def parse_equality(self) -> Expression:
        """Parse equality: comparison { ("==" | "!=") comparison }"""
        left = self.parse_comparison()

        while self.check(TokenType.EQ, TokenType.NE):
            op = self.advance().value
            right = self.parse_comparison()
            left = BinaryOp(operator=op, left=left, right=right, location=left.location)

        return left

    def parse_comparison(self) -> Expression:
        """Parse comparison: addition { ("<" | ">" | "<=" | ">=") addition }"""
        left = self.parse_addition()

        while self.check(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op = self.advance().value
            right = self.parse_addition()
            left = BinaryOp(operator=op, left=left, right=right, location=left.location)

        return left

    def parse_addition(self) -> Expression:
        """Parse addition: multiplication { ("+" | "-") multiplication }"""
        left = self.parse_multiplication()

        while self.check(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplication()
            left = BinaryOp(operator=op, left=left, right=right, location=left.location)

        return left

    def parse_multiplication(self) -> Expression:
        """Parse multiplication: power { ("*" | "/" | "%") power }"""
        left = self.parse_power()

        while self.check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance().value
            right = self.parse_power()
            left = BinaryOp(operator=op, left=left, right=right, location=left.location)

        return left

    def parse_power(self) -> Expression:
        """Parse power: unary { "^" unary }"""
        left = self.parse_unary()

        while self.check(TokenType.CARET):
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOp(operator=op, left=left, right=right, location=left.location)

        return left

    def parse_unary(self) -> Expression:
        """Parse unary: ("not" | "-") unary | call"""
        loc = self.current_token.location

        if self.check_keyword('not'):
            op = self.advance().value
            operand = self.parse_unary()
            return UnaryOp(operator=op, operand=operand, location=loc)

        if self.check(TokenType.MINUS):
            op = self.advance().value
            operand = self.parse_unary()
            return UnaryOp(operator=op, operand=operand, location=loc)

        return self.parse_call()

    def parse_call(self) -> Expression:
        """Parse call and index: primary { "(" args ")" | "[" index "]" }"""
        expr = self.parse_primary()

        while True:
            if self.check(TokenType.LPAREN):
                self.advance()
                args = self.parse_arguments()
                self.expect(TokenType.RPAREN, "Expected ')' after arguments")

                # Get function name if it's an identifier
                func_name = expr.name if isinstance(expr, Identifier) else expr
                expr = CallExpression(
                    function=func_name,
                    arguments=args,
                    location=expr.location
                )

            elif self.check(TokenType.LBRACKET):
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexExpression(array=expr, index=index, location=expr.location)

            elif self.check(TokenType.DOT):
                self.advance()
                member = self.expect(TokenType.IDENTIFIER, "Expected member name").value
                expr = MemberExpression(object=expr, member=member, location=expr.location)

            else:
                break

        return expr

    def parse_arguments(self) -> List[Expression]:
        """Parse function call arguments."""
        args = []
        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                args.append(self.parse_expression())
        return args

    def parse_primary(self) -> Expression:
        """Parse primary expression."""
        loc = self.current_token.location

        # Integer literal
        if self.check(TokenType.INTEGER):
            token = self.advance()
            return IntegerLiteral(value=int(token.value), location=loc)

        # Float literal
        if self.check(TokenType.FLOAT):
            token = self.advance()
            return FloatLiteral(value=float(token.value), location=loc)

        # String literal
        if self.check(TokenType.STRING):
            token = self.advance()
            return StringLiteral(value=token.value, location=loc)

        # Boolean literal
        if self.check(TokenType.BOOLEAN):
            token = self.advance()
            return BooleanLiteral(value=(token.value == 'true'), location=loc)

        # Nil literal
        if self.check(TokenType.NIL):
            self.advance()
            return NilLiteral(location=loc)

        # Array literal
        if self.check(TokenType.LBRACKET):
            return self.parse_array_literal()

        # Parenthesized expression
        if self.check(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        # Quantum expressions
        if self.check_keyword('superpose', 'measure', 'entangle'):
            return self.parse_quantum_expression()

        # Identifier
        if self.check(TokenType.IDENTIFIER):
            token = self.advance()
            return Identifier(name=token.value, location=loc)

        raise self.error(f"Unexpected token: {self.current_token.value!r}")

    def parse_array_literal(self) -> ArrayLiteral:
        """Parse array literal: [expr, expr, ...]"""
        loc = self.current_token.location
        self.expect(TokenType.LBRACKET)

        elements = []
        if not self.check(TokenType.RBRACKET):
            elements.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                elements.append(self.parse_expression())

        self.expect(TokenType.RBRACKET, "Expected ']' after array elements")

        return ArrayLiteral(elements=elements, location=loc)

    def parse_quantum_expression(self) -> QuantumExpression:
        """Parse quantum operation: superpose(...), measure(...), entangle(...)"""
        loc = self.current_token.location
        operation = self.advance().value

        self.expect(TokenType.LPAREN, f"Expected '(' after '{operation}'")
        args = self.parse_arguments()
        self.expect(TokenType.RPAREN, f"Expected ')' after {operation} arguments")

        return QuantumExpression(operation=operation, arguments=args, location=loc)
