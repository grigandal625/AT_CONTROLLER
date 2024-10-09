from at_queue.core.at_component import ATComponent
from at_queue.utils.decorators import authorized_method
from at_controller.core.fsm import StateMachine
# from at_controller.core.pages import PAGES
# from at_controller.diagram.states import TRANSITIONS, STATES, get_triggering_transitions
from at_queue.core.session import ConnectionParameters
from typing import Dict
from yaml import safe_load
from at_controller.diagram.models import DiagramModel

class ATController(ATComponent):
    
    state_machines = None
    scenario = None
    
    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters=connection_parameters, *args, **kwargs)
        with open('src/scenario.yaml', 'r') as file:
            diagram_dict = safe_load(file)
            diagram = DiagramModel.from_dict(diagram_dict)
            self.scenario = diagram
        
        self.state_machines = {}
    
    @authorized_method
    async def start_process(self, auth_token: str = None) -> str:
        auth_token = auth_token or 'default'
        
        process = StateMachine(self, auth_token=auth_token, diagram=self.scenario)
        self.state_machines[auth_token] = process
        
        initial_state = process.diagram.get_state(process.state)
        
        await self.exec_external_method('ATRenderer', 'render_page', {
            'page': initial_state.get_page(process)
        }, auth_token=auth_token)
        
        return process.state
    
    
    @authorized_method
    async def trigger_transition(self, trigger: str, frames: dict, auth_token: str = None) -> str:
        auth_token = auth_token or 'default'
        process: StateMachine = self.state_machines.get(auth_token)
        
        if not process:
            return 'No tutoring process found for this auth token'
        
        state = process.diagram.get_state(process.state)
        transition = process.diagram.get_transition(trigger)
        if transition.name in [t.name for t in process.diagram.get_state_exit_transitions(state)]:
            
            if transition.actions:
                for action in transition.actions:
                    action.perform(process, frames)
            
            process.trigger(transition.name)
            
            new_state = process.diagram.get_state(process.state)
            await self.exec_external_method('ATRenderer', 'render_page', {
                'page': new_state.get_page(process)
            }, auth_token=auth_token)
        
        return process.state
    