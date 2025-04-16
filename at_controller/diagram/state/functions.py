import re
from dataclasses import dataclass
from dataclasses import field
from logging import getLogger
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import Union
from urllib.parse import parse_qs
from urllib.parse import urlparse

from at_controller.diagram.state.conditions import BinaryOperationCondition
from at_controller.diagram.state.conditions import NonArgOperationCondition


if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine

logger = getLogger(__name__)


@dataclass(kw_only=True)
class Function:
    name: str
    kwargs: Optional[Dict[str, Union[str, int, float, bool, list, dict, "Function"]]] = field(default_factory=dict)

    def _search_and_call_functions(
        self, value: Any, state_machine: "StateMachine", frames: Dict[str, str], **kwargs
    ) -> dict:
        if isinstance(value, Function):
            return value.exec(state_machine, frames, **kwargs)
        elif isinstance(value, dict):
            return {k: self._search_and_call_functions(v, state_machine, frames, **kwargs) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._search_and_call_functions(item, state_machine, frames, **kwargs) for item in value]
        return value

    @staticmethod
    def search_and_call_functions(
        value: Any, state_machine: "StateMachine", frames: Dict[str, str], event_data: dict = None
    ):
        if isinstance(value, Function):
            return value.call(state_machine, frames, event_data=event_data)
        elif isinstance(value, dict):
            return {
                k: Function.search_and_call_functions(v, state_machine, frames, event_data=event_data)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            return [
                Function.search_and_call_functions(item, state_machine, frames, event_data=event_data) for item in value
            ]
        return value

    def call(
        self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None, initial_event_data: Any = None
    ):
        kwargs = self._search_and_call_functions(
            self.kwargs, state_machine, frames, event_data=event_data, initial_event_data=initial_event_data
        )
        return self.exec(state_machine, frames, event_data=event_data, **kwargs)

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        pass


class AttributeArg(TypedDict):
    attribute: str


@dataclass(kw_only=True)
class GetAttribute(Function):
    name: Literal["get_attribute"] = field(default="get_attribute")
    kwargs: AttributeArg

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        return state_machine.attributes.get(self.kwargs["attribute"])


class UrlRegexpSub(TypedDict):
    regexp: str
    group: Optional[int]


class QueryParamSub(TypedDict):
    param: str
    index: Optional[int]


class FrameUrlArg(TypedDict):
    frame_id: str
    parse: Optional[UrlRegexpSub]
    query_param: Optional[QueryParamSub]


@dataclass(kw_only=True)
class FrameUrl(Function):
    name: Literal["frame_url"]
    kwargs: FrameUrlArg

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        frame_id = kwargs["frame_id"]
        url = frames.get(frame_id)

        if "parse" in kwargs:
            parse = kwargs["parse"]
            match = re.match(parse["regexp"], url)
            if match is None:
                return None
            return match.groups()[parse["group"]]

        if "query_params" in kwargs:
            query_params = kwargs["query_params"]
            query_string = urlparse(url).query
            query_params = parse_qs(query_string)
            if "index" in kwargs["query_params"]:
                index = kwargs["query_params"]["index"] or 0
                return query_params.get(
                    kwargs["query_params"]["param"],
                    [None] * (index + 1),
                )[index]
            else:
                return query_params.get(kwargs["query_params"], [None])[0]
        return url


@dataclass(kw_only=True)
class AuthToken(Function):
    name: Literal["auth_token"]
    kwargs: Dict

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        return state_machine.auth_token


class EventDataKwargs(TypedDict):
    key_path: Optional[List[str]]


@dataclass(kw_only=True)
class EventData(Function):
    name: Literal["event_data"]
    kwargs: EventDataKwargs

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        if self.kwargs and self.kwargs.get("key_path"):
            return self.extract(event_data, self.kwargs["key_path"])
        return event_data

    @staticmethod
    def extract(data: Union[Dict, List], key_path: List[str]) -> Any:
        if not len(key_path):
            return data
        if isinstance(data, dict):
            return EventData.extract(data.get(key_path[0], {}), key_path=key_path[1:])
        if isinstance(data, list) and len(data) > key_path[0]:
            return data[key_path[0]]
        return None


@dataclass(kw_only=True)
class InitialEventData(Function):
    name: Literal["initial_event_data"]
    kwargs: EventDataKwargs

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        if self.kwargs and self.kwargs.get("key_path"):
            return EventData.extract(initial_event_data, self.kwargs["key_path"])
        return initial_event_data


class LogicalFunctionKwargs(TypedDict):
    items: List[Union[str, int, float, bool, "Function", list, dict]]


@dataclass(kw_only=True)
class AndFunction(Function):
    name: Literal["and"]
    kwargs: LogicalFunctionKwargs

    def call(self, state_machine, frames, event_data=None, initial_event_data=None):
        return self.exec(state_machine, frames, event_data, initial_event_data)

    @property
    def items(self):
        return self.kwargs["items"]

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        result = True
        for f in self.items:
            new_result = f.call(state_machine, frames, event_data, initial_event_data=initial_event_data) if isinstance(f, Function) else f
            result = result and new_result
            if not result:
                return result
        return result


@dataclass(kw_only=True)
class OrFunction(Function):
    name: Literal["or"]
    kwargs: LogicalFunctionKwargs

    def call(self, state_machine, frames, event_data=None, initial_event_data=None):
        return self.exec(state_machine, frames, event_data, initial_event_data)

    @property
    def items(self):
        return self.kwargs["items"]

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        result = False
        for f in self.items:
            new_result = f.call(state_machine, frames, event_data, initial_event_data=initial_event_data) if isinstance(f, Function) else f
            result = result or new_result
            if result:
                return result
        return result


UnaryFuncType = Literal[
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
    "state_attr",
    "not",
]


class UnaryFunctionKwargs(TypedDict):
    value: Union[str, int, float, bool, "Function", list, dict]


@dataclass(kw_only=True)
class UnaryFunction(Function):
    name: UnaryFuncType
    kwargs: UnaryFunctionKwargs

    @property
    def value(self):
        return self.kwargs["value"]

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        checking_value = (
            self.value.call(state_machine, frames, event_data) if isinstance(self.value, Function) else self.value
        )
        if self.name == "not":
            return not checking_value
        if self.name == "state_attr":
            return state_machine.attributes.get(checking_value)
        cond = NonArgOperationCondition(type=self.name)
        return cond.perform_operation(checking_value=checking_value, state_machine=state_machine)


class BinaryFunctionKwargs(TypedDict):
    left_value: Union[str, int, float, bool, "Function", list, dict]
    right_value: Union[str, int, float, bool, "Function", list, dict]


BinaryFuncType = Literal[
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
    "get_attr",
    "has_attr",
]


@dataclass(kw_only=True)
class BinaryFunction(Function):
    name: BinaryFuncType
    kwargs: BinaryFunctionKwargs

    @property
    def left_value(self):
        return self.kwargs["left_value"]

    @property
    def right_value(self):
        return self.kwargs["right_value"]

    def exec(
        self,
        state_machine: "StateMachine",
        frames: Dict[str, str],
        event_data: Any = None,
        initial_event_data: Any = None,
        **kwargs
    ):
        left_value = (
            self.left_value.call(state_machine, frames, event_data)
            if isinstance(self.left_value, Function)
            else self.left_value
        )
        right_value = (
            self.right_value.call(state_machine, frames, event_data)
            if isinstance(self.right_value, Function)
            else self.right_value
        )
        cond = BinaryOperationCondition(type=self.name, argument=right_value)
        return cond.perform_operation(checking_value=left_value, state_machine=state_machine)
