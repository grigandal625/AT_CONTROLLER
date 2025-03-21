from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
from pydantic import RootModel

from at_controller.diagram.models.functions import ActionValueType
from at_controller.diagram.models.functions import FunctionModel
from at_controller.diagram.state.actions import ExecMethodAction
from at_controller.diagram.state.actions import SetAttributeAction
from at_controller.diagram.state.actions import ShowMessageAction


class ActionBodyModel(BaseModel):
    next: Optional[List["AllActionModels"]] = Field(default=None)

    def to_internal(self, **kwargs):
        result = self.model_dump()
        if self.next:
            result["next"] = [action.to_internal() for action in self.next]
        return result


class SetAttributeBody(ActionBodyModel):
    attribute: str
    value: ActionValueType

    def to_internal(self, **kwargs):
        data = super().to_internal()
        data["value"] = FunctionModel.build_functions(self.value)
        return SetAttributeAction(**data)


class SimpleSetAttributeBody(RootModel[Dict[str, ActionValueType]]):
    @model_validator(mode="before")
    def check_keys(self, values, **kwargs):
        if isinstance(values, dict) and len(list(values)) > 1:
            raise ValueError("SetAttribute action must contain only one key-value pair")
        return values

    def to_internal(self, **kwargs):
        attr = next(iter(self.root.keys()))
        value = self.root[attr]
        value = FunctionModel.build_functions(value)
        return SetAttributeAction(attribute=attr, value=value)


class SetAttributeActionModel(BaseModel):
    set_attribute: Union[SetAttributeBody, SimpleSetAttributeBody]

    def to_internal(self, **kwargs):
        return self.set_attribute.to_internal()


class ShowMessageBody(ActionBodyModel):
    message: str
    title: Optional[str] = Field(default="Сообщеие")
    modal: Optional[bool] = Field(default=True)
    message_type: Optional[Literal["info", "warning", "success", "error"]] = Field(default="info")

    def to_internal(self, **kwargs):
        result = super().to_internal(**kwargs)
        return ShowMessageAction(**result)


class ShowMessageActionModel(BaseModel):
    show_message: ShowMessageBody

    def to_internal(self, **kwargs):
        return self.show_message.to_internal(**kwargs)


class ExecMethodBodyModel(ActionBodyModel):
    component: ActionValueType
    method: ActionValueType
    method_args: ActionValueType
    auth_token: Optional[ActionValueType] = Field(default=None)

    def to_internal(self, **kwargs):
        data = super().to_internal()
        data["component"] = FunctionModel.build_functions(self.component)
        data["method"] = FunctionModel.build_functions(self.method)
        data["method_args"] = FunctionModel.build_functions(self.method_args)
        if self.auth_token:
            data["auth_token"] = FunctionModel.build_functions(self.auth_token)
        return ExecMethodAction(**data)


class ExecMethodActionModel(BaseModel):
    exec_method: ExecMethodBodyModel

    def to_internal(self, **kwargs):
        return self.exec_method.to_internal()


AllActionModels = Union[SetAttributeActionModel, ShowMessageActionModel, ExecMethodActionModel]

SetAttributeActionModel.model_rebuild()
ShowMessageActionModel.model_rebuild()
ExecMethodActionModel.model_rebuild()
