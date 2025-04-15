from dataclasses import dataclass
from dataclasses import field
from logging import getLogger
from typing import List
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

from at_controller.diagram.state.functions import Function
from at_controller.diagram.state.states import State


if TYPE_CHECKING:
    from at_controller.diagram.state.actions import Action


logger = getLogger(__name__)


@dataclass(kw_only=True)
class Transition:
    name: str
    source: "State"
    dest: "State"
    type: Literal["link", "frame_handler"]
    actions: List["Action"]
    translation: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)

    @property
    def annotation(self):
        return {
            "trigger": self.name,
            "source": (self.source.annotation if isinstance(self.source, State) else self.source),
            "dest": self.dest.annotation if isinstance(self.dest, State) else self.dest,
        }


@dataclass(kw_only=True)
class LinkTransition(Transition):
    name: str
    label: str
    actions: List["Action"]
    position: Optional[Literal["header", "footer", "control"]] = field(default="header")
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
class EventTransition(Transition):
    name: str
    event: Optional[str] = field(default=None)

    trigger_condition: Optional[Union[str, int, float, bool, "Function", list, dict]] = field(default=None)

    actions: List["Action"] = field(default=None)
    type: Literal["internal_event"] = field(default="event")
    translation: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)

    def __post_init__(self):
        if not self.event:
            self.event = self.name
