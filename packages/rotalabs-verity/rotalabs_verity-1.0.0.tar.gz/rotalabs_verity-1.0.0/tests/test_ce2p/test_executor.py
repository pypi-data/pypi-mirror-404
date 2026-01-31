"""Tests for concrete executor."""

import pytest
from rotalabs_verity.ce2p import ConcreteExecutor, execute_on_counterexample, ExecutionTrace
from rotalabs_verity.core import Counterexample


class TestConcreteExecutor:
    def test_simple_execution(self):
        """Execute simple code."""
        code = '''
def method(self, x: int) -> int:
    self.count = self.count - x
    return self.count
'''
        executor = ConcreteExecutor(
            initial_state={"count": 10},
            inputs={"x": 3}
        )
        trace = executor.execute(code)

        assert trace.completed
        assert trace.return_value == 7
        assert trace.final_state["count"] == 7

    def test_traces_all_steps(self):
        """Executor should trace all steps."""
        code = '''
def method(self, x: int) -> int:
    self.count = self.count - x
    return self.count
'''
        executor = ConcreteExecutor(
            initial_state={"count": 10},
            inputs={"x": 3}
        )
        trace = executor.execute(code)

        assert len(trace.steps) == 2  # assignment + return
        assert trace.steps[0].source_code == "self.count = self.count - x"
        assert trace.steps[1].source_code == "return self.count"

    def test_records_state_changes(self):
        """Executor should record state before and after."""
        code = '''
def method(self, x: int) -> int:
    self.count = self.count - x
    return self.count
'''
        executor = ConcreteExecutor(
            initial_state={"count": 10},
            inputs={"x": 3}
        )
        trace = executor.execute(code)

        step = trace.steps[0]
        assert step.state_before["count"] == 10
        assert step.state_after["count"] == 7

    def test_conditional_true_branch(self):
        """Execute true branch of conditional."""
        code = '''
def method(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''
        executor = ConcreteExecutor(
            initial_state={"count": 10},
            inputs={"x": 3}
        )
        trace = executor.execute(code)

        assert trace.completed
        assert trace.return_value == True
        assert trace.final_state["count"] == 7

    def test_conditional_false_branch(self):
        """Execute false branch of conditional."""
        code = '''
def method(self, x: int) -> bool:
    if self.count >= x:
        self.count = self.count - x
        return True
    return False
'''
        executor = ConcreteExecutor(
            initial_state={"count": 2},
            inputs={"x": 5}
        )
        trace = executor.execute(code)

        assert trace.completed
        assert trace.return_value == False
        assert trace.final_state["count"] == 2

    def test_augmented_assignment(self):
        """Execute augmented assignment."""
        code = '''
def method(self, x: int) -> int:
    self.count -= x
    return self.count
'''
        executor = ConcreteExecutor(
            initial_state={"count": 10},
            inputs={"x": 3}
        )
        trace = executor.execute(code)

        assert trace.return_value == 7

    def test_builtin_functions(self):
        """Execute built-in functions."""
        code = '''
def method(self, x: int, y: int) -> int:
    self.result = min(max(x, y), 100)
    return self.result
'''
        executor = ConcreteExecutor(
            initial_state={"result": 0},
            inputs={"x": 150, "y": 50}
        )
        trace = executor.execute(code)

        assert trace.return_value == 100


class TestExecuteOnCounterexample:
    def test_convenience_function(self):
        """Test convenience function."""
        code = '''
def method(self, x: int) -> int:
    self.count = self.count - x
    return self.count
'''
        cx = Counterexample(
            pre_state={"count": 10},
            inputs={"x": 3},
            post_state={"count": 7},
            output=7
        )

        trace = execute_on_counterexample(code, cx)

        assert trace.completed
        assert trace.final_state["count"] == 7
