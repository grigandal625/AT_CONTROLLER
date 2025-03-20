from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic import RootModel
from pydantic import ValidationError
from yaml import safe_load

from at_controller.diagram.state.actions import ExecMethodAction
from at_controller.diagram.state.actions import SetAttributeAction
from at_controller.diagram.state.actions import ShowMessageAction
from at_controller.diagram.state.conditions import AndCondition
from at_controller.diagram.state.conditions import BinaryOperationCondition
from at_controller.diagram.state.conditions import BinaryType
from at_controller.diagram.state.conditions import EquatationCondition
from at_controller.diagram.state.conditions import EquatationType
from at_controller.diagram.state.conditions import InclusionCondition
from at_controller.diagram.state.conditions import InclusionType
from at_controller.diagram.state.conditions import NonArgOperationCondition
from at_controller.diagram.state.conditions import NonArgType
from at_controller.diagram.state.conditions import NotCondition
from at_controller.diagram.state.conditions import OrCondition
from at_controller.diagram.state.diagram import Diagram
from at_controller.diagram.state.events import Event
from at_controller.diagram.state.functions import AndFunction
from at_controller.diagram.state.functions import AuthToken
from at_controller.diagram.state.functions import BinaryFunction
from at_controller.diagram.state.functions import BinaryFuncType
from at_controller.diagram.state.functions import EventData
from at_controller.diagram.state.functions import FrameUrl
from at_controller.diagram.state.functions import FrameUrlArg
from at_controller.diagram.state.functions import GetAttribute
from at_controller.diagram.state.functions import OrFunction
from at_controller.diagram.state.functions import UnaryFunction
from at_controller.diagram.state.functions import UnaryFuncType
from at_controller.diagram.state.states import Frame
from at_controller.diagram.state.states import State
from at_controller.diagram.state.transitions import EventTransition
from at_controller.diagram.state.transitions import FrameHandlerTransition
from at_controller.diagram.state.transitions import LinkTransition


class FrameModel(BaseModel):
    src: str
    redirect: Optional[str] = Field(default=None)
    redirect_param: Optional[str] = Field(default="to")
    frame_id_param: Optional[str] = Field(default="frame_id")
    type: Literal["basic", "format_attributes"] = Field(default="basic")
    span: Optional[Union[int, str]] = Field(default="auto")

    def to_internal(self, **kwargs):
        data = self.model_dump()
        data.update(kwargs)
        return Frame(**data)


class FrameRowModel(RootModel[Dict[str, Union[str, FrameModel]]]):
    def to_internal(self, **kwargs):
        result = []
        for key, value in self.root.items():
            if isinstance(value, str):
                value = FrameModel(src=value)
            result.append(value.to_internal(frame_id=key))
        return result


# Определяем модели для State
class StateModel(BaseModel):
    label: Optional[str]
    frame_rows: Union[FrameRowModel, List[FrameRowModel]]
    control_label: Optional[str] = Field(default=None)
    control_subtitle: Optional[str] = Field(default=None)
    translation: Optional[str] = Field(default=None)
    initial: Optional[bool] = Field(default=False)

    def to_internal(self, **kwargs):
        data = self.model_dump()
        data.update(kwargs)
        if isinstance(self.frame_rows, FrameRowModel):
            data["frame_rows"] = [self.frame_rows.to_internal()]
        else:
            data["frame_rows"] = [row.to_internal() for row in self.frame_rows]
        return State(**data)


class States(RootModel[Dict[str, StateModel]]):
    def to_internal(self, **kwargs):
        result = []
        for key, value in self.root.items():
            result.append(value.to_internal(name=key))
        return result


ActionValueType = Union[
    None,
    str,
    int,
    float,
    bool,
    "GetAttributeModel",
    "FrameUrlModel",
    "AuthTokenModel",
    "EventDataModel",
    "LogicalFunctionModel",
    "UnaryFunctionModel",
    "BinaryFunctionModel",
    List,
    Dict,
]


class SetAttributeBody(BaseModel):
    attribute: str
    value: ActionValueType
    next: Optional[List[Union["SetAttributeActionModel", "ShowMessageActionModel"]]] = Field(
        default=None
    )  # Параметры действий, которые могут быть сложными


class ShowMessageBody(BaseModel):
    message: str
    title: Optional[str] = Field(default="")
    modal: Optional[bool] = Field(default=True)
    message_type: Optional[str] = Field(default="info")

    next: Optional[List[Union["SetAttributeActionModel", "ShowMessageActionModel"]]] = Field(
        default=None
    )  # Параметры действий, которые могут быть сложными


class ShowMessageActionModel(BaseModel):
    show_message: ShowMessageBody

    @classmethod
    def from_dict(cls, action_dict: Dict[str, Any]):
        body = ShowMessageBody(**action_dict["show_message"])
        nxt = []
        if body.next:
            for i, n in enumerate(body.next):
                nxt.append(n.from_dict(action_dict["set_attribute"]["next"][i]))

        return ShowMessageAction(
            type="show_message",
            next=nxt,
            message=body.message,
            message_type=body.message_type,
            title=body.title,
            modal=body.modal,
        )


class SimpleSetAttributeBody(RootModel[Dict[str, ActionValueType]]):
    pass


class SetAttributeActionModel(BaseModel):
    set_attribute: Union[SetAttributeBody, SimpleSetAttributeBody]

    @classmethod
    def from_dict(cls, action_dict: Dict[str, Any]):
        set_attribute = cls(**action_dict)

        body = set_attribute.set_attribute

        if isinstance(body, SimpleSetAttributeBody):
            attribute = next(iter(body.root.keys()))
            value = next(iter(body.root.values()))
            return SetAttributeAction(
                type="set_attribute", **cls._build_functions({"attribute": attribute, "value": value})
            )

        nxt = []
        if body.next:
            for i, n in enumerate(body.next):
                nxt.append(n.from_dict(action_dict["set_attribute"]["next"][i]))

        return SetAttributeAction(
            type="set_attribute", **cls._build_functions({"value": body.value, "attribute": body.attribute}), next=nxt
        )

    @staticmethod
    def _build_functions(action_body: Dict):
        body = SetAttributeBody(**action_body)
        if internable(body.value):
            action_body["value"] = body.value.to_internal()
        return action_body


class ExecMethodActionModel(BaseModel):
    component: str
    method: str
    method_args: ActionValueType
    auth_token: Optional[str] = Field(default=None)

    @classmethod
    def from_dict(cls, action_dict: Dict[str, Any]):
        if internable(action_dict["method_args"]):
            action_dict["method_args"] = action_dict["method_args"].to_internal()
        return ExecMethodAction(**action_dict)


class TransitionModel(BaseModel):
    source: str
    dest: str
    actions: Optional[List[Union[SetAttributeActionModel, ShowMessageActionModel, ExecMethodActionModel]]] = Field(
        default=None
    )
    translation: Optional[str] = Field(default=None)


class LinkTransitionModel(TransitionModel):
    type: str = "link"
    label: str
    position: Optional[str] = Field(default="header")
    icon: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)

    @field_validator("position")
    def validate_position(cls, v):
        if v not in {"header", "footer", "control", None}:
            raise ValueError("position must be 'header', 'footer', 'control', or None")
        return v


class FrameHandlerTransitionModel(TransitionModel):
    type: str = "frame_handler"
    frame_id: str
    test: str
    tags: Optional[List[str]] = Field(default=None)


class EquatationConditionModel(BaseModel):
    type: EquatationType
    value: Any

    def to_internal(self) -> "EquatationCondition":
        return EquatationCondition(type=self.type, value=self.value)


class InclusionConditionModel(BaseModel):
    type: InclusionType
    value: Union[List[Any], Dict[Any, Any]]

    def to_internal(self) -> "InclusionCondition":
        return InclusionCondition(type=self.type, value=self.value)


# Логические условия
class AndConditionModel(BaseModel):
    type: Literal["and"]
    conditions: List[
        Union[
            "EquatationConditionModel",
            "InclusionConditionModel",
            "AndConditionModel",
            "OrConditionModel",
            "NotConditionModel",
            "NonArgOperationConditionModel",
            "BinaryOperationConditionModel",
        ]
    ]

    def to_internal(self) -> "AndCondition":
        return AndCondition(type="and", arguments=[cond.to_internal() for cond in self.conditions])


class OrConditionModel(BaseModel):
    type: Literal["or"]
    conditions: List[
        Union[
            "EquatationConditionModel",
            "InclusionConditionModel",
            "AndConditionModel",
            "OrConditionModel",
            "NotConditionModel",
            "NonArgOperationConditionModel",
            "BinaryOperationConditionModel",
        ]
    ]

    def to_internal(self) -> "OrCondition":
        return OrCondition(type="or", arguments=[cond.to_internal() for cond in self.conditions])


class NotConditionModel(BaseModel):
    type: Literal["not"]
    condition: Union[
        "EquatationConditionModel",
        "InclusionConditionModel",
        "AndConditionModel",
        "OrConditionModel",
        "NotConditionModel",
    ]

    def to_internal(self) -> "NotCondition":
        return NotCondition(condition=self.condition.to_internal())


# Операционные условия
class NonArgOperationConditionModel(BaseModel):
    type: NonArgType
    condition: Optional[
        Union[
            "EquatationConditionModel",
            "InclusionConditionModel",
            "AndConditionModel",
            "OrConditionModel",
            "NotConditionModel",
            "NonArgOperationConditionModel",
            "BinaryOperationConditionModel",
        ]
    ] = None

    @model_validator(mode="before")
    def parse_conditions(cls, values):
        if isinstance(values, dict):
            values["condition"] = EventTransitionModel.parse_condition(values.get("condition", {}))
        return values

    def to_internal(self) -> "NonArgOperationCondition":
        return NonArgOperationCondition(
            type=self.type,
            condition=self.condition.to_internal() if self.condition else None,
        )


class BinaryOperationConditionModel(BaseModel):
    type: BinaryType
    argument: Any
    condition: Optional[
        Union[
            "EquatationConditionModel",
            "InclusionConditionModel",
            "AndConditionModel",
            "OrConditionModel",
            "NotConditionModel",
            "NonArgOperationConditionModel",
            "BinaryOperationConditionModel",
        ]
    ] = None

    @model_validator(mode="before")
    def parse_conditions(cls, values):
        if isinstance(values, dict):
            values["condition"] = EventTransitionModel.parse_condition(values.get("condition", {}))
        return values

    def to_internal(self) -> "BinaryOperationCondition":
        return BinaryOperationCondition(
            type=self.type,
            argument=self.argument,
            condition=self.condition.to_internal() if self.condition else None,
        )


# Модель перехода событий
class EventTransitionModel(BaseModel):
    event: Optional[str] = Field(default=None)
    type: Literal["event"] = "event"
    source: str
    dest: str
    trigger_condition: Optional[
        Union[
            EquatationConditionModel,
            InclusionConditionModel,
            AndConditionModel,
            OrConditionModel,
            NotConditionModel,
            NonArgOperationConditionModel,
            BinaryOperationConditionModel,
        ]
    ]
    actions: Optional[List[Union[SetAttributeActionModel, ShowMessageActionModel]]] = Field(default=None)

    @model_validator(mode="before")
    def parse_conditions(cls, values):
        if isinstance(values, dict):
            condition_data = values.get("trigger_condition")
            condition_model = cls.parse_condition(condition_data)
            if condition_data:
                values["trigger_condition"] = condition_model
        return values

    @classmethod
    def parse_condition(
        cls, data: Dict[str, Any]
    ) -> Union[
        EquatationConditionModel,
        InclusionConditionModel,
        AndConditionModel,
        OrConditionModel,
        NotConditionModel,
        NonArgOperationConditionModel,
        BinaryOperationConditionModel,
    ]:
        if isinstance(data, BaseModel):
            return data
        if data is None:
            return None
        if isinstance(data, dict):
            if not len(data.keys()):
                return None
            cond_type = next(iter(data))  # Извлекаем первый ключ
        elif isinstance(data, str):
            cond_type = data
            data = {}

        # Проверка на операционные условия (NonArg и BinaryOperation)
        if cond_type in NonArgType.__args__:
            cond_body = data.get(cond_type)
            if isinstance(cond_body, dict):
                condition = cond_body.get("condition")
                if condition is None:
                    condition = cond_body or {}
            else:
                condition = {}
            return NonArgOperationConditionModel(type=cond_type, condition=cls.parse_condition(condition))
        elif cond_type in BinaryType.__args__:
            cond_body = data.get(cond_type)
            if isinstance(cond_body, dict):
                argument = cond_body.get("argument")
                condition = cond_body.get("condition")
                if argument is None:
                    argument = data[cond_type]
                    condition = {}
            else:
                argument = data[cond_type]
                condition = {}
            return BinaryOperationConditionModel(
                type=cond_type,
                argument=argument,
                condition=cls.parse_condition(condition),
            )

        # Логические условия (and, or, not)
        if "and" in data:
            conditions = [cls.parse_condition(cond) for cond in data["and"]]
            return AndConditionModel(
                type="and",
                conditions=conditions,
            )
        elif "or" in data:
            conditions = [cls.parse_condition(cond) for cond in data["or"]]
            return OrConditionModel(type="or", conditions=conditions)
        elif "not" in data:
            condition = cls.parse_condition(data["not"])
            return NotConditionModel(type="not", condition=condition)

        elif cond_type in InclusionType.__args__:
            return InclusionConditionModel(type=cond_type, value=data[cond_type])

        elif cond_type in EquatationType.__args__:
            return EquatationConditionModel(type=cond_type, value=data[cond_type])


class Transitions(
    RootModel[
        Dict[
            str,
            Union[LinkTransitionModel, FrameHandlerTransitionModel, EventTransitionModel],
        ]
    ]
):
    @classmethod
    def from_dict(cls, transitions_dict: Dict[str, Any]):
        transitions = cls(transitions_dict)
        return [
            (
                LinkTransition(name=name, **cls._build_actions(transition))
                if isinstance(transition, LinkTransitionModel) and transition.type == "link"
                else (
                    FrameHandlerTransition(name=name, **cls._build_actions(transition))
                    if isinstance(transition, FrameHandlerTransitionModel) and transition.type == "frame_handler"
                    else EventTransition(name=name, **cls._build_actions(transition))
                )
            )
            for name, transition in transitions.root.items()
        ]

    @staticmethod
    def _build_actions(transition: Union[LinkTransitionModel, FrameHandlerTransitionModel, EventTransitionModel]):
        transition_body = transition.model_dump()
        if isinstance(transition, EventTransitionModel):
            transition_body["trigger_condition"] = transition.trigger_condition.to_internal()
        return {
            **transition_body,
            "actions": [
                SetAttributeActionModel.from_dict(action_body)
                if next(iter(action_body.keys())) == "set_attribute"
                else ShowMessageActionModel.from_dict(action_body)
                if next(iter(action_body.keys())) == "show_message"
                else ExecMethodActionModel.from_dict(action_body)
                for action_body in transition_body.get("actions", [])
            ],
        }


class GetAttributeBodyModel(BaseModel):
    attribute: str


class GetAttributeModel(BaseModel):
    get_attribute: Union[str, GetAttributeBodyModel]

    @classmethod
    def from_dict(cls, function_dict: Dict[str, Any]):
        return GetAttribute(name="get_attribute", **cls._build_kwargs(function_dict))

    @staticmethod
    def _build_kwargs(function_dict):
        if isinstance(function_dict["get_attribute"], str):
            return {"kwargs": GetAttributeBodyModel(attribute=function_dict["get_attribute"]).model_dump()}
        return {"kwargs": GetAttributeBodyModel(**function_dict["get_attribute"]).model_dump()}

    def to_internal(self):
        if isinstance(self.get_attribute, str):
            return GetAttribute(name="get_attribute", kwargs={"attribute": self.get_attribute})
        if isinstance(self.get_attribute, GetAttributeBodyModel):
            return GetAttribute(name="get_attribute", kwargs=self.get_attribute.model_dump())


class FrameUrlBodyModel(BaseModel):
    frame_id: str

    def to_internal(self):
        return self.model_dump()


class ParseBodyModel(BaseModel):
    regexp: str
    group: Optional[int]


class FrameUrlParseBody(FrameUrlBodyModel):
    parse: Union[str, ParseBodyModel]

    def to_internal(self):
        result = super().to_internal()
        if isinstance(self.parse, str):
            result.update({"parse": {"regexp": self.parse}})
        return result


class QueryBodyModel(BaseModel):
    param: str
    index: Optional[int]


class FrameUrlQueryBody(FrameUrlBodyModel):
    query_param: Union[str, QueryBodyModel]

    def to_internal(self):
        result = super().to_internal()
        if isinstance(self.query_param, str):
            result.update({"query_param": {"param": self.query_param}})
        return result


class FrameUrlModel(BaseModel):
    frame_url: Union[FrameUrlParseBody, FrameUrlQueryBody, FrameUrlBodyModel]

    @classmethod
    def from_dict(cls, function_dict: Dict[str, Any]):
        return FrameUrl(name="frame_url", **cls._build_kwargs(function_dict))

    @staticmethod
    def _build_kwargs(function_dict):
        if isinstance(function_dict["frame_url"], str):
            return {"kwargs": FrameUrlBodyModel(frame_id=function_dict["frame_url"]).model_dump()}

        if "parse" in function_dict["frame_url"]:
            if isinstance(function_dict["frame_url"]["parse"], str):
                return {
                    "kwargs": FrameUrlParseBody(
                        frame_id=function_dict["frame_url"]["frame_id"],
                        parse=ParseBodyModel(regexp=function_dict["frame_url"]["parse"]),
                    ).model_dump()
                }

            return {
                "kwargs": FrameUrlParseBody(
                    frame_id=function_dict["frame_url"]["frame_id"],
                    parse=ParseBodyModel(**function_dict["frame_url"]["parse"]),
                ).model_dump()
            }

        if "query_param" in function_dict["frame_url"]:
            if isinstance(function_dict["frame_url"]["query_param"], str):
                return {
                    "kwargs": FrameUrlQueryBody(
                        frame_id=function_dict["frame_url"]["frame_id"],
                        query_param=QueryBodyModel(param=function_dict["frame_url"]["query_param"]).model_dump(),
                    )
                }

            return {
                "kwargs": FrameUrlQueryBody(
                    frame_id=function_dict["frame_url"]["frame_id"],
                    query_param=QueryBodyModel(**function_dict["frame_url"]["query_param"]),
                ).model_dump()
            }

        return {"kwargs": FrameUrlBodyModel(**function_dict["frame_url"]).model_dump()}

    def to_internal(self):
        kwargs: FrameUrlArg = {}
        if isinstance(self.frame_url, str):
            kwargs["frame_id"] = self.frame_url
        else:
            kwargs = self.frame_url.to_internal()
        return FrameUrl(name="frame_url", kwargs=kwargs)


class AuthTokenModel(BaseModel):
    auth_token: Dict[str, Any]

    @classmethod
    def from_dict(cls, function_dict: Dict[str, Any]):
        return AuthToken(name="auth_token", kwargs={})

    def to_internal(self):
        return AuthToken(name="auth_token", kwargs={})


class EventDataModel(BaseModel):
    event_data: List[str]

    @classmethod
    def from_dict(cls, function_dict: Union[Literal["event_data"], Dict[Literal["event_data"], Any]]):
        if isinstance(function_dict, str):
            EventData(name="event_data", kwargs={"key_path": []})
        return EventData(name="event_data", kwargs={"key_path": function_dict.get("event_data", [])})

    def to_internal(self):
        return EventData(name="event_data", kwargs={"key_path": self.event_data})


class LogicalFunctionModel(RootModel[Dict[str, List[ActionValueType]]]):
    @model_validator(mode="before")
    def check_key(cls, values):
        if isinstance(values, dict):
            first_key = next(iter(values.keys()), None)
            if first_key not in ["and", "or"]:
                raise ValueError(f'Key must be "and" or "or" but got "{first_key}"')
        return values

    @classmethod
    def from_dict(cls, logical_function_dict: Dict[str, List[ActionValueType]]):
        first_key = next(iter(logical_function_dict.keys()), None)
        data = cls(logical_function_dict)

        items = [SetAttributeActionModel._build_functions({"value": {k: v}})["value"] for k, v in data.root.items()]

        if first_key == "and":
            return AndFunction(name="and", kwargs={"items": items})
        if first_key == "or":
            return OrFunction(name="or", kwargs={"items": items})

    def to_internal(self):
        first_key = next(iter(self.root.keys()), None)
        FunctionClass = {"and": AndFunction, "or": OrFunction}[first_key]

        return FunctionClass(
            name=first_key, kwargs={"items": [v.to_internal() if internable(v) else v for v in self.root[first_key]]}
        )


class UnaryFunctionModel(RootModel[Dict[str, ActionValueType]]):
    @model_validator(mode="before")
    def check_key(cls, values):
        if isinstance(values, dict):
            first_key = next(iter(values.keys()), None)
            if first_key not in UnaryFuncType.__args__:
                raise ValueError(f'Key must be one of {UnaryFuncType.__args__} but got "{first_key}"')
        return values

    @classmethod
    def from_dict(cls, unary_function_dict: Dict[str, List[ActionValueType]]):
        first_key = next(iter(unary_function_dict.keys()), None)
        data = cls(unary_function_dict)

        kwargs = SetAttributeActionModel._build_functions({"value": data.root})

        return UnaryFunction(name=first_key, kwargs=kwargs)

    def to_internal(self):
        first_key = next(iter(self.root.keys()), None)
        return UnaryFunction(
            name=first_key,
            kwargs={
                "value": self.root[first_key].to_internal()
                if internable(self.root[first_key])
                else self.root[first_key]
            },
        )


class BinaryFunctionBody(BaseModel):
    left_value: ActionValueType
    right_value: ActionValueType


class BinaryFunctionModel(RootModel[Dict[str, BinaryFunctionBody]]):
    @model_validator(mode="before")
    def check_key(cls, values):
        if isinstance(values, dict):
            first_key = next(iter(values.keys()), None)
            if first_key not in BinaryFuncType.__args__:
                raise ValueError(f'Key must be one of {BinaryFuncType.__args__} but got "{first_key}"')
        return values

    @classmethod
    def from_dict(cls, binary_function_dict: Dict[str, Any]):
        first_key = next(iter(binary_function_dict.keys()), None)
        data = cls(binary_function_dict)

        left_value = SetAttributeActionModel._build_functions({"value": data.root[first_key]["left_value"]})["value"]
        right_value = SetAttributeActionModel._build_functions({"value": data.root[first_key]["right_value"]})["value"]

        return BinaryFunction(name=first_key, kwargs={"left_value": left_value, "right_value": right_value})

    def to_internal(self):
        first_key = next(iter(self.root.keys()), None)
        return BinaryFunction(
            name=first_key,
            kwargs={
                "left_value": self.root[first_key].left_value.to_internal()
                if internable(self.root[first_key].left_value)
                else self.root[first_key].left_value,
                "right_value": self.root[first_key].right_value.to_internal()
                if internable(self.root[first_key].right_value)
                else self.root[first_key].right_value,
            },
        )


class EventModel(BaseModel):
    handler_component: Optional[str] = Field(default=None)
    handler_method: Optional[str] = Field(default=None)
    raise_on_missing: Optional[bool] = Field(default=False)
    actions: Optional[List[Union[SetAttributeActionModel, ShowMessageActionModel]]] = Field(default=None)


class Events(RootModel[Dict[str, EventModel]]):
    @classmethod
    def from_dict(cls, events_dict: Dict[str, Any]):
        events = cls(events_dict)
        return [
            Event(
                name=name,
                handler_component=event.handler_component,
                handler_method=event.handler_method,
                actions=[a.from_dict(events_dict[name]["actions"][i]) for i, a in enumerate(event.actions or [])],
            )
            for name, event in events.root.items()
        ]


class InitialAttributesModel(RootModel[Dict[str, Any]]):
    pass


INTERNABLE_FUNCTIONS = [
    GetAttributeModel,
    FrameUrlModel,
    AuthTokenModel,
    EventDataModel,
    LogicalFunctionModel,
    UnaryFunctionModel,
    BinaryFunctionModel,
]


def internable(f):
    return any([isinstance(f, c) for c in INTERNABLE_FUNCTIONS])


class DiagramModel(BaseModel):
    states: States
    transitions: Transitions
    events: Events
    initial_attributes: Optional[InitialAttributesModel] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, diagram_dict: Dict[str, Any]):
        states = States.from_dict(diagram_dict["states"])
        transitions = Transitions.from_dict(diagram_dict["transitions"])
        events = Events.from_dict(diagram_dict.get("events", {}))
        initial_attributes = diagram_dict.get("initial_attributes", {})
        return Diagram(states=states, transitions=transitions, events=events, initial_attributes=initial_attributes)


# Пример использования
if __name__ == "__main__":
    try:
        with open("src/scenario.yaml", "r") as file:
            diagram_dict = safe_load(file)

        # Валидация и создание экземпляра Diagram с сериализацией
        diagram = DiagramModel.from_dict(diagram_dict)
        print(diagram)

    except ValidationError as e:
        print(e.json(indent=4))
