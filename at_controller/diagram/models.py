from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    Field,
    RootModel,
    ValidationError,
    field_validator,
    model_validator,
)
from yaml import safe_load

from at_controller.diagram.state import (
    AndCondition,
    AuthToken,
    BinaryOperationCondition,
    Diagram,
    EquatationCondition,
    EventTransition,
    Frame,
    FrameHandlerTransition,
    FrameUrl,
    GetAttribute,
    InclusionCondition,
    LinkTransition,
    NonArgOperationCondition,
    NotCondition,
    OrCondition,
    SetAttributeAction,
    State,
)


class FrameModel(BaseModel):
    src: str
    redirect: Optional[str] = Field(default=None)
    redirect_param: Optional[str] = Field(default="to")
    frame_id_param: Optional[str] = Field(default="frame_id")
    type: Optional[str] = Field(default="basic")
    span: Optional[Union[int, str]] = Field(default="auto")

    @field_validator("type")
    def validate_type(cls, value):
        if value not in ["basic", "format_attributes"]:
            raise ValueError("Invalid frame type")
        return value


class FrameRowModel(RootModel[Dict[str, Union[str, FrameModel]]]):
    @classmethod
    def from_dict(cls, frame_row_dict: Dict[str, Any]):
        frame_row = FrameRowModel(**frame_row_dict)
        return [
            Frame(frame_id=frame_id, **cls._build_frame(frame_data).model_dump())
            for frame_id, frame_data in frame_row.root.items()
        ]

    @staticmethod
    def _build_frame(frame: Union[FrameModel, str]):
        if isinstance(frame, str):
            return FrameModel(src=frame)
        return frame


# Определяем модели для State
class StateModel(BaseModel):
    label: Optional[str]
    frame_rows: Union[FrameRowModel, List[FrameRowModel]]
    control_label: Optional[str] = Field(default=None)
    control_subtitle: Optional[str] = Field(default=None)
    translation: Optional[str] = Field(default=None)
    initial: Optional[bool] = Field(default=False)


class States(RootModel[Dict[str, StateModel]]):
    @classmethod
    def from_dict(cls, states_dict: Dict[str, Any]):
        states = cls(states_dict)
        return [
            State(name=name, **cls._build_frame_rows(state.model_dump()))
            for name, state in states.root.items()
        ]

    @staticmethod
    def _build_frame_rows(state: Dict):
        state_model = StateModel(**state)
        frame_rows = state_model.frame_rows
        if isinstance(frame_rows, FrameRowModel):
            frame_rows = [frame_rows]
        state["frame_rows"] = [
            FrameRowModel.from_dict(frame_row.model_dump()) for frame_row in frame_rows
        ]
        return state


class SetAttributeBody(BaseModel):
    attribute: str
    value: Union[
        str,
        int,
        float,
        bool,
        "GetAttributeModel",
        "FrameUrlModel",
        "AuthTokenModel",
        List,
        Dict,
    ]
    next: Optional[List[Dict[str, Any]]] = Field(
        default=None
    )  # Параметры действий, которые могут быть сложными


class SetAttributeActionModel(BaseModel):
    set_attribute: SetAttributeBody

    @classmethod
    def from_dict(cls, action_dict: Dict[str, Any]):
        return SetAttributeAction(
            type="set_attribute",
            **cls._build_functions(
                SetAttributeBody(**action_dict["set_attribute"]).model_dump()
            )
        )

    @staticmethod
    def _build_functions(action_body: Dict):
        body = SetAttributeBody(**action_body)
        if isinstance(body.value, GetAttributeModel):
            action_body["value"] = GetAttributeModel.from_dict(body.value.model_dump())
        elif isinstance(body.value, FrameUrlModel):
            action_body["value"] = FrameUrlModel.from_dict(body.value.model_dump())
        elif isinstance(body.value, AuthTokenModel):
            action_body["value"] = AuthTokenModel.from_dict(body.value.model_dump())
        return action_body


class TransitionModel(BaseModel):
    source: str
    dest: str
    actions: Optional[List[SetAttributeActionModel]] = Field(default=None)
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
    type: Literal["eq", "ne", "gt", "gte", "lt", "lte"]
    value: Any

    def to_internal(self) -> "EquatationCondition":
        return EquatationCondition(type=self.type, value=self.value)


class InclusionConditionModel(BaseModel):
    type: Literal["in", "not_in", "includes", "not_includes"]
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
        ]
    ]

    def to_internal(self) -> "AndCondition":
        return AndCondition(
            type="and", arguments=[cond.to_internal() for cond in self.conditions]
        )


class OrConditionModel(BaseModel):
    type: Literal["or"]
    conditions: List[
        Union[
            "EquatationConditionModel",
            "InclusionConditionModel",
            "AndConditionModel",
            "OrConditionModel",
            "NotConditionModel",
        ]
    ]

    def to_internal(self) -> "OrCondition":
        return OrCondition(
            type="or", arguments=[cond.to_internal() for cond in self.conditions]
        )


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
    type: Literal[
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
    condition: Optional[
        Union[
            "EquatationConditionModel",
            "InclusionConditionModel",
            "AndConditionModel",
            "OrConditionModel",
            "NotConditionModel",
        ]
    ] = None

    @model_validator(mode="before")
    def parse_conditions(cls, values):
        if values.get("condition"):
            values["condition"] = EventTransitionModel.parse_condition(
                values["condition"]
            )
        return values

    def to_internal(self) -> "NonArgOperationCondition":
        return NonArgOperationCondition(
            type=self.type,
            condition=self.condition.to_internal() if self.condition else None,
        )


class BinaryOperationConditionModel(BaseModel):
    type: Literal[
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
    ]
    argument: Any
    condition: Optional[
        Union[
            "EquatationConditionModel",
            "InclusionConditionModel",
            "AndConditionModel",
            "OrConditionModel",
            "NotConditionModel",
        ]
    ] = None

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
    handler_component: Optional[str]
    handler_method: Optional[str]
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
    actions: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="before")
    def parse_conditions(cls, values):
        condition_data = values.get("trigger_condition")
        if condition_data:
            values["trigger_condition"] = cls.parse_condition(condition_data)
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
        cond_type = next(iter(data))  # Извлекаем первый ключ

        # Проверка на операционные условия (NonArg и BinaryOperation)
        if cond_type in NonArgOperationConditionModel:
            return NonArgOperationConditionModel(
                type=cond_type, condition=cls.parse_condition(data.get("condition", {}))
            )
        elif type in type(BinaryOperationConditionModel.type):
            return BinaryOperationConditionModel(
                type=type,
                argument=data[type],
                condition=cls.parse_condition(data.get("condition", {})),
            )

        # Логические условия (and, or, not)
        if "and" in data:
            return AndConditionModel(
                type="and",
                conditions=[cls.parse_condition(cond) for cond in data["and"]],
            )
        elif "or" in data:
            return OrConditionModel(
                type="or", conditions=[cls.parse_condition(cond) for cond in data["or"]]
            )
        elif "not" in data:
            return NotConditionModel(
                type="not", condition=cls.parse_condition(data["not"])
            )

        # Условия включения (in, not_in, includes, not_includes)
        if any(k in data for k in ["in", "not_in", "includes", "not_includes"]):
            return InclusionConditionModel(type=type, value=data[type])

        # Обычные уравнительные условия (eq, ne, gt, gte, lt, lte)
        return EquatationConditionModel(type=type, value=data[type])


class Transitions(
    RootModel[
        Dict[
            str,
            Union[
                LinkTransitionModel, FrameHandlerTransitionModel, EventTransitionModel
            ],
        ]
    ]
):
    @classmethod
    def from_dict(cls, transitions_dict: Dict[str, Any]):
        transitions = cls(transitions_dict)
        return [
            LinkTransition(name=name, **cls._build_actions(transition))
            if isinstance(transition, LinkTransitionModel) and transition.type == "link"
            else FrameHandlerTransition(name=name, **cls._build_actions(transition))
            if isinstance(transition, FrameHandlerTransitionModel)
            and transition.type == "frame_handler"
            else EventTransition(name=name, **cls._build_actions(transition))
            for name, transition in transitions.root.items()
        ]

    @staticmethod
    def _build_actions(
        transition: Union[
            LinkTransitionModel, FrameHandlerTransitionModel, EventTransitionModel
        ]
    ):
        transition_body = transition.model_dump()
        if isinstance(transition, EventTransitionModel):
            transition_body[
                "trigger_condition"
            ] = transition.trigger_condition.to_internal()
        return {
            **transition_body,
            "actions": [
                SetAttributeActionModel.from_dict(action_body)
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
            return {
                "kwargs": GetAttributeBodyModel(
                    attribute=function_dict["get_attribute"]
                ).model_dump()
            }
        return {
            "kwargs": GetAttributeBodyModel(
                **function_dict["get_attribute"]
            ).model_dump()
        }


class FrameUrlBodyModel(BaseModel):
    frame_id: str


class ParseBodyModel(BaseModel):
    regexp: str
    group: Optional[int]


class FrameUrlParseBody(FrameUrlBodyModel):
    parse: Union[str, ParseBodyModel]


class QueryBodyModel(BaseModel):
    param: str
    index: Optional[int]


class FrameUrlQueryBody(FrameUrlBodyModel):
    query_param: Union[str, QueryBodyModel]


# Определяем модель для FrameUrl
class FrameUrlModel(BaseModel):
    frame_url: Union[FrameUrlParseBody, FrameUrlQueryBody, FrameUrlBodyModel]

    @classmethod
    def from_dict(cls, function_dict: Dict[str, Any]):
        return FrameUrl(name="frame_url", **cls._build_kwargs(function_dict))

    @staticmethod
    def _build_kwargs(function_dict):
        if isinstance(function_dict["frame_url"], str):
            return {
                "kwargs": FrameUrlBodyModel(
                    frame_id=function_dict["frame_url"]
                ).model_dump()
            }

        if "parse" in function_dict["frame_url"]:
            if isinstance(function_dict["frame_url"]["parse"], str):
                return {
                    "kwargs": FrameUrlParseBody(
                        frame_id=function_dict["frame_url"]["frame_id"],
                        parse=ParseBodyModel(
                            regexp=function_dict["frame_url"]["parse"]
                        ),
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
                        query_param=QueryBodyModel(
                            param=function_dict["frame_url"]["query_param"]
                        ).model_dump(),
                    )
                }

            return {
                "kwargs": FrameUrlQueryBody(
                    frame_id=function_dict["frame_url"]["frame_id"],
                    query_param=QueryBodyModel(
                        **function_dict["frame_url"]["query_param"]
                    ),
                ).model_dump()
            }

        return {"kwargs": FrameUrlBodyModel(**function_dict["frame_url"]).model_dump()}


class AuthTokenModel(BaseModel):
    auth_token: Dict[str, Any]

    @classmethod
    def from_dict(cls, function_dict: Dict[str, Any]):
        return AuthToken(name="auth_token", kwargs={})


class DiagramModel(BaseModel):
    states: States
    transitions: Transitions

    @classmethod
    def from_dict(cls, diagram_dict: Dict[str, Any]):
        states = States.from_dict(diagram_dict["states"])
        transitions = Transitions.from_dict(diagram_dict["transitions"])
        return Diagram(states=states, transitions=transitions)


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
