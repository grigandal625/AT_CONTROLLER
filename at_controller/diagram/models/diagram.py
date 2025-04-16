import os
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel

from at_controller.diagram.models.events import Events
from at_controller.diagram.models.states import States
from at_controller.diagram.models.transitions import Transitions
from at_controller.diagram.state.diagram import Diagram
import dotenv

dotenv.load_dotenv()


class EnvInitialAttributeModel(BaseModel):
    env: str
    default: Optional[Any] = Field(default=None)

    def to_internal(self):
        return os.getenv(self.env, self.default)


class InitialAttributes(RootModel[Dict[str, Union[EnvInitialAttributeModel, Any]]]):
    def to_internal(self):
        return {k: v.to_internal() if isinstance(v, EnvInitialAttributeModel) else v for k, v in self.root.items()}


class DiagramModel(BaseModel):
    states: States
    transitions: Transitions
    events: Optional[Events] = Field(default_factory=lambda: Events({}))
    initial_attributes: Optional[InitialAttributes] = Field(default_factory=lambda: InitialAttributes({}))

    def to_internal(self):
        data = self.model_dump()
        if self.initial_attributes:
            data["initial_attributes"] = self.initial_attributes.to_internal()
        data["states"] = self.states.to_internal()
        data["transitions"] = self.transitions.to_internal()
        if self.events:
            data["events"] = self.events.to_internal()
        return Diagram(**data)
