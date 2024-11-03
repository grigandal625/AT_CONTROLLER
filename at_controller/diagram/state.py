import asyncio
import math
import operator
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
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse

import numpy as np
logger = getLogger(__name__)


if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine


@dataclass(kw_only=True)
class Frame:
    frame_id: str
    src: str
    redirect: Optional[str] = field(default=None)
    redirect_param: Optional[str] = field(default="to")
    frame_id_param: Optional[str] = field(default="frame_id")
    type: Literal["basic", "format_attributes"] = field(default="basic")
    span: Optional[Union[int, str]] = field(default="auto")

    def format_src(self, state_machine: "StateMachine"):
        if self.type == "format_attributes":
            return self.src.format_map(state_machine.attributes)
        return self.src

    def format_redirect(self, state_machine: "StateMachine"):
        if self.type == "format_attributes" and self.redirect is not None:
            return self.redirect.format_map(state_machine.attributes)
        return self.redirect

    def get_src(self, state_machine: "StateMachine"):
        src = self.format_src(state_machine)
        if self.redirect is not None:
            redirect = self.format_redirect(state_machine)
            parsed_url = urlparse(src)
            parsed_query = parse_qs(parsed_url.query)

            redirect_param = self.redirect_param or "to"
            parsed_query[redirect_param] = [redirect]

            frame_id_param = self.frame_id_param or "frame_id"
            parsed_query[frame_id_param] = [self.frame_id]

            new_query_string = urlencode(parsed_query, doseq=True)

            final_src = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query_string,
                    parsed_url.fragment,
                )
            )

            return final_src
        return src

    def get_column(self, state_machine: "StateMachine"):
        return {
            "src": self.get_src(state_machine),
            "frame_id": self.frame_id,
            "props": {"flex": self.span, "style": {"height": "100%"}},
        }


@dataclass(kw_only=True)
class State:
    name: str
    label: str
    frame_rows: List[List[Frame]]
    control_label: Optional[str] = field(default=None)
    control_subtitle: Optional[str] = field(default=None)
    translation: Optional[str] = field(default=None)
    initial: Optional[bool] = field(default=False)

    @property
    def annotation(self):
        return self.name

    def get_page(self, state_machine: "StateMachine"):
        link_transitions: List[LinkTransition] = [
            t
            for t in state_machine.diagram.get_state_exit_transitions(self)
            if t.type == "link"
        ]
        frame_handler_transitions: List[FrameHandlerTransition] = [
            t
            for t in state_machine.diagram.get_state_exit_transitions(self)
            if t.type == "frame_handler"
        ]

        header = {
            "label": self.label,
            "links": [
                {
                    "type": "component_method",
                    "label": transition.label,
                    "component": "ATController",
                    "method": "trigger_transition",
                    "kwargs": {
                        "trigger": transition.name,
                    },
                    "framedata_field": "frames",
                }
                for transition in link_transitions
                if transition.position == "header"
            ],
        }

        footer = {
            "links": [
                {
                    "type": "component_method",
                    "label": transition.label,
                    "component": "ATController",
                    "method": "trigger_transition",
                    "kwargs": {
                        "trigger": transition.name,
                    },
                    "framedata_field": "frames",
                }
                for transition in link_transitions
                if transition.position == "footer"
            ]
        }

        control = {
            "label": self.control_label or "",
            "subtitle": self.control_subtitle or "",
            "links": [
                {
                    "type": "component_method",
                    "label": transition.label,
                    "component": "ATController",
                    "method": "trigger_transition",
                    "kwargs": {
                        "trigger": transition.name,
                    },
                    "framedata_field": "frames",
                }
                for transition in link_transitions
                if transition.position == "control"
            ],
        }

        handlers = [
            {
                "type": "component_method",
                "component": "ATController",
                "method": "trigger_transition",
                "test": transition.test,
                "frame_id": transition.frame_id,
                "kwargs": {
                    "trigger": transition.name,
                },
                "framedata_field": "frames",
            }
            for transition in frame_handler_transitions
        ]

        result = {
            "grid": {
                "rows": [
                    {
                        "props": {"style": {"height": "100%"}},
                        "cols": [
                            frame.get_column(state_machine) for frame in frame_row
                        ],
                    }
                    for frame_row in self.frame_rows
                ]
            },
            "header": header,
            "handlers": handlers,
        }

        if footer["links"]:
            result["footer"] = footer
        if control["label"] or control["subtitle"] or control["links"]:
            result["control"] = control

        return result


@dataclass(kw_only=True)
class Transition:
    name: str
    source: Union[str, State]
    dest: Union[str, State]
    type: Literal["link", "frame_handler"]
    actions: List["Action"]
    translation: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)

    @property
    def annotation(self):
        return {
            "trigger": self.name,
            "source": (
                self.source.annotation
                if isinstance(self.source, State)
                else self.source
            ),
            "dest": self.dest.annotation if isinstance(self.dest, State) else self.dest,
        }


@dataclass(kw_only=True)
class LinkTransition(Transition):
    name: str
    label: str
    actions: List["Action"]
    position: Optional[Literal["header", "footer",
                               "control"]] = field(default="header")
    translation: Optional[str] = field(default=None)
    type: Literal["link"] = field(default="link")
    icon: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)


@dataclass(kw_only=True)
class FrameHandlerTransition(Transition):
    name: str
    frame_id: str
    actions: List["Action"] = field(default=None)
    test: str
    type: Literal["frame_handler"] = field(default="frame_handler")
    translation: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)


@dataclass(kw_only=True)
class Condition:
    type: str

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        raise NotImplementedError


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
    arguments: List[
        Union[
            EquatationCondition,
            InclusionCondition,
            "AndCondition",
            "OrCondition",
            "NotCondition",
            "NonArgOperationCondition",
            "BinaryOperationCondition",
        ]
    ]

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        return all(
            condition.check(checking_value, state_machine)
            for condition in self.arguments
        )


@dataclass(kw_only=True)
class OrCondition(Condition):
    type: Literal["or"]
    arguments: List[
        Union[
            EquatationCondition,
            InclusionCondition,
            AndCondition,
            "OrCondition",
            "NotCondition",
            "NonArgOperationCondition",
            "BinaryOperationCondition",
        ]
    ]

    def check(self, checking_value: Any, state_machine: "StateMachine",  *args, **kwargs):
        return any(
            condition.check(checking_value, state_machine)
            for condition in self.arguments
        )


@dataclass(kw_only=True)
class NotCondition(Condition):
    type: Literal["not"]
    condition: Union[
        EquatationCondition,
        InclusionCondition,
        AndCondition,
        OrCondition,
        "NotCondition",
        "NonArgOperationCondition",
        "BinaryOperationCondition",
    ]

    def check(self, checking_value: Any, state_machine: "StateMachine", *args, **kwargs):
        return not self.condition.check(checking_value, state_machine)


@dataclass(kw_only=True)
class OperationCondition(Condition):
    type: str
    condition: Optional[
        Union[
            EquatationCondition,
            InclusionCondition,
            AndCondition,
            OrCondition,
            "NotCondition",
            "NonArgOperationCondition",
            "BinaryOperationCondition",
        ]
    ] = field(default=None)

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
    "has_attr"
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


@dataclass(kw_only=True)
class EventTransition(Transition):
    name: str
    event: Optional[str] = field(default=None)

    trigger_condition: Optional[
        Union[
            EquatationCondition,
            InclusionCondition,
            AndCondition,
            OrCondition,
            NotCondition,
        ]
    ] = field(default=None)

    actions: List["Action"] = field(default=None)
    type: Literal["internal_event"] = field(default="event")
    translation: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)

    def __post_init__(self):
        if not self.event:
            self.event = self.name


@dataclass(kw_only=True)
class Action:
    type: str
    next: Optional[List["Action"]] = field(default=None)

    async def perform(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        result = await self.action(state_machine, frames, event_data=event_data)
        if self.next:
            await asyncio.gather(*[next_action.perform(state_machine, frames, event_data=event_data) for next_action in self.next])
        return result

    async def action(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        pass


@dataclass(kw_only=True)
class SetAttributeAction(Action):
    type: Literal["set_attribute"] = field(default="set_attribute")
    attribute: str
    value: Union[str, int, float, bool, "Function", list, dict]

    async def action(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        value = self.value
        if isinstance(value, Function):
            value = value.exec(state_machine, frames, event_data=event_data, **value.kwargs)
        state_machine.attributes[self.attribute] = value

        result = {}
        result[self.attribute] = value
        return result


@dataclass(kw_only=True)
class ShowMessageAction(Action):
    type: Literal["show_message"] = field(default="show_message")
    message: str
    title: Optional[str] = field(default="")
    modal: Optional[bool] = field(default=True)
    message_type: Optional[str] = field(default="info")

    async def action(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        return await state_machine.component.exec_external_method(
            'ATRenderer',
            'show_message',
            {
                "message": self.format_message(state_machine),
                "modal": self.modal,
                "message_type": self.message_type,
                "title": self.title,
            },
            auth_token=state_machine.auth_token
        )

    def format_message(self, state_machine: "StateMachine"):
        return self.message.format_map(state_machine.attributes)


@dataclass(kw_only=True)
class Function:
    name: str
    kwargs: Optional[
        Dict[str, Union[str, int, float, bool, list, dict, "Function"]]
    ] = field(default_factory=dict)

    def _search_and_call_functions(
        self, value: dict, state_machine: "StateMachine", frames: Dict[str, str]
    ) -> dict:
        for k, v in value.items():
            if isinstance(v, Function):
                value[k] = v.call(state_machine, frames)
            elif isinstance(v, dict):
                value[k] = self._search_and_call_functions(
                    v, state_machine, frames)
            elif isinstance(v, list):
                value[k] = [
                    self._search_and_call_functions(
                        item, state_machine, frames)
                    for item in v
                ]
        return value

    def call(self, state_machine: "StateMachine", frames: Dict[str, str]):
        kwargs = self._search_and_call_functions(
            self.kwargs, state_machine, frames)
        return self.exec(state_machine, frames, **kwargs)

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        pass


class AttributeArg(TypedDict):
    attribute: str


@dataclass(kw_only=True)
class GetAttribute(Function):
    name: Literal["get_attribute"] = field(default="get_attribute")
    kwargs: AttributeArg

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        return state_machine.attributes.get(kwargs["attribute"])


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

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
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
                return query_params.get(
                    kwargs["query_params"]["param"],
                    [None] * (kwargs["query_params"]["index"] + 1),
                )[kwargs["query_params"]["index"]]
            else:
                return query_params.get(kwargs["query_params"], [None])[0]

        return url


@dataclass(kw_only=True)
class AuthToken(Function):
    name: Literal["auth_token"]
    kwargs: Dict

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        return state_machine.auth_token


class EventDataKwargs(TypedDict):
    key_path: Optional[List[str]]


@dataclass(kw_only=True)
class EventData(Function):
    name: Literal["event_data"]
    kwargs: EventDataKwargs

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        if self.kwargs and self.kwargs.get('key_path'):
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


class LogicalFunctionKwargs(TypedDict):
    items: List[Union[str, int, float, bool, "Function", list, dict]]


@dataclass(kw_only=True)
class AndFunction(Function):
    name: Literal['and']
    kwargs: LogicalFunctionKwargs

    @property
    def items(self):
        return self.kwargs["items"]

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        return all(*[f.exec(state_machine, frames, event_data, **kwargs) if isinstance(f, Function) else f for f in self.items])


@dataclass(kw_only=True)
class OrFunction(Function):
    name: Literal['or']
    kwargs: LogicalFunctionKwargs

    @property
    def items(self):
        return self.kwargs["items"]

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        return any(*[f.exec(state_machine, frames, event_data, **kwargs) if isinstance(f, Function) else f for f in self.items])


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
    "state_attr"
]


class UnaryFunctionKwargs(TypedDict):
    value: Union[str, int, float, bool, "Function", list, dict]


@dataclass(kw_only=True)
class UnaryFunction(Function):
    name: NonArgType
    kwargs: UnaryFunctionKwargs

    @property
    def value(self):
        return self.kwargs["value"]

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        checking_value = self.value.exec(state_machine, frames, event_data, **
                                         kwargs) if isinstance(self.value, Function) else self.value
        if self.name == 'state_attr':
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
    "has_attr"
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

    def exec(self, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        left_value = self.left_value.exec(state_machine, frames, event_data, **
                                          kwargs) if isinstance(self.left_value, Function) else self.left_value
        right_value = self.right_value.exec(state_machine, frames, event_data, **
                                            kwargs) if isinstance(self.right_value, Function) else self.right_value
        cond = BinaryOperationCondition(type=self.name, argument=right_value)
        return cond.perform_operation(checking_value=left_value, state_machine=state_machine)


@dataclass(kw_only=True)
class Event:
    name: str
    handler_component: Optional[str] = field(default=None)
    handler_method: Optional[str] = field(default=None)
    raise_on_missing: Optional[bool] = field(default=False)
    actions: Optional[List[Action]] = field(default=None)

    async def handle(self, event: str, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs):
        checking_data = event_data
        if self.handler_component and self.handler_method:
            if await state_machine.component.check_external_registered(
                self.handler_component
            ):
                checking_data = await state_machine.component.exec_external_method(
                    self.handler_component,
                    self.handler_method,
                    {"event": event, "data": event_data},
                    auth_token=state_machine.auth_token,
                )
            else:
                msg = f"For event {event} handler component "
                msg += f"{self.handler_component} is not registered"
                if self.raise_on_missing:
                    raise ReferenceError(msg)
                logger.warning(msg)

        await asyncio.gather(*[action.perform(state_machine, frames, checking_data) for action in self.actions])

        return checking_data


@dataclass(kw_only=True)
class Diagram:
    states: List[State]
    transitions: List[Transition]
    events: List[Event]
    initial_attributes: Optional[Dict[str, Any]] = field(default_factory=dict)

    @property
    def annotation(self):
        return {
            "states": [state.annotation for state in self.states],
            "transitions": [transition.annotation for transition in self.transitions],
            "initial": next(
                (state.annotation for state in self.states if state.initial), None
            ),
        }

    def get_state(self, name: str) -> Union[State, None]:
        return next((state for state in self.states if state.name == name), None)

    def get_transition(self, name: str) -> Union[Transition, None]:
        return next(
            (transition for transition in self.transitions if transition.name == name),
            None,
        )

    def get_state_exit_transitions(self, state: Union[str, State]) -> List[Transition]:
        if isinstance(state, State):
            state = state.annotation

        return [
            transition
            for transition in self.transitions
            if transition.annotation["source"] == state
        ]

    def get_state_enter_transitions(self, state: Union[str, State]) -> List[Transition]:
        if isinstance(state, State):
            state = state.annotation

        return [
            transition
            for transition in self.transitions
            if transition.annotation["dest"] == state
        ]

    def get_state_all_transitions(self, state: Union[str, State]) -> List[Transition]:
        return self.get_state_exit_transitions(
            state
        ) + self.get_state_enter_transitions(state)

    def get_event(self, name: str) -> Union[Event, None]:
        return next((event for event in self.events if event.name == name), None)
