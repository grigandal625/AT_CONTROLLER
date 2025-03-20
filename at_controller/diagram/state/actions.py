import asyncio
from dataclasses import dataclass
from dataclasses import field
from logging import getLogger
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

from at_controller.diagram.state.functions import Function

logger = getLogger(__name__)


if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine


@dataclass(kw_only=True)
class Action:
    type: str
    next: Optional[List["Action"]] = field(default=None)

    async def perform(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        result = await self.action(state_machine, frames, event_data=event_data)
        if self.next:
            await asyncio.gather(
                *[next_action.perform(state_machine, frames, event_data=event_data) for next_action in self.next]
            )
        return result

    async def action(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        pass


@dataclass(kw_only=True)
class SetAttributeAction(Action):
    type: Literal["set_attribute"] = field(default="set_attribute")
    attribute: str
    value: Union[str, int, float, bool, "Function", list, dict]

    async def action(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        value = self.value
        if isinstance(value, Function):
            value = value.exec(state_machine, frames, event_data=event_data, **value.kwargs)
        state_machine.attributes[self.attribute] = value

        result = {}
        result[self.attribute] = value
        return result


@dataclass(kw_only=True)
class ShowMessageAction(Action):
    type: Literal["show_message"] = field(default="show_message")
    message: str
    title: Optional[str] = field(default="")
    modal: Optional[bool] = field(default=True)
    message_type: Optional[str] = field(default="info")

    async def action(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        return await state_machine.component.exec_external_method(
            "ATRenderer",
            "show_message",
            {
                "message": self.format_message(state_machine),
                "modal": self.modal,
                "message_type": self.message_type,
                "title": self.title,
            },
            auth_token=state_machine.auth_token,
        )

    def format_message(self, state_machine: "StateMachine"):
        return self.message.format_map(state_machine.attributes)


@dataclass(kw_only=True)
class ExecMethodAction(Action):
    type: Literal["exec_method"] = field(default="exec_method")
    component: str
    method: str
    method_args: Optional[Dict[str, Union[str, int, float, bool, list, dict, "Function"]]] = field(default_factory=dict)
    auth_token: Optional[str] = field(default=None)

    async def action(self, state_machine: "StateMachine", frames: Dict[str, str], event_data=None):
        if not await state_machine.component.check_external_registered(self.component):
            raise ValueError(f'Component "{self.component}" is not registered')
        method_args = self.method_args
        method_args = Function.search_and_call_functions(method_args, state_machine, frames, event_data=event_data)
        auth_token = self.auth_token or state_machine.auth_token
        return await state_machine.component.exec_external_method(
            self.component, self.method, method_args, auth_token=auth_token
        )
