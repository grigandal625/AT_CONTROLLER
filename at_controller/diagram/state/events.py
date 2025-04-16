import asyncio
from dataclasses import dataclass
from dataclasses import field
from logging import getLogger
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from at_controller.diagram.state.actions import Action


if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine

logger = getLogger(__name__)


@dataclass(kw_only=True)
class Event:
    name: str
    handler_component: Optional[str] = field(default=None)
    handler_method: Optional[str] = field(default=None)
    raise_on_missing: Optional[bool] = field(default=False)
    actions: Optional[List[Action]] = field(default=None)

    async def handle(
        self, event: str, state_machine: "StateMachine", frames: Dict[str, str], event_data: Any = None, **kwargs
    ):
        checking_data = event_data
        if self.handler_component and self.handler_method:
            if await state_machine.component.check_external_registered(self.handler_component):
                try:
                    checking_data = await state_machine.component.exec_external_method(
                        self.handler_component,
                        self.handler_method,
                        {"event": event, "data": event_data},
                        auth_token=state_machine.auth_token,
                    )
                except Exception as e:
                    logger.error(e)
            else:
                msg = f"For event {event} handler component "
                msg += f"{self.handler_component} is not registered"
                if self.raise_on_missing:
                    raise ReferenceError(msg)
                logger.warning(msg)

        if self.actions:
            await asyncio.gather(*[action.perform(state_machine, frames, checking_data) for action in self.actions])

        return checking_data
