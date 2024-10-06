from at_queue.core.at_component import ATComponent
from at_queue.utils.decorators import authorized_method
from at_controller.core.fsm import TutoringProcess
from at_controller.core.pages import PAGES
from at_controller.core.states import TRANSITIONS, STATES, get_triggering_transitions
from at_queue.core.session import ConnectionParameters
from typing import Dict

class ATController(ATComponent):
    
    tutoring_processes = None
    
    def __init__(self, connection_parameters: ConnectionParameters, *args, **kwargs):
        super().__init__(connection_parameters=connection_parameters, *args, **kwargs)
        self.tutoring_processes = {}
    
    @authorized_method
    async def start_tutoring(self, auth_token: str = None) -> str:
        auth_token = auth_token or 'default'
        process = TutoringProcess(self, auth_token=auth_token)
        self.tutoring_processes[auth_token] = process
        
        await self.exec_external_method('ATRenderer', 'render_page', {
            'page': PAGES[STATES[process.state]]
        }, auth_token=auth_token)
        
        return process.state
    
    
    @authorized_method
    async def trigger_transition(self, transition: str, frames: dict, auth_token: str = None) -> str:
        auth_token = auth_token or 'default'
        process = self.tutoring_processes.get(auth_token)
        
        if not process:
            return 'No tutoring process found for this auth token'
        
        transition = TRANSITIONS[transition]
        if transition in get_triggering_transitions(process.state):
            process.trigger(transition.name)
            await self.exec_external_method('ATRenderer', 'render_page', {
                'page': PAGES[STATES[process.state]]
            }, auth_token=auth_token)
        
        return process.state
    