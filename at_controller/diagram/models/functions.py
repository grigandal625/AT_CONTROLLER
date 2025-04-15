from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
from pydantic import RootModel
from pydantic import ValidationError

from at_controller.diagram.state.functions import AndFunction
from at_controller.diagram.state.functions import AuthToken
from at_controller.diagram.state.functions import BinaryFunction
from at_controller.diagram.state.functions import BinaryFuncType
from at_controller.diagram.state.functions import EventData
from at_controller.diagram.state.functions import FrameUrl
from at_controller.diagram.state.functions import FrameUrlArg
from at_controller.diagram.state.functions import GetAttribute
from at_controller.diagram.state.functions import InitialEventData
from at_controller.diagram.state.functions import OrFunction
from at_controller.diagram.state.functions import UnaryFunction
from at_controller.diagram.state.functions import UnaryFuncType


class FunctionModel(BaseModel):
    @staticmethod
    def build_functions(arg: "ActionValueType"):
        if isinstance(arg, list):
            return [FunctionModel.build_functions(item) for item in arg]
        elif isinstance(arg, dict):
            return {key: FunctionModel.build_functions(value) for key, value in arg.items()}
        elif isinstance(arg, FunctionModel):
            return arg.to_internal()
        else:
            return arg

    @staticmethod
    def find_function_models(data):
        if isinstance(data, list):
            return [FunctionModel.find_function_models(item) for item in data]
        if isinstance(data, dict):
            try:
                return ExplicitFunctionModel(root=data)
            except ValidationError:
                return {key: FunctionModel.find_function_models(value) for key, value in data.items()}
        if isinstance(data, str):
            try:
                return ExplicitFunctionModel(root=data)
            except ValidationError:
                return data
        return data

    def to_internal(self, **kwargs):
        raise NotImplementedError("Not implemented")


class GetAttributeModel(FunctionModel):
    get_attribute: "ActionValueType"

    def to_internal(self, **kwargs):
        data = {"kwargs": {"attribute": self.build_functions(self.get_attribute)}}
        return GetAttribute(**data)


class FrameUrlBodyModel(BaseModel):
    frame_id: "ActionValueType"

    def to_internal(self, **kwargs):
        result = self.model_dump()
        result["frame_id"] = FunctionModel.build_functions(self.frame_id)
        return result


class ParseBodyModel(BaseModel):
    regexp: "ActionValueType"
    group: Optional["ActionValueType"] = Field(default=None)

    def to_internal(self, **kwargs):
        result = self.model_dump()
        result["regexp"] = FunctionModel.build_functions(self.regexp)
        if self.group:
            result["group"] = FunctionModel.build_functions(self.group)
        return result


class FrameUrlParseBody(FrameUrlBodyModel):
    parse: Union[ParseBodyModel, "ActionValueType"]

    def to_internal(self, **kwargs):
        result = super().to_internal()
        if isinstance(self.parse, ParseBodyModel):
            result["parse"] = self.parse.to_internal()
        else:
            result["parse"] = {"regexp": self.parse}
        return result


class QueryBodyModel(BaseModel):
    param: "ActionValueType"
    index: Optional["ActionValueType"] = Field(default=None)

    def to_internal(self, **kwargs):
        result = self.model_dump()
        result["param"] = FunctionModel.build_functions(self.param)
        if self.index:
            result["index"] = FunctionModel.build_functions(self.index)
        return result


class FrameUrlQueryBody(FrameUrlBodyModel):
    query_param: Union[QueryBodyModel, "ActionValueType"]

    def to_internal(self, **kwargs):
        result = super().to_internal()
        if isinstance(self.query_param, QueryBodyModel):
            result["query_param"] = self.query_param.to_internal()
        else:
            result["query_param"] = {"param": self.query_param}
        return result


class FrameUrlModel(FunctionModel):
    frame_url: Union[str, FrameUrlParseBody, FrameUrlQueryBody, FrameUrlBodyModel]

    def to_internal(self):
        kwargs: FrameUrlArg = {}
        if isinstance(self.frame_url, str):
            kwargs["frame_id"] = self.frame_url
        else:
            kwargs = self.frame_url.to_internal()
        return FrameUrl(name="frame_url", kwargs=kwargs)


class AuthTokenInternalModel(BaseModel):
    auth_token: Literal["$"]

    def to_internal(self):
        return AuthToken(name="auth_token", kwargs={})


class AuthTokenModel(RootModel[Union[Literal["$auth_token"], AuthTokenInternalModel]], FunctionModel):
    def to_internal(self, **kwargs):
        return AuthToken(name="auth_token", kwargs={})


class EventDataInternalModel(FunctionModel):
    event_data: Union[List[Union[str, int, float]], Literal["$"]]

    def to_internal(self):
        return EventData(
            name="event_data", kwargs={"key_path": self.event_data if isinstance(self.event_data, list) else []}
        )


class EventDataModel(RootModel[Union[Literal["$event_data"], EventDataInternalModel]], FunctionModel):
    def to_internal(self):
        if isinstance(self.root, str):
            return EventData(name="event_data", kwargs={"key_path": []})
        return self.root.to_internal()


class InitialEventDataInternalModel(FunctionModel):
    initial_event_data: Union[List[Union[str, int, float]], Literal["$"]]

    def to_internal(self):
        return InitialEventData(
            name="initial_event_data", kwargs={"key_path": self.event_data if isinstance(self.event_data, list) else []}
        )


class InitialEventDataModel(
    RootModel[Union[Literal["$initial_event_data"], InitialEventDataInternalModel]], FunctionModel
):
    def to_internal(self):
        if isinstance(self.root, str):
            return InitialEventData(name="initial_event_data", kwargs={"key_path": []})
        return self.root.to_internal()


class LogicalFunctionModel(RootModel[Dict[Literal["and", "or"], List["ActionValueType"]]], FunctionModel):
    @model_validator(mode="before")
    def check_key(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Logical operation must contain only one key")
        return values

    def to_internal(self):
        first_key = next(iter(self.root.keys()), None)
        FunctionClass = {"and": AndFunction, "or": OrFunction}[first_key]

        return FunctionClass(
            name=first_key, kwargs={"items": [FunctionModel.build_functions(v) for v in self.root[first_key]]}
        )


class UnaryFunctionModel(RootModel[Dict[UnaryFuncType, "ActionValueType"]], FunctionModel):
    @model_validator(mode="before")
    def check_key(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Unary operationmust contain only one key")
        return values

    def to_internal(self):
        first_key = next(iter(self.root.keys()), None)
        return UnaryFunction(
            name=first_key,
            kwargs={"value": self.build_functions(self.root[first_key])},
        )


class BinaryFunctionBody(BaseModel):
    left_value: "ActionValueType"
    right_value: "ActionValueType"

    def to_internal(self, **kwargs):
        data = self.model_dump()
        data["left_value"] = FunctionModel.build_functions(self.left_value)
        data["right_value"] = FunctionModel.build_functions(self.right_value)
        return data


class BinaryFunctionModel(RootModel[Dict[BinaryFuncType, BinaryFunctionBody]], FunctionModel):
    @model_validator(mode="before")
    def check_key(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Binary operation must contain only one key")
        return values

    def to_internal(self, **kwargs):
        first_key = next(iter(self.root.keys()), None)
        return BinaryFunction(
            name=first_key,
            kwargs=self.root[first_key].to_internal(),
        )


class PerhapsInnerFunctions(RootModel[Union[List, Dict, str]], FunctionModel):
    @model_validator(mode="before")
    @classmethod
    def check_inner_functions(cls, values):
        return cls.find_function_models(values)

    def to_internal(self, **kwargs):
        return self.build_functions(self.root)


class PrimitiveModel(RootModel[Union[None, int, float, str, bool]], FunctionModel):
    @model_validator(mode="before")
    @classmethod
    def check_inner_functions(cls, values):
        if isinstance(cls.find_function_models(values), FunctionModel):
            raise ValueError("Primitive value cannot contain function models")
        return values

    def to_internal(self, **kwargs):
        return self.root


ExplicitFunctionModels = Union[
    GetAttributeModel,
    FrameUrlModel,
    AuthTokenModel,
    EventDataModel,
    InitialEventDataModel,
    LogicalFunctionModel,
    UnaryFunctionModel,
    BinaryFunctionModel,
]

ActionValueType = Union[
    ExplicitFunctionModels,
    PerhapsInnerFunctions,
    PrimitiveModel,
]

GetAttributeModel.model_rebuild()
FrameUrlModel.model_rebuild()
AuthTokenModel.model_rebuild()
EventDataModel.model_rebuild()
InitialEventDataModel.model_rebuild()
LogicalFunctionModel.model_rebuild()
UnaryFunctionModel.model_rebuild()
BinaryFunctionModel.model_rebuild()


class ExplicitFunctionModel(RootModel[ExplicitFunctionModels], FunctionModel):
    def to_internal(self):
        return self.root.to_internal()
