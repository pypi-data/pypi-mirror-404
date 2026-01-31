"""
RP-006: Gossip Protocol

Epidemic broadcast for state dissemination.
"""

from rotalabs_verity.core import (
    Example,
    InputVariable,
    ProblemSpec,
    Property,
    StateVariable,
)

PROBLEM_ID = "RP-006"
NAME = "Gossip Protocol"
CATEGORY = "replication"
DIFFICULTY = "hard"

DESCRIPTION = """
Implement Gossip Protocol.

receive_gossip(sender_value, sender_version):
1. gossip_rounds = gossip_rounds + 1
2. If sender_version > local_version:
   - local_value = sender_value
   - local_version = sender_version
   - infected = 1
   - return True (state updated)
3. return False (already up to date)
"""

METHOD_SIGNATURE = "def receive_gossip(self, sender_value: int, sender_version: int) -> bool"

STATE_VARIABLES = [
    StateVariable(
        name="local_value",
        var_type="int",
        description="Local data value",
        bounds=(0, 1000),
        initial_value=0
    ),
    StateVariable(
        name="local_version",
        var_type="int",
        description="Local version",
        bounds=(0, 100),
        initial_value=0
    ),
    StateVariable(
        name="infected",
        var_type="int",
        description="Whether node has new data to spread (0 or 1)",
        bounds=(0, 1),
        initial_value=0
    ),
    StateVariable(
        name="gossip_rounds",
        var_type="int",
        description="Number of gossip rounds participated",
        bounds=(0, 100),
        initial_value=0
    ),
]

INPUT_VARIABLES = [
    InputVariable(
        name="sender_value",
        var_type="int",
        description="Value from sender",
        bounds=(1, 1000)
    ),
    InputVariable(
        name="sender_version",
        var_type="int",
        description="Version from sender",
        bounds=(0, 100)
    ),
]

OUTPUT_TYPE = "bool"


def _prop_version_monotonic(pre, post, inputs, output):
    """local_version must not decrease."""
    return post["local_version"] >= pre["local_version"]


def _prop_infected_valid(pre, post, inputs, output):
    """infected must be 0 or 1."""
    import z3
    return z3.And(post["infected"] >= 0, post["infected"] <= 1)


PROPERTIES = [
    Property(
        name="version_monotonic",
        description="local_version must not decrease",
        formula="□(local_version' >= local_version)",
        encode=_prop_version_monotonic
    ),
    Property(
        name="infected_valid",
        description="infected must be 0 or 1",
        formula="□(0 <= infected <= 1)",
        encode=_prop_infected_valid
    ),
]


EXAMPLES = [
    Example(
        name="receive_update",
        description="Receive gossip with newer data",
        pre_state={"local_value": 0, "local_version": 0, "infected": 0, "gossip_rounds": 0},
        inputs={"sender_value": 42, "sender_version": 3},
        expected_output=True,
        expected_post_state={"local_value": 42, "local_version": 3, "infected": 1, "gossip_rounds": 1}
    ),
]


BUGGY_CODE = """
def receive_gossip(self, sender_value: int, sender_version: int) -> bool:
    self.gossip_rounds = self.gossip_rounds + 1
    if sender_version > self.local_version:
        self.local_value = sender_value
        self.local_version = sender_version
        # BUG: Sets infected to invalid value
        self.infected = 5
        return True
    return False
"""

CORRECT_CODE = """
def receive_gossip(self, sender_value: int, sender_version: int) -> bool:
    self.gossip_rounds = self.gossip_rounds + 1
    if sender_version > self.local_version:
        self.local_value = sender_value
        self.local_version = sender_version
        self.infected = 1
        return True
    return False
"""


def get_spec() -> ProblemSpec:
    return ProblemSpec(
        problem_id=PROBLEM_ID,
        name=NAME,
        category=CATEGORY,
        difficulty=DIFFICULTY,
        description=DESCRIPTION,
        method_signature=METHOD_SIGNATURE,
        state_variables=STATE_VARIABLES,
        input_variables=INPUT_VARIABLES,
        output_type=OUTPUT_TYPE,
        properties=PROPERTIES,
        examples=EXAMPLES,
        buggy_code=BUGGY_CODE,
        correct_code=CORRECT_CODE,
        tags=["replication", "gossip"]
    )
