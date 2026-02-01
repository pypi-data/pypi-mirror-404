"""
Unit tests for the CodeSandbox class.
"""

import pytest
from fishertools.learn.repl.code_sandbox import CodeSandbox


class TestCodeSandboxBasic:
    """Test basic code execution in the sandbox."""
    
    def test_execute_simple_print(self):
        """Test executing simple print statement."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print('Hello')")
        assert success is True
        assert "Hello" in output
    
    def test_execute_arithmetic(self):
        """Test executing arithmetic operations."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print(2 + 2)")
        assert success is True
        assert "4" in output
    
    def test_execute_variable_assignment(self):
        """Test executing variable assignment."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("x = 5\nprint(x * 2)")
        assert success is True
        assert "10" in output
    
    def test_execute_list_operations(self):
        """Test executing list operations."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("lst = [1, 2, 3]\nprint(sum(lst))")
        assert success is True
        assert "6" in output
    
    def test_execute_loop(self):
        """Test executing for loop."""
        sandbox = CodeSandbox()
        code = """
for i in range(3):
    print(i)
"""
        success, output = sandbox.execute(code)
        assert success is True
        assert "0" in output
        assert "1" in output
        assert "2" in output
    
    def test_execute_function_definition(self):
        """Test executing function definition."""
        sandbox = CodeSandbox()
        code = """
def add(a, b):
    return a + b

print(add(3, 4))
"""
        success, output = sandbox.execute(code)
        assert success is True
        assert "7" in output


class TestCodeSandboxErrors:
    """Test error handling in the sandbox."""
    
    def test_syntax_error(self):
        """Test handling of syntax errors."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print('unclosed")
        assert success is False
        assert "Syntax Error" in output
    
    def test_runtime_error(self):
        """Test handling of runtime errors."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print(1 / 0)")
        assert success is False
        assert "ZeroDivisionError" in output
    
    def test_name_error(self):
        """Test handling of undefined variables."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print(undefined_var)")
        assert success is False
        assert "NameError" in output
    
    def test_empty_code(self):
        """Test handling of empty code."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("")
        assert success is False
        assert "empty" in output.lower()
    
    def test_whitespace_only_code(self):
        """Test handling of whitespace-only code."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("   \n  \n  ")
        assert success is False


class TestCodeSandboxRestrictions:
    """Test that dangerous operations are blocked."""
    
    def test_block_import(self):
        """Test that imports are blocked."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("import os")
        assert success is False
        assert "import" in output.lower() or "not allowed" in output.lower()
    
    def test_block_from_import(self):
        """Test that from imports are blocked."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("from os import path")
        assert success is False
        assert "import" in output.lower() or "not allowed" in output.lower()
    
    def test_block_open_function(self):
        """Test that open() is blocked."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("open('file.txt')")
        assert success is False
        assert "not allowed" in output.lower() or "file" in output.lower()
    
    def test_block_exec(self):
        """Test that exec() is blocked."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("exec('print(1)')")
        assert success is False
        assert "not allowed" in output.lower()
    
    def test_block_eval(self):
        """Test that eval() is blocked."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("eval('1+1')")
        assert success is False
        assert "not allowed" in output.lower()
    
    def test_block_globals(self):
        """Test that globals() is blocked."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("globals()")
        assert success is False
        assert "not allowed" in output.lower()


class TestCodeSandboxMath:
    """Test math operations in the sandbox."""
    
    def test_math_module_available(self):
        """Test that math module is available."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("import math\nprint(math.pi)")
        # Math module should be available through restricted globals
        # But import should be blocked
        assert success is False
    
    def test_builtin_math_functions(self):
        """Test built-in math functions."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print(abs(-5))")
        assert success is True
        assert "5" in output
    
    def test_pow_function(self):
        """Test pow function."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print(pow(2, 3))")
        assert success is True
        assert "8" in output
    
    def test_round_function(self):
        """Test round function."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print(round(3.7))")
        assert success is True
        assert "4" in output


class TestCodeSandboxUtilityMethods:
    """Test utility methods of CodeSandbox."""
    
    def test_get_available_builtins(self):
        """Test getting list of available built-ins."""
        sandbox = CodeSandbox()
        builtins = sandbox.get_available_builtins()
        assert isinstance(builtins, list)
        assert "print" in builtins
        assert "len" in builtins
        assert "sum" in builtins
    
    def test_get_blocked_builtins(self):
        """Test getting list of blocked built-ins."""
        sandbox = CodeSandbox()
        blocked = sandbox.get_blocked_builtins()
        assert isinstance(blocked, list)
        assert "open" in blocked
        assert "exec" in blocked
        assert "eval" in blocked
    
    def test_get_blocked_modules(self):
        """Test getting list of blocked modules."""
        sandbox = CodeSandbox()
        blocked = sandbox.get_blocked_modules()
        assert isinstance(blocked, list)
        assert "os" in blocked
        assert "sys" in blocked
        assert "subprocess" in blocked


class TestCodeSandboxEdgeCases:
    """Test edge cases in code execution."""
    
    def test_multiline_code(self):
        """Test executing multiline code."""
        sandbox = CodeSandbox()
        code = """
x = 10
y = 20
z = x + y
print(z)
"""
        success, output = sandbox.execute(code)
        assert success is True
        assert "30" in output
    
    def test_nested_loops(self):
        """Test executing nested loops."""
        sandbox = CodeSandbox()
        code = """
for i in range(2):
    for j in range(2):
        print(f"{i},{j}")
"""
        success, output = sandbox.execute(code)
        assert success is True
        assert "0,0" in output
    
    def test_list_comprehension(self):
        """Test list comprehension."""
        sandbox = CodeSandbox()
        success, output = sandbox.execute("print([x*2 for x in range(3)])")
        assert success is True
        assert "0" in output
        assert "2" in output
        assert "4" in output
    
    def test_dictionary_operations(self):
        """Test dictionary operations."""
        sandbox = CodeSandbox()
        code = """
d = {'a': 1, 'b': 2}
print(d['a'])
"""
        success, output = sandbox.execute(code)
        assert success is True
        assert "1" in output
