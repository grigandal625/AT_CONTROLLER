from dataclasses import dataclass
from dataclasses import field
from logging import getLogger
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from at_controller.diagram.state.events import Event
from at_controller.diagram.state.states import State
from at_controller.diagram.state.transitions import Transition


logger = getLogger(__name__)


@dataclass(kw_only=True)
class Diagram:
    states: List[State]
    transitions: List[Transition]
    events: List[Event]
    initial_attributes: Optional[Dict[str, Any]] = field(default_factory=dict)

    @property
    def annotation(self):
        return {
            "states": [state.annotation for state in self.states],
            "transitions": [transition.annotation for transition in self.transitions],
            "initial": next((state.annotation for state in self.states if state.initial), None),
        }

    def get_state(self, name: str) -> Union[State, None]:
        return next((state for state in self.states if state.name == name), None)

    def get_transition(self, name: str) -> Union[Transition, None]:
        return next(
            (transition for transition in self.transitions if transition.name == name),
            None,
        )

    def get_state_exit_transitions(self, state: Union[str, State]) -> List[Transition]:
        if isinstance(state, State):
            state = state.annotation

        return [transition for transition in self.transitions if transition.annotation["source"] == state]

    def get_state_enter_transitions(self, state: Union[str, State]) -> List[Transition]:
        if isinstance(state, State):
            state = state.annotation

        return [transition for transition in self.transitions if transition.annotation["dest"] == state]

    def get_state_all_transitions(self, state: Union[str, State]) -> List[Transition]:
        return self.get_state_exit_transitions(state) + self.get_state_enter_transitions(state)

    def get_event(self, name: str) -> Union[Event, None]:
        return next((event for event in self.events if event.name == name), None)
