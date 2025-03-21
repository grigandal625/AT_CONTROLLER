from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel

from at_controller.diagram.models.actions import AllActionModels
from at_controller.diagram.state.events import Event


class EventModel(BaseModel):
    handler_component: Optional[str] = Field(default=None)
    handler_method: Optional[str] = Field(default=None)
    raise_on_missing: Optional[bool] = Field(default=False)
    actions: Optional[List[AllActionModels]] = Field(default=None)

    def to_internal(self, **kwargs):
        data = self.model_dump()
        data.update(kwargs)
        if self.actions:
            data["actions"] = [action.to_internal() for action in self.actions]
        return Event(**data)


class Events(RootModel[Dict[str, EventModel]]):
    def to_internal(self, **kwargs):
        return [event.to_internal(name=key) for key, event in self.root.items()]
