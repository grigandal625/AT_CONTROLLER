from typing import Any
from typing import Dict
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from at_controller.diagram.models.events import Events
from at_controller.diagram.models.states import States
from at_controller.diagram.models.transitions import Transitions
from at_controller.diagram.state.diagram import Diagram


class DiagramModel(BaseModel):
    states: States
    transitions: Transitions
    events: Optional[Events] = Field(default_factory=lambda: Events({}))
    initial_attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)

    def to_internal(self):
        data = self.model_dump()
        data["states"] = self.states.to_internal()
        data["transitions"] = self.transitions.to_internal()
        if self.events:
            data["events"] = self.events.to_internal()
        return Diagram(**data)
