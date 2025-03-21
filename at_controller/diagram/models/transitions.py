from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel

from at_controller.diagram.models.actions import AllActionModels
from at_controller.diagram.models.conditions import AllConditionModels
from at_controller.diagram.state.transitions import EventTransition
from at_controller.diagram.state.transitions import FrameHandlerTransition
from at_controller.diagram.state.transitions import LinkTransition


class TransitionModel(BaseModel):
    source: str
    dest: str
    actions: Optional[List[AllActionModels]] = Field(default=None)
    translation: Optional[str] = Field(default=None)

    def get_data(self):
        data = self.model_dump()
        if self.actions:
            data["actions"] = [action.to_internal() for action in self.actions]
        return data


class LinkTransitionModel(TransitionModel):
    type: str = "link"
    label: str
    position: Optional[Literal["header", "footer", "control"]] = Field(default="header")
    icon: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)

    def to_internal(self, **kwargs):
        data = self.get_data()
        data.update(kwargs)
        return LinkTransition(**data)


class FrameHandlerTransitionModel(TransitionModel):
    type: str = "frame_handler"
    frame_id: str
    test: str
    tags: Optional[List[str]] = Field(default=None)

    def to_internal(self, **kwargs):
        data = self.get_data()
        data.update(kwargs)
        return FrameHandlerTransition(**data)


class EventTransitionModel(TransitionModel):
    event: Optional[str] = Field(default=None)
    type: Literal["event"] = "event"
    source: str
    dest: str
    trigger_condition: Optional[AllConditionModels] = Field(default=None)

    def get_data(self):
        data = super().get_data()
        if self.trigger_condition:
            data["trigger_condition"] = self.trigger_condition.to_internal()
        return data

    def to_internal(self, **kwargs):
        data = self.get_data()
        data.update(kwargs)
        return EventTransition(**data)


AllTransitionModes = Union[LinkTransitionModel, FrameHandlerTransitionModel, EventTransitionModel]


class Transitions(RootModel[Dict[str, AllTransitionModes]]):
    def to_internal(self, **kwargs):
        return [transition.to_internal(name=key) for key, transition in self.root.items()]
