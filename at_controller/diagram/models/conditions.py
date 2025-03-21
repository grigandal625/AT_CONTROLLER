from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
from pydantic import RootModel

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


class EquatationConditionModel(RootModel[Dict[EquatationType, Any]]):
    @model_validator(mode="before")
    def validate_keys(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Equatation condition must contain only one key-value pair")
        return values

    def to_internal(self) -> "EquatationCondition":
        type = next(iter(self.root.keys()))
        return EquatationCondition(type=type, value=self.root[type])


class InclusionConditionModel(RootModel[Dict[InclusionType, Union[List[Any], Dict[str, Any]]]]):
    @model_validator(mode="before")
    def validate_keys(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Inclusion condition must contain only one key-value pair")
        return values

    def to_internal(self) -> "InclusionCondition":
        type = next(iter(self.root.keys()))
        return InclusionCondition(type=type, value=self.root[type])


# Логические условия
class AndConditionModel(RootModel[Dict[Literal["and"], List["AllConditionModels"]]]):
    @model_validator(mode="before")
    def validate_keys(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("And condition must contain only one key-value pair")
        return values

    def to_internal(self, **kwargs):
        return AndCondition(type="and", arguments=[cond.to_internal() for cond in self.root["and"]])


class OrConditionModel(RootModel[Dict[Literal["or"], List["AllConditionModels"]]]):
    @model_validator(mode="before")
    def validate_keys(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Or condition must contain only one key-value pair")

    def to_internal(self, **kwargs):
        return OrCondition(type="or", arguments=[cond.to_internal() for cond in self.root["or"]])


class NotConditionModel(RootModel[Dict[Literal["not"], "AllConditionModels"]]):
    @model_validator(mode="before")
    def validate_keys(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Not condition must contain only one key-value pair")
        return values

    def to_internal(self, **kwargs):
        return NotCondition(type="not", argument=self.root["not"].to_internal())


# Операционные условия


class SubConditionModel(BaseModel):
    condition: Optional["AllConditionModels"] = Field(default=None)

    def to_internal(self, **kwargs):
        result = self.model_dump()
        if self.condition:
            result["condition"] = self.condition.to_internal()
        return result


class NonArgBodyModel(SubConditionModel):
    def to_internal(self, **kwargs):
        data = super().to_internal(**kwargs)
        data.update(kwargs)
        return NonArgOperationCondition(**data)


class NonArgOperationConditionModel(RootModel[Dict[NonArgType, Union[Literal["$"], NonArgBodyModel]]]):
    @model_validator(mode="before")
    def validate_keys(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Non-arg operation condition must contain only one key-value pair")
        return values

    def to_internal(self, **kwargs):
        type = next(iter(self.root.keys()))
        if isinstance(self.root[type], NonArgBodyModel):
            return self.root[type].to_internal(type=type)
        return NonArgOperationCondition(type=type)


class BinaryBodyModel(SubConditionModel):
    argument: Any

    def to_internal(self, **kwargs):
        data = super().to_internal(**kwargs)
        data.update(kwargs)
        return BinaryOperationCondition(**data)


class BinaryOperationConditionModel(RootModel[Dict[BinaryType, Union[BinaryBodyModel, Any]]]):
    @model_validator(mode="before")
    def validate_keys(cls, values):
        if isinstance(values, dict) and len(list(values.keys())) > 1:
            raise ValueError("Binary operation condition must contain only one key-value pair")
        return values

    def to_internal(self, **kwargs):
        type = next(iter(self.root.keys()))
        if isinstance(self.root[type], BinaryBodyModel):
            return self.root[type].to_internal(type=type)
        return BinaryOperationCondition(type=type, argument=self.root[type])


AllConditionModels = Union[
    EquatationConditionModel,
    InclusionConditionModel,
    AndConditionModel,
    OrConditionModel,
    NotConditionModel,
    NonArgOperationConditionModel,
    BinaryOperationConditionModel,
]

EquatationConditionModel.model_rebuild()
InclusionConditionModel.model_rebuild()
AndConditionModel.model_rebuild()
OrConditionModel.model_rebuild()
NotConditionModel.model_rebuild()
NonArgOperationConditionModel.model_rebuild()
BinaryOperationConditionModel.model_rebuild()
