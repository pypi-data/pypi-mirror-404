#!/usr/bin/env python3
"""
hypnotIC - I see what you meant.

A programming language that doesn't scream at you.
"""

import sys
import re
import random
import operator

# =============================================================================
# LEXER - Break code into tokens
# =============================================================================

KEYWORDS = {
    # Control flow
    '?': 'IF',
    'Ls': 'ELSE',
    'file': 'ELIF',
    'IC': 'END',
    '4': 'FOR',
    'wyl': 'WHILE',
    '-->': 'CONTINUE',
    # Note: 'x' for BREAK is handled by parser, not lexer (allows variable names like 'x')
    # Note: 'n' for IN is handled specially in read_identifier()

    # Functions
    'fun': 'FUNCTION',
    're:': 'RETURN',

    # Boolean
    't': 'TRUE',
    'f': 'FALSE',

    # Null
    'N^0': 'NULL',

    # Operators
    'iz': 'EQ',
    'aint': 'NEQ',
    'or': 'OR',
    'RHO': 'OR',
    'mold': 'MOD',

    # Error handling
    'hard': 'TRY',
    'C': 'CATCH',

    # Special
    'ego': 'SELF',
    'rayz': 'ARRAY',
    'up': 'APPEND',
    '!!!': 'POP',
}

class Token:
    def __init__(self, type_, value, line=0):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r})'


class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.line = 1
        self.tokens = []

    def error(self, msg):
        print(f"IC sees a problem on line {self.line}: {msg}")
        sys.exit(1)

    def peek(self, n=1):
        return self.code[self.pos:self.pos + n]

    def advance(self, n=1):
        for _ in range(n):
            if self.pos < len(self.code):
                if self.code[self.pos] == '\n':
                    self.line += 1
                self.pos += 1

    def skip_whitespace(self):
        while self.pos < len(self.code) and self.code[self.pos] in ' \t':
            self.advance()

    def skip_comment(self):
        # fuck this is a comment
        if self.peek(4) == 'fuck':
            while self.pos < len(self.code) and self.code[self.pos] != '\n':
                self.advance()

    def read_string(self):
        quote = self.code[self.pos]
        self.advance()
        result = ''
        while self.pos < len(self.code) and self.code[self.pos] != quote:
            if self.code[self.pos] == '\\' and self.pos + 1 < len(self.code):
                self.advance()
                escape = self.code[self.pos]
                if escape == 'n':
                    result += '\n'
                elif escape == 't':
                    result += '\t'
                else:
                    result += escape
            else:
                result += self.code[self.pos]
            self.advance()
        self.advance()  # closing quote
        return Token('STRING', result, self.line)

    def read_number(self):
        result = ''
        has_dot = False
        while self.pos < len(self.code) and (self.code[self.pos].isdigit() or self.code[self.pos] == '.'):
            if self.code[self.pos] == '.':
                if has_dot:
                    break
                has_dot = True
            result += self.code[self.pos]
            self.advance()
        if has_dot:
            return Token('FLOAT', float(result), self.line)
        return Token('INT', int(result), self.line)

    def read_identifier(self):
        result = ''
        while self.pos < len(self.code) and (self.code[self.pos].isalnum() or self.code[self.pos] in '_'):
            result += self.code[self.pos]
            self.advance()

        # Check for special multi-char tokens
        if result == 'N' and self.peek(2) == '^0':
            self.advance(2)
            return Token('NULL', None, self.line)

        # Multi-letter keywords first
        if result in KEYWORDS:
            return Token(KEYWORDS[result], result, self.line)

        # Single letter keywords - only 'n' for 'in' needs special handling
        # 'x', 't', 'f' are returned as IDENT and handled by parser contextually
        if result == 'n' and len(result) == 1:
            return Token('IN', 'n', self.line)

        # Check if it starts with capital (could be a class)
        if result and result[0].isupper():
            return Token('CLASSNAME', result, self.line)

        return Token('IDENT', result, self.line)

    def tokenize(self):
        while self.pos < len(self.code):
            # Skip whitespace
            if self.code[self.pos] in ' \t':
                self.skip_whitespace()
                continue

            # Newlines are significant
            if self.code[self.pos] == '\n':
                self.tokens.append(Token('NEWLINE', '\n', self.line))
                self.advance()
                continue

            # Comments (fuck this line)
            if self.peek(4) == 'fuck':
                self.skip_comment()
                continue

            # Multi-char operators first
            if self.peek(3) == '-->':
                self.tokens.append(Token('CONTINUE', '-->', self.line))
                self.advance(3)
                continue

            if self.peek(3) == '!!!':
                self.tokens.append(Token('POP', '!!!', self.line))
                self.advance(3)
                continue

            if self.peek(2) == '->':
                self.tokens.append(Token('IMPORT', '->', self.line))
                self.advance(2)
                continue

            if self.peek(2) == '+>':
                self.tokens.append(Token('APPEND', '+>', self.line))
                self.advance(2)
                continue

            if self.peek(2) == '<-':
                self.tokens.append(Token('ARROW_LEFT', '<-', self.line))
                self.advance(2)
                continue

            if self.peek(2) == '>=':
                self.tokens.append(Token('GTE', '>=', self.line))
                self.advance(2)
                continue

            if self.peek(2) == '<=':
                self.tokens.append(Token('LTE', '<=', self.line))
                self.advance(2)
                continue

            if self.peek(2) == 're':
                if self.peek(3) == 're:':
                    self.tokens.append(Token('RETURN', 're:', self.line))
                    self.advance(3)
                    continue

            if self.peek(2) == 'PV':
                self.tokens.append(Token('INPUT', 'PV', self.line))
                self.advance(2)
                continue

            if self.peek(2) == 'IC':
                self.tokens.append(Token('END', 'IC', self.line))
                self.advance(2)
                continue

            if self.peek(2) == 'Ls':
                self.tokens.append(Token('ELSE', 'Ls', self.line))
                self.advance(2)
                continue

            if self.peek(3) == 'wyl':
                self.tokens.append(Token('WHILE', 'wyl', self.line))
                self.advance(3)
                continue

            if self.peek(3) == 'fun':
                self.tokens.append(Token('FUNCTION', 'fun', self.line))
                self.advance(3)
                continue

            if self.peek(4) == 'file':
                self.tokens.append(Token('ELIF', 'file', self.line))
                self.advance(4)
                continue

            if self.peek(4) == 'hard':
                self.tokens.append(Token('TRY', 'hard', self.line))
                self.advance(4)
                continue

            if self.peek(4) == 'mold':
                self.tokens.append(Token('MOD', 'mold', self.line))
                self.advance(4)
                continue

            if self.peek(4) == 'aint':
                self.tokens.append(Token('NEQ', 'aint', self.line))
                self.advance(4)
                continue

            if self.peek(4) == 'rayz':
                self.tokens.append(Token('ARRAY', 'rayz', self.line))
                self.advance(4)
                continue

            if self.peek(3) == 'N^0':
                self.tokens.append(Token('NULL', None, self.line))
                self.advance(3)
                continue

            if self.peek(3) == 'RHO':
                self.tokens.append(Token('OR', 'RHO', self.line))
                self.advance(3)
                continue

            if self.peek(3) == 'ego':
                self.tokens.append(Token('SELF', 'ego', self.line))
                self.advance(3)
                continue

            if self.peek(2) == 'iz':
                self.tokens.append(Token('EQ', 'iz', self.line))
                self.advance(2)
                continue

            if self.peek(2) == 'up':
                self.tokens.append(Token('APPEND', 'up', self.line))
                self.advance(2)
                continue

            if self.peek(2) == 'or':
                self.tokens.append(Token('OR', 'or', self.line))
                self.advance(2)
                continue

            # Strings
            if self.code[self.pos] in '"\'':
                self.tokens.append(self.read_string())
                continue

            # Special case: '4' at start of statement is FOR loop
            if self.code[self.pos] == '4':
                # Check if next char is not a digit (so it's not like 42)
                next_pos = self.pos + 1
                if next_pos >= len(self.code) or not self.code[next_pos].isdigit():
                    # Check if at start of statement
                    is_start = (len(self.tokens) == 0 or
                               self.tokens[-1].type == 'NEWLINE' or
                               self.tokens[-1].type in ('END', 'ELSE', 'ELIF', 'COLON', 'LBRACE'))
                    if is_start:
                        self.tokens.append(Token('FOR', '4', self.line))
                        self.advance()
                        continue

            # Numbers
            if self.code[self.pos].isdigit():
                self.tokens.append(self.read_number())
                continue

            # Single char operators (NOT letters - those are identifiers)
            # Context-sensitive: '*' at start of statement is PRINT, otherwise MUL
            if self.code[self.pos] == '*':
                # Check if this is at the start of a statement (after newline or start)
                is_start = (len(self.tokens) == 0 or
                           self.tokens[-1].type == 'NEWLINE' or
                           self.tokens[-1].type in ('END', 'ELSE', 'ELIF', 'COLON', 'LBRACE'))
                if is_start:
                    self.tokens.append(Token('PRINT', '*', self.line))
                else:
                    self.tokens.append(Token('MUL', '*', self.line))
                self.advance()
                continue

            single_chars = {
                '?': 'IF',
                '=': 'ASSIGN',
                '+': 'PLUS',
                '-': 'MINUS',
                '/': 'DIV',
                '^': 'POW',
                '<': 'LT',
                '>': 'GT',
                '&': 'AND',
                '(': 'LPAREN',
                ')': 'RPAREN',
                '[': 'LBRACKET',
                ']': 'RBRACKET',
                '{': 'LBRACE',
                '}': 'RBRACE',
                ':': 'COLON',
                ',': 'COMMA',
                '.': 'DOT',
                '\\': 'LAMBDA',
            }

            if self.code[self.pos] in single_chars:
                char = self.code[self.pos]
                self.tokens.append(Token(single_chars[char], char, self.line))
                self.advance()
                continue

            # Identifiers and single-letter keywords
            if self.code[self.pos].isalpha() or self.code[self.pos] == '_':
                self.tokens.append(self.read_identifier())
                continue

            # Numbers that could be keywords (4 for 'for')
            if self.code[self.pos] == '4':
                self.tokens.append(Token('FOR', '4', self.line))
                self.advance()
                continue

            # Unknown - skip it (forgiving!)
            self.advance()

        self.tokens.append(Token('EOF', None, self.line))
        return self.tokens


# =============================================================================
# PARSER - Build AST
# =============================================================================

class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class PrintStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class InputExpr(ASTNode):
    def __init__(self, prompt):
        self.prompt = prompt

class VarAssign(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class VarRef(ASTNode):
    def __init__(self, name):
        self.name = name

class BinOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value

class IfStmt(ASTNode):
    def __init__(self, condition, then_block, elif_blocks, else_block):
        self.condition = condition
        self.then_block = then_block
        self.elif_blocks = elif_blocks  # list of (condition, block)
        self.else_block = else_block

class ForLoop(ASTNode):
    def __init__(self, var, iterable, body):
        self.var = var
        self.iterable = iterable
        self.body = body

class WhileLoop(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class FuncDef(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FuncCall(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ReturnStmt(ASTNode):
    def __init__(self, value):
        self.value = value

class BreakStmt(ASTNode):
    pass

class ContinueStmt(ASTNode):
    pass

class ArrayLiteral(ASTNode):
    def __init__(self, elements):
        self.elements = elements

class ArrayAccess(ASTNode):
    def __init__(self, array, index):
        self.array = array
        self.index = index

class ArrayAppend(ASTNode):
    def __init__(self, array, value):
        self.array = array
        self.value = value

class ArrayPop(ASTNode):
    def __init__(self, array):
        self.array = array

class LengthExpr(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class DictLiteral(ASTNode):
    def __init__(self, pairs):
        self.pairs = pairs

class MemberAccess(ASTNode):
    def __init__(self, obj, member):
        self.obj = obj
        self.member = member

class LambdaExpr(ASTNode):
    def __init__(self, params, body):
        self.params = params
        self.body = body

class TryStmt(ASTNode):
    def __init__(self, try_block, catch_block):
        self.try_block = try_block
        self.catch_block = catch_block

class ImportStmt(ASTNode):
    def __init__(self, module):
        self.module = module


class Parser:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type != 'NEWLINE' or t.type == 'EOF']
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', None)

    def peek(self, n=1):
        pos = self.pos + n
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token('EOF', None)

    def advance(self):
        token = self.current()
        self.pos += 1
        return token

    def expect(self, type_):
        if self.current().type == type_:
            return self.advance()
        # IC sees what you meant - be forgiving
        print(f"IC expected {type_}, got {self.current().type}. Continuing anyway...")
        return self.current()

    def skip_newlines(self):
        while self.current().type == 'NEWLINE':
            self.advance()

    def parse(self):
        statements = []
        while self.current().type != 'EOF':
            self.skip_newlines()
            if self.current().type == 'EOF':
                break
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    def parse_statement(self):
        self.skip_newlines()
        token = self.current()

        if token.type == 'PRINT':
            return self.parse_print()
        elif token.type == 'IF':
            return self.parse_if()
        elif token.type == 'FOR':
            return self.parse_for()
        elif token.type == 'WHILE':
            return self.parse_while()
        elif token.type == 'FUNCTION':
            return self.parse_function()
        elif token.type == 'RETURN':
            return self.parse_return()
        elif token.type == 'BREAK':
            self.advance()
            return BreakStmt()
        elif token.type == 'CONTINUE':
            self.advance()
            return ContinueStmt()
        elif token.type == 'TRY':
            return self.parse_try()
        elif token.type == 'IMPORT':
            return self.parse_import()
        elif token.type == 'IDENT':
            # Check for single-letter keywords used as statements
            if token.value == 'x' and self.peek().type != 'ASSIGN':
                self.advance()
                return BreakStmt()
            return self.parse_assignment_or_expr()
        elif token.type == 'END':
            return None  # IC ends blocks
        elif token.type == 'ELSE' or token.type == 'ELIF':
            return None  # handled by if
        elif token.type == 'CATCH':
            return None  # handled by try
        else:
            # Try to parse as expression
            expr = self.parse_expression()
            if expr:
                return expr
            self.advance()  # skip unknown
            return None

    def parse_print(self):
        self.advance()  # skip *
        expr = self.parse_expression()
        return PrintStmt(expr)

    def parse_if(self):
        self.advance()  # skip ?
        condition = self.parse_expression()
        self.skip_newlines()

        then_block = []
        while self.current().type not in ('ELSE', 'ELIF', 'END', 'EOF'):
            stmt = self.parse_statement()
            if stmt:
                then_block.append(stmt)
            self.skip_newlines()

        elif_blocks = []
        while self.current().type == 'ELIF':
            self.advance()  # skip file
            elif_cond = self.parse_expression()
            self.skip_newlines()
            elif_body = []
            while self.current().type not in ('ELSE', 'ELIF', 'END', 'EOF'):
                stmt = self.parse_statement()
                if stmt:
                    elif_body.append(stmt)
                self.skip_newlines()
            elif_blocks.append((elif_cond, elif_body))

        else_block = []
        if self.current().type == 'ELSE':
            self.advance()  # skip Ls
            self.skip_newlines()
            while self.current().type not in ('END', 'EOF'):
                stmt = self.parse_statement()
                if stmt:
                    else_block.append(stmt)
                self.skip_newlines()

        if self.current().type == 'END':
            self.advance()  # skip IC

        return IfStmt(condition, then_block, elif_blocks, else_block)

    def parse_for(self):
        self.advance()  # skip 4
        var = self.advance().value  # loop variable
        self.expect('IN')  # n
        iterable = self.parse_expression()
        self.skip_newlines()

        body = []
        while self.current().type not in ('END', 'EOF'):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()

        if self.current().type == 'END':
            self.advance()  # skip IC

        return ForLoop(var, iterable, body)

    def parse_while(self):
        self.advance()  # skip wyl
        condition = self.parse_expression()
        self.skip_newlines()

        body = []
        while self.current().type not in ('END', 'EOF'):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()

        if self.current().type == 'END':
            self.advance()  # skip IC

        return WhileLoop(condition, body)

    def parse_function(self):
        self.advance()  # skip fun
        name = self.advance().value

        params = []
        while self.current().type == 'IDENT':
            params.append(self.advance().value)

        self.skip_newlines()

        body = []
        while self.current().type not in ('END', 'EOF'):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()

        if self.current().type == 'END':
            self.advance()  # skip IC

        return FuncDef(name, params, body)

    def parse_return(self):
        self.advance()  # skip re:
        value = self.parse_expression()
        return ReturnStmt(value)

    def parse_try(self):
        self.advance()  # skip hard
        self.skip_newlines()

        try_block = []
        while self.current().type not in ('CATCH', 'END', 'EOF'):
            stmt = self.parse_statement()
            if stmt:
                try_block.append(stmt)
            self.skip_newlines()

        catch_block = []
        if self.current().type == 'CATCH':
            self.advance()  # skip C
            self.skip_newlines()
            while self.current().type not in ('END', 'EOF'):
                stmt = self.parse_statement()
                if stmt:
                    catch_block.append(stmt)
                self.skip_newlines()

        if self.current().type == 'END':
            self.advance()  # skip IC

        return TryStmt(try_block, catch_block)

    def parse_import(self):
        self.advance()  # skip ->
        module = self.advance().value
        return ImportStmt(module)

    def parse_assignment_or_expr(self):
        name = self.advance().value

        if self.current().type == 'ASSIGN':
            self.advance()  # skip =
            value = self.parse_expression()
            return VarAssign(name, value)
        elif self.current().type == 'APPEND':
            self.advance()  # skip up
            value = self.parse_expression()
            return ArrayAppend(VarRef(name), value)
        elif self.current().type == 'POP':
            self.advance()  # skip !!!
            return ArrayPop(VarRef(name))
        else:
            # Could be function call
            self.pos -= 1  # go back
            return self.parse_expression()

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.current().type == 'OR':
            op = self.advance().value
            right = self.parse_and()
            left = BinOp(left, 'or', right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.current().type == 'AND':
            self.advance()
            right = self.parse_equality()
            left = BinOp(left, 'and', right)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.current().type in ('EQ', 'NEQ'):
            op = 'iz' if self.current().type == 'EQ' else 'aint'
            self.advance()
            right = self.parse_comparison()
            left = BinOp(left, op, right)
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        while self.current().type in ('LT', 'GT', 'LTE', 'GTE'):
            op = self.advance().value
            right = self.parse_additive()
            left = BinOp(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.current().type in ('PLUS', 'MINUS'):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinOp(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_power()
        while self.current().type in ('MUL', 'DIV', 'MOD'):
            op = self.current().value
            if self.current().type == 'MUL':
                op = '*'
            elif self.current().type == 'MOD':
                op = 'mold'
            self.advance()
            right = self.parse_power()
            left = BinOp(left, op, right)
        return left

    def parse_power(self):
        left = self.parse_unary()
        if self.current().type == 'POW':
            self.advance()
            right = self.parse_power()  # right associative
            left = BinOp(left, '^', right)
        return left

    def parse_unary(self):
        if self.current().type == 'MINUS':
            self.advance()
            operand = self.parse_unary()
            return UnaryOp('-', operand)
        return self.parse_postfix()

    def parse_postfix(self):
        left = self.parse_primary()

        while True:
            if self.current().type == 'DOT':
                self.advance()
                member = self.advance().value
                left = MemberAccess(left, member)
            elif self.current().type == 'LBRACKET':
                self.advance()
                index = self.parse_expression()
                self.expect('RBRACKET')
                left = ArrayAccess(left, index)
            elif self.current().type == 'INCH':
                self.advance()
                left = LengthExpr(left)
            elif self.current().type == 'LPAREN':
                # Function call with parens
                self.advance()
                args = []
                while self.current().type != 'RPAREN':
                    args.append(self.parse_expression())
                    if self.current().type == 'COMMA':
                        self.advance()
                self.expect('RPAREN')
                left = FuncCall(left, args)
            else:
                break

        return left

    def parse_primary(self):
        token = self.current()

        if token.type == 'INT':
            self.advance()
            return Literal(token.value)
        elif token.type == 'FLOAT':
            self.advance()
            return Literal(token.value)
        elif token.type == 'STRING':
            self.advance()
            return Literal(token.value)
        elif token.type == 'TRUE':
            self.advance()
            return Literal(True)
        elif token.type == 'FALSE':
            self.advance()
            return Literal(False)
        elif token.type == 'NULL':
            self.advance()
            return Literal(None)
        elif token.type == 'INPUT':
            self.advance()
            prompt = ""
            if self.current().type == 'STRING':
                prompt = self.advance().value
            return InputExpr(prompt)
        elif token.type == 'IDENT':
            name = self.advance().value
            # Handle single-letter boolean keywords
            if name == 't':
                return Literal(True)
            if name == 'f':
                return Literal(False)
            return VarRef(name)
        elif token.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr
        elif token.type == 'LBRACKET':
            self.advance()
            elements = []
            while self.current().type != 'RBRACKET':
                elements.append(self.parse_expression())
                if self.current().type == 'COMMA':
                    self.advance()
            self.expect('RBRACKET')
            return ArrayLiteral(elements)
        elif token.type == 'LBRACE':
            return self.parse_dict()
        elif token.type == 'LAMBDA':
            return self.parse_lambda()
        elif token.type == 'SELF':
            self.advance()
            return VarRef('ego')
        else:
            return Literal(None)

    def parse_dict(self):
        self.advance()  # skip {
        pairs = []
        while self.current().type != 'RBRACE':
            key = self.advance().value
            self.expect('COLON')
            value = self.parse_expression()
            pairs.append((key, value))
            if self.current().type == 'COMMA':
                self.advance()
        self.expect('RBRACE')
        return DictLiteral(pairs)

    def parse_lambda(self):
        self.advance()  # skip \
        params = []
        while self.current().type == 'IDENT':
            params.append(self.advance().value)
        self.expect('COLON')
        body = self.parse_expression()
        return LambdaExpr(params, body)


# =============================================================================
# INTERPRETER - Execute AST
# =============================================================================

class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name, value):
        self.vars[name] = value

    def update(self, name, value):
        if name in self.vars:
            self.vars[name] = value
        elif self.parent:
            self.parent.update(name, value)
        else:
            self.vars[name] = value


class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class HypnoticFunction:
    def __init__(self, params, body, closure):
        self.params = params
        self.body = body
        self.closure = closure


class HypnoticLambda:
    def __init__(self, params, body, closure):
        self.params = params
        self.body = body
        self.closure = closure


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.setup_builtins()

    def setup_builtins(self):
        # Built-in functions
        self.global_env.set('int', lambda x: int(x))
        self.global_env.set('str', lambda x: str(x))
        self.global_env.set('float', lambda x: float(x))

        # Random module simulation
        class RandomModule:
            @staticmethod
            def randint(a, b):
                return random.randint(a, b)

        self.global_env.set('random', RandomModule())

    def interpret(self, program):
        for stmt in program.statements:
            self.execute(stmt, self.global_env)

    def execute(self, node, env):
        if node is None:
            return None

        method_name = f'exec_{node.__class__.__name__}'
        method = getattr(self, method_name, self.exec_default)
        return method(node, env)

    def exec_default(self, node, env):
        return self.evaluate(node, env)

    def exec_Program(self, node, env):
        result = None
        for stmt in node.statements:
            result = self.execute(stmt, env)
        return result

    def exec_PrintStmt(self, node, env):
        value = self.evaluate(node.expr, env)
        print(value)

    def exec_VarAssign(self, node, env):
        value = self.evaluate(node.value, env)
        env.set(node.name, value)

    def exec_IfStmt(self, node, env):
        if self.evaluate(node.condition, env):
            for stmt in node.then_block:
                self.execute(stmt, env)
        else:
            executed = False
            for elif_cond, elif_body in node.elif_blocks:
                if self.evaluate(elif_cond, env):
                    for stmt in elif_body:
                        self.execute(stmt, env)
                    executed = True
                    break
            if not executed and node.else_block:
                for stmt in node.else_block:
                    self.execute(stmt, env)

    def exec_ForLoop(self, node, env):
        iterable = self.evaluate(node.iterable, env)

        # If it's just a number, make it a range
        if isinstance(iterable, (int, float)):
            iterable = range(int(iterable))

        for item in iterable:
            env.set(node.var, item)
            try:
                for stmt in node.body:
                    self.execute(stmt, env)
            except BreakException:
                break
            except ContinueException:
                continue

    def exec_WhileLoop(self, node, env):
        while self.evaluate(node.condition, env):
            try:
                for stmt in node.body:
                    self.execute(stmt, env)
            except BreakException:
                break
            except ContinueException:
                continue

    def exec_FuncDef(self, node, env):
        func = HypnoticFunction(node.params, node.body, env)
        env.set(node.name, func)

    def exec_ReturnStmt(self, node, env):
        value = self.evaluate(node.value, env)
        raise ReturnException(value)

    def exec_BreakStmt(self, node, env):
        raise BreakException()

    def exec_ContinueStmt(self, node, env):
        raise ContinueException()

    def exec_TryStmt(self, node, env):
        try:
            for stmt in node.try_block:
                self.execute(stmt, env)
        except Exception as e:
            for stmt in node.catch_block:
                self.execute(stmt, env)

    def exec_ImportStmt(self, node, env):
        # Basic import support
        module_name = node.module
        try:
            if module_name == 'random':
                import random as mod
            elif module_name == 'math':
                import math as mod
            else:
                mod = __import__(module_name)
            env.set(module_name, mod)
        except ImportError:
            print(f"IC can't find module: {module_name}")

    def exec_ArrayAppend(self, node, env):
        arr = self.evaluate(node.array, env)
        value = self.evaluate(node.value, env)
        arr.append(value)

    def exec_ArrayPop(self, node, env):
        arr = self.evaluate(node.array, env)
        return arr.pop() if arr else None

    def evaluate(self, node, env):
        if node is None:
            return None

        method_name = f'eval_{node.__class__.__name__}'
        method = getattr(self, method_name, self.eval_default)
        return method(node, env)

    def eval_default(self, node, env):
        return None

    def eval_Literal(self, node, env):
        return node.value

    def eval_VarRef(self, node, env):
        return env.get(node.name)

    def eval_BinOp(self, node, env):
        left = self.evaluate(node.left, env)
        right = self.evaluate(node.right, env)

        ops = {
            '+': lambda a, b: str(a) + str(b) if isinstance(a, str) or isinstance(b, str) else a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: a / b if b != 0 else 0,
            '^': lambda a, b: a ** b,
            'mold': lambda a, b: a % b if b != 0 else 0,
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
            'iz': lambda a, b: a == b,
            'aint': lambda a, b: a != b,
            'and': lambda a, b: a and b,
            'or': lambda a, b: a or b,
        }

        if node.op in ops:
            return ops[node.op](left, right)
        return None

    def eval_UnaryOp(self, node, env):
        operand = self.evaluate(node.operand, env)
        if node.op == '-':
            if isinstance(operand, bool):
                return not operand
            return -operand
        return operand

    def eval_InputExpr(self, node, env):
        if node.prompt:
            return input(node.prompt)
        return input()

    def eval_FuncCall(self, node, env):
        if isinstance(node.name, VarRef):
            func = env.get(node.name.name)
        else:
            func = self.evaluate(node.name, env)

        args = [self.evaluate(arg, env) for arg in node.args]

        if callable(func) and not isinstance(func, (HypnoticFunction, HypnoticLambda)):
            return func(*args)

        if isinstance(func, HypnoticFunction):
            local_env = Environment(func.closure)
            for param, arg in zip(func.params, args):
                local_env.set(param, arg)
            try:
                for stmt in func.body:
                    self.execute(stmt, local_env)
            except ReturnException as e:
                return e.value
            return None

        if isinstance(func, HypnoticLambda):
            local_env = Environment(func.closure)
            for param, arg in zip(func.params, args):
                local_env.set(param, arg)
            return self.evaluate(func.body, local_env)

        return None

    def eval_ArrayLiteral(self, node, env):
        return [self.evaluate(el, env) for el in node.elements]

    def eval_ArrayAccess(self, node, env):
        arr = self.evaluate(node.array, env)
        index = self.evaluate(node.index, env)
        try:
            return arr[int(index)]
        except (IndexError, TypeError):
            return None

    def eval_LengthExpr(self, node, env):
        value = self.evaluate(node.expr, env)
        return len(value) if hasattr(value, '__len__') else 0

    def eval_DictLiteral(self, node, env):
        return {key: self.evaluate(val, env) for key, val in node.pairs}

    def eval_MemberAccess(self, node, env):
        obj = self.evaluate(node.obj, env)
        if isinstance(obj, dict):
            return obj.get(node.member)
        return getattr(obj, node.member, None)

    def eval_LambdaExpr(self, node, env):
        return HypnoticLambda(node.params, node.body, env)

    def eval_ArrayAppend(self, node, env):
        arr = self.evaluate(node.array, env)
        value = self.evaluate(node.value, env)
        arr.append(value)
        return arr

    def eval_ArrayPop(self, node, env):
        arr = self.evaluate(node.array, env)
        return arr.pop() if arr else None


# =============================================================================
# MAIN
# =============================================================================

def run_code(code, debug=False):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    if debug:
        print("Tokens:", tokens)

    parser = Parser(tokens)
    ast = parser.parse()
    if debug:
        print("AST parsed")

    interpreter = Interpreter()
    interpreter.interpret(ast)


def run_file(filename, debug=False):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        if debug:
            print(f"Code: {repr(code)}")
        run_code(code, debug)
    except FileNotFoundError:
        print(f"IC can't find file: {filename}")


def repl():
    print("hypnotIC v0.1 - I see what you meant.")
    print("Type 'exit' to quit.\n")

    interpreter = Interpreter()

    while True:
        try:
            code = input("IC> ")
            if code.strip().lower() == 'exit':
                break
            if not code.strip():
                continue

            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            interpreter.interpret(ast)
        except KeyboardInterrupt:
            print("\nIC sees you want to leave.")
            break
        except Exception as e:
            print(f"IC saw a problem: {e}")


def main():
    import sys
    sys.stdout.flush()

    debug = '-d' in sys.argv
    args = [a for a in sys.argv[1:] if a != '-d']

    if len(args) < 1:
        repl()
    elif args[0] == '-c' and len(args) > 1:
        run_code(args[1], debug)
    else:
        run_file(args[0], debug)


if __name__ == "__main__":
    main()
