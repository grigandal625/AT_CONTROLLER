import asyncio
from logging import getLogger
from typing import Union

from at_queue.core.at_component import ATComponent
from at_queue.core.session import ConnectionParameters
from at_queue.utils.decorators import authorized_method
from yaml import safe_load

from at_controller.core.fsm import StateMachine
from at_controller.diagram.models import DiagramModel
from at_controller.diagram.state import EventTransition

# from at_controller.core.pages import PAGES
# from at_controller.diagram.states import TRANSITIONS, STATES, get_triggering_transitions

logger = getLogger(__name__)


class ATController(ATComponent):
    state_machines = None
    scenario = None

    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters=connection_parameters, *args, **kwargs)
        with open("src/scenario.yaml", "r") as file:
            diagram_dict = safe_load(file)
            diagram = DiagramModel.from_dict(diagram_dict)
            self.scenario = diagram

        self.state_machines = {}

    @authorized_method
    async def start_process(self, auth_token: str = None) -> str:
        auth_token = auth_token or "default"

        process = StateMachine(
            self, auth_token=auth_token, diagram=self.scenario)
        self.state_machines[auth_token] = process

        initial_state = process.diagram.get_state(process.state)

        await self.exec_external_method(
            "ATRenderer",
            "render_page",
            {"page": initial_state.get_page(process)},
            auth_token=auth_token,
        )

        return process.state

    @authorized_method
    async def trigger_transition(
        self, trigger: str, frames: dict, auth_token: str = None
    ) -> str:
        auth_token = auth_token or "default"
        process: StateMachine = self.state_machines.get(auth_token)

        if not process:
            return "No process found for this auth token"

        state = process.diagram.get_state(process.state)
        transition = process.diagram.get_transition(trigger)
        if transition.name in [
            t.name for t in process.diagram.get_state_exit_transitions(state)
        ]:
            if transition.actions:
                await asyncio.gather(*[action.perform(process, frames) for action in transition.actions])

            process.trigger(transition.name)

            new_state = process.diagram.get_state(process.state)
            await self.exec_external_method(
                "ATRenderer",
                "render_page",
                {"page": new_state.get_page(process)},
                auth_token=auth_token,
            )

        return process.state

    @authorized_method
    async def handle_event(
        self,
        event: str,
        data: Union[int, float, bool, str, dict, list],
        frames: dict = None,
        auth_token: str = None,
    ):
        auth_token = auth_token or "default"
        process: StateMachine = self.state_machines.get(auth_token)

        if not process:
            return "No process found for this auth token"

        state = process.diagram.get_state(process.state)
        diagram_event = process.diagram.get_event(event)

        checking_data = data

        if diagram_event:
            if diagram_event.handler_component and diagram_event.handler_method:
                if await self.check_external_registered(
                    diagram_event.handler_component
                ):
                    checking_data = await self.exec_external_method(
                        diagram_event.handler_component,
                        diagram_event.handler_method,
                        {"event": event, "data": data},
                        auth_token=auth_token,
                    )
                else:
                    msg = f"For event {event} handler component "
                    msg += f"{diagram_event.handler_component} is not registered"
                    if diagram_event.raise_on_missing:
                        raise ReferenceError(msg)
                    logger.warning(msg)

        for transition in process.diagram.get_state_exit_transitions(state):
            if (
                not transition
                or not isinstance(transition, EventTransition)
                or transition.event != event
            ):
                continue

            if transition.trigger_condition:
                if transition.trigger_condition.check(checking_data, process):
                    return await self.trigger_transition(
                        transition.name, frames or {}, auth_token=auth_token
                    )
            else:
                return await self.trigger_transition(
                    transition.name, frames or {}, auth_token=auth_token
                )

        return data
