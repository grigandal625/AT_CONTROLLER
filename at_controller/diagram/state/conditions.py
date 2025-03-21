import math
import operator
from dataclasses import dataclass
from dataclasses import field
from logging import getLogger
from typing import Any
from typing import List
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

import numpy as np

if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine

logger = getLogger(__name__)


@dataclass(kw_only=True)
class Condition:
    type: str

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        raise NotImplementedError("Not implemented")


EquatationType = Literal["eq", "ne", "gt", "gte", "lt", "lte"]


@dataclass(kw_only=True)
class EquatationCondition(Condition):
    type: EquatationType
    value: Any

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        if self.type == "eq":
            return checking_value == self.value
        elif self.type == "ne":
            return checking_value != self.value
        elif self.type == "gt":
            return checking_value > self.value
        elif self.type == "gte":
            return checking_value >= self.value
        elif self.type == "lt":
            return checking_value < self.value
        elif self.type == "lte":
            return checking_value <= self.value


InclusionType = Literal["in", "not_in", "includes", "not_includes"]


@dataclass(kw_only=True)
class InclusionCondition(Condition):
    type: InclusionType
    value: Any

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        if self.type == "in":
            return checking_value in self.value
        elif self.type == "not_in":
            return checking_value not in self.value
        elif self.type == "includes":
            return self.value in checking_value
        elif self.type == "not_includes":
            return self.value not in checking_value


@dataclass(kw_only=True)
class AndCondition(Condition):
    type: Literal["and"]
    arguments: List["AllConditionsType"]

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        return all(condition.check(checking_value, state_machine) for condition in self.arguments)


@dataclass(kw_only=True)
class OrCondition(Condition):
    type: Literal["or"]
    arguments: List["AllConditionsType"]

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        return any(condition.check(checking_value, state_machine) for condition in self.arguments)


@dataclass(kw_only=True)
class NotCondition(Condition):
    type: Literal["not"]
    condition: Union["AllConditionsType"]

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        return not self.condition.check(checking_value, state_machine)


@dataclass(kw_only=True)
class OperationCondition(Condition):
    type: str
    condition: Optional["AllConditionsType"] = field(default=None)

    def perform_operation(self, checking_value, state_machine: "StateMachine", *args, **kwargs):
        pass

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        v = self.perform_operation(checking_value, state_machine, *args, **kwargs)
        if self.condition is not None:
            return self.condition.check(v, state_machine)
        return v


NonArgType = Literal[
    "len",
    "sqrt",
    "abs",
    "ceil",
    "floor",
    "round",
    "sign",
    "log",
    "exp",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "neg",
    "transpose",
    "det",
    "inv",
    "norm",
    "trace",
    "is_null",
]


@dataclass(kw_only=True)
class NonArgOperationCondition(OperationCondition):
    type: NonArgType

    def perform_operation(self, checking_value, state_machine: "StateMachine"):
        if self.type == "len":
            return len(checking_value)
        elif self.type == "sqrt":
            return math.sqrt(checking_value)
        elif self.type == "abs":
            return abs(checking_value)
        elif self.type == "ceil":
            return math.ceil(checking_value)
        elif self.type == "floor":
            return math.floor(checking_value)
        elif self.type == "round":
            return round(checking_value)
        elif self.type == "sign":
            return math.copysign(1, checking_value)
        elif self.type == "log":
            return math.log(checking_value)
        elif self.type == "exp":
            return math.exp(checking_value)
        elif self.type == "sin":
            return math.sin(checking_value)
        elif self.type == "cos":
            return math.cos(checking_value)
        elif self.type == "tan":
            return math.tan(checking_value)
        elif self.type == "asin":
            return math.asin(checking_value)
        elif self.type == "acos":
            return math.acos(checking_value)
        elif self.type == "atan":
            return math.atan(checking_value)
        elif self.type == "neg":
            return -checking_value
        elif self.type == "transpose":
            return np.transpose(checking_value)
        elif self.type == "det":
            return np.linalg.det(checking_value)
        elif self.type == "inv":
            return np.linalg.inv(checking_value)
        elif self.type == "norm":
            return np.linalg.norm(checking_value)
        elif self.type == "trace":
            return np.trace(checking_value)
        elif self.type == "is_null":
            return checking_value is None
        else:
            raise ValueError(f"Unsupported operation type: {self.type}")


BinaryType = Literal[
    "add",
    "sub",
    "mul",
    "div",
    "mod",
    "pow",
    "logical_and",
    "logical_or",
    "xor",
    "max",
    "min",
    "equal",
    "not_equal",
    "less_than",
    "less_or_equal",
    "greater_than",
    "greater_or_equal",
    "state_attr",
    "get_attr",
    "has_attr",
]


@dataclass(kw_only=True)
class BinaryOperationCondition(OperationCondition):
    type: BinaryType
    argument: Any

    def perform_operation(self, checking_value, state_machine: "StateMachine"):
        if self.type == "add":
            return checking_value + self.argument
        elif self.type == "sub":
            return checking_value - self.argument
        elif self.type == "mul":
            return checking_value * self.argument
        elif self.type == "div":
            return checking_value / self.argument
        elif self.type == "mod":
            return checking_value % self.argument
        elif self.type == "pow":
            return checking_value**self.argument
        elif self.type == "logical_and":
            return checking_value and self.argument
        elif self.type == "logical_or":
            return checking_value or self.argument
        elif self.type == "xor":
            return operator.xor(checking_value, self.argument)
        elif self.type == "max":
            return max(checking_value, self.argument)
        elif self.type == "min":
            return min(checking_value, self.argument)
        elif self.type == "equal":
            return checking_value == self.argument
        elif self.type == "not_equal":
            return checking_value != self.argument
        elif self.type == "less_than":
            return checking_value < self.argument
        elif self.type == "less_or_equal":
            return checking_value <= self.argument
        elif self.type == "greater_than":
            return checking_value > self.argument
        elif self.type == "greater_or_equal":
            return checking_value >= self.argument
        elif self.type == "state_attr":
            return state_machine.attributes.get(self.argument)
        elif self.type == "get_attr":
            return checking_value[self.argument]
        elif self.type == "has_attr":
            return self.argument in checking_value
        else:
            raise ValueError(f"Unsupported operation type: {self.type}")


AllConditionsType = Union[
    EquatationCondition,
    InclusionCondition,
    AndCondition,
    OrCondition,
    NotCondition,
    NonArgOperationCondition,
    BinaryOperationCondition,
]
