"""Tests for symbolic execution."""

import pytest
import ast
import z3
from rotalabs_verity.encoder import SymbolicExecutor, EncodingError
from rotalabs_verity.core import ProblemSpec, StateVariable, InputVariable, Property


@pytest.fixture
def simple_spec():
    """Simple counter specification."""
    return ProblemSpec(
        problem_id="TEST-001",
        name="Simple Counter",
        category="test",
        difficulty="easy",
        description="A counter",
        method_signature="def decrement(self, amount: int) -> bool",
        state_variables=[
            StateVariable("count", "int", "Counter", bounds=(0, 100)),
        ],
        input_variables=[
            InputVariable("amount", "int", "Amount", bounds=(1, 10)),
        ],
        output_type="bool",
        properties=[]
    )


class TestSymbolicExecutor:
    def test_simple_return(self, simple_spec):
        """Execute simple return."""
        code = "return True"
        body = ast.parse(code).body

        executor = SymbolicExecutor(simple_spec)
        pre = {"count": z3.Int("count_pre")}
        inputs = {"amount": z3.Int("amount")}

        post, output, _ = executor.execute(body, pre, inputs)

        # Check output is True
        solver = z3.Solver()
        solver.add(output == True)
        assert solver.check() == z3.sat

    def test_assignment(self, simple_spec):
        """Execute assignment."""
        code = '''
self.count = self.count - amount
return True
'''
        body = ast.parse(code).body

        executor = SymbolicExecutor(simple_spec)
        pre = {"count": z3.Int("count_pre")}
        inputs = {"amount": z3.Int("amount")}

        post, output, _ = executor.execute(body, pre, inputs)

        # Check count_post = count_pre - amount
        solver = z3.Solver()
        solver.add(pre["count"] == 10)
        solver.add(inputs["amount"] == 3)
        solver.add(post["count"] == pre["count"] - inputs["amount"])

        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(post["count"]).as_long() == 7

    def test_conditional(self, simple_spec):
        """Execute if statement."""
        code = '''
if self.count >= amount:
    self.count = self.count - amount
    return True
return False
'''
        body = ast.parse(code).body

        executor = SymbolicExecutor(simple_spec)
        pre = {"count": z3.Int("count_pre")}
        inputs = {"amount": z3.Int("amount")}

        post, output, _ = executor.execute(body, pre, inputs)

        solver = z3.Solver()

        # Case 1: count >= amount (should succeed)
        solver.push()
        solver.add(pre["count"] == 10)
        solver.add(inputs["amount"] == 3)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(output) == True
        assert model.eval(post["count"]).as_long() == 7
        solver.pop()

        # Case 2: count < amount (should fail)
        solver.push()
        solver.add(pre["count"] == 2)
        solver.add(inputs["amount"] == 5)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(output) == False
        solver.pop()

    def test_augmented_assignment(self, simple_spec):
        """Execute augmented assignment."""
        code = '''
self.count -= amount
return True
'''
        body = ast.parse(code).body

        executor = SymbolicExecutor(simple_spec)
        pre = {"count": z3.Int("count_pre")}
        inputs = {"amount": z3.Int("amount")}

        post, output, _ = executor.execute(body, pre, inputs)

        solver = z3.Solver()
        solver.add(pre["count"] == 10)
        solver.add(inputs["amount"] == 3)

        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(post["count"]).as_long() == 7

    def test_min_max_abs(self, simple_spec):
        """Execute min, max, abs functions."""
        code = '''
self.count = min(max(amount, 0), 100)
return True
'''
        body = ast.parse(code).body

        executor = SymbolicExecutor(simple_spec)
        pre = {"count": z3.Int("count_pre")}
        inputs = {"amount": z3.Int("amount")}

        post, output, _ = executor.execute(body, pre, inputs)

        solver = z3.Solver()

        # Test with amount = 50 -> count = 50
        solver.push()
        solver.add(inputs["amount"] == 50)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(post["count"]).as_long() == 50
        solver.pop()

        # Test with amount = 150 -> count = 100 (capped)
        solver.push()
        solver.add(inputs["amount"] == 150)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(post["count"]).as_long() == 100
        solver.pop()

    def test_conditional_expression(self, simple_spec):
        """Execute conditional expression."""
        code = '''
self.count = self.count - amount if self.count >= amount else self.count
return self.count >= 0
'''
        body = ast.parse(code).body

        executor = SymbolicExecutor(simple_spec)
        pre = {"count": z3.Int("count_pre")}
        inputs = {"amount": z3.Int("amount")}

        post, output, _ = executor.execute(body, pre, inputs)

        solver = z3.Solver()

        # When count >= amount, decrement happens
        solver.push()
        solver.add(pre["count"] == 10)
        solver.add(inputs["amount"] == 3)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(post["count"]).as_long() == 7
        solver.pop()

        # When count < amount, no change
        solver.push()
        solver.add(pre["count"] == 2)
        solver.add(inputs["amount"] == 5)
        assert solver.check() == z3.sat
        model = solver.model()
        assert model.eval(post["count"]).as_long() == 2
        solver.pop()
