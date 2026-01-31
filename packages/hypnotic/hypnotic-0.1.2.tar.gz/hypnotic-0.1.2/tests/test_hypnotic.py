"""
Tests for hypnotIC interpreter
Run with: pytest tests/
"""

import sys
import io
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hypnotic import Lexer, Parser, Interpreter, run_code


def capture_output(code):
    """Run hypnotIC code and capture stdout."""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        run_code(code)
        return sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout


class TestBasics:
    def test_hello_world(self):
        output = capture_output('* "Hello, world!"')
        assert output.strip() == "Hello, world!"

    def test_print_number(self):
        output = capture_output('* 42')
        assert output.strip() == "42"

    def test_print_expression(self):
        output = capture_output('* 2 + 2')
        assert output.strip() == "4"


class TestVariables:
    def test_assign_and_print(self):
        output = capture_output('x = 5\n* x')
        assert output.strip() == "5"

    def test_string_variable(self):
        output = capture_output('name = "IC"\n* name')
        assert output.strip() == "IC"

    def test_boolean_true(self):
        output = capture_output('flag = t\n* flag')
        assert output.strip() == "True"

    def test_boolean_false(self):
        output = capture_output('flag = f\n* flag')
        assert output.strip() == "False"


class TestMath:
    def test_addition(self):
        output = capture_output('* 10 + 5')
        assert output.strip() == "15"

    def test_subtraction(self):
        output = capture_output('* 10 - 3')
        assert output.strip() == "7"

    def test_multiplication(self):
        output = capture_output('* 4 * 5')
        assert output.strip() == "20"

    def test_division(self):
        output = capture_output('* 20 / 4')
        assert output.strip() == "5.0"

    def test_exponent(self):
        output = capture_output('* 2 ^ 10')
        assert output.strip() == "1024"

    def test_modulo(self):
        output = capture_output('* 10 mold 3')
        assert output.strip() == "1"


class TestComparisons:
    def test_equals_true(self):
        output = capture_output('* 5 iz 5')
        assert output.strip() == "True"

    def test_equals_false(self):
        output = capture_output('* 5 iz 6')
        assert output.strip() == "False"

    def test_not_equals(self):
        output = capture_output('* 5 aint 6')
        assert output.strip() == "True"

    def test_greater_than(self):
        output = capture_output('* 10 > 5')
        assert output.strip() == "True"

    def test_less_than(self):
        output = capture_output('* 3 < 7')
        assert output.strip() == "True"


class TestConditionals:
    def test_if_true(self):
        code = '''
? 5 > 3
* "yes"
IC
'''
        output = capture_output(code)
        assert output.strip() == "yes"

    def test_if_false_else(self):
        code = '''
? 3 > 5
* "yes"
Ls
* "no"
IC
'''
        output = capture_output(code)
        assert output.strip() == "no"

    def test_elif(self):
        code = '''
x = 5
? x iz 3
* "three"
file x iz 5
* "five"
Ls
* "other"
IC
'''
        output = capture_output(code)
        assert output.strip() == "five"


class TestLoops:
    def test_for_loop(self):
        code = '''
4 i n 5
* i
IC
'''
        output = capture_output(code)
        lines = output.strip().split('\n')
        assert lines == ['0', '1', '2', '3', '4']

    def test_while_loop(self):
        code = '''
x = 3
wyl x > 0
* x
x = x - 1
IC
'''
        output = capture_output(code)
        lines = output.strip().split('\n')
        assert lines == ['3', '2', '1']

    def test_break(self):
        code = '''
4 i n 10
? i iz 3
x
IC
* i
IC
'''
        output = capture_output(code)
        lines = output.strip().split('\n')
        assert lines == ['0', '1', '2']


class TestFunctions:
    def test_basic_function(self):
        code = '''
fun greet name
* "Hello " + name
IC
greet("World")
'''
        output = capture_output(code)
        assert output.strip() == "Hello World"

    def test_function_return(self):
        code = '''
fun add a b
re: a + b
IC
* add(3, 4)
'''
        output = capture_output(code)
        assert output.strip() == "7"

    def test_lambda(self):
        code = r'''
double = \ x : x * 2
* double(5)
'''
        output = capture_output(code)
        assert output.strip() == "10"


class TestArrays:
    def test_array_literal(self):
        code = '''
nums = [1 2 3]
* nums[0]
'''
        output = capture_output(code)
        assert output.strip() == "1"

    def test_array_iteration(self):
        code = '''
nums = [1 2 3]
4 x n nums
* x
IC
'''
        output = capture_output(code)
        lines = output.strip().split('\n')
        assert lines == ['1', '2', '3']


class TestComments:
    def test_comment_ignored(self):
        code = '''
fuck this is a comment
* "hello"
fuck another comment
'''
        output = capture_output(code)
        assert output.strip() == "hello"


class TestStrings:
    def test_string_concat(self):
        output = capture_output('* "Hello" + " " + "World"')
        assert output.strip() == "Hello World"

    def test_escape_newline(self):
        output = capture_output(r'* "line1\nline2"')
        assert "line1" in output and "line2" in output


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
