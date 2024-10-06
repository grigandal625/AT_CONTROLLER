from transitions.extensions import GraphMachine
from at_controller.core.states import STATES, TRANSITIONS
from at_queue.core.at_component import ATComponent

class TutoringProcess(object):
    comaponent: ATComponent
    auth_token: str

    def __init__(self, component, auth_token):
        self.component = component
        self.auth_token = auth_token
        
        self.translated_machine = GraphMachine(
            model=self, 
            states=STATES.states,
            transitions=TRANSITIONS.transitions, 
            initial=STATES.states[0]
        )
        
    
        

# Пример использования машины состояний и генерации диаграммы
if __name__ == "__main__":
    process = TutoringProcess()
    print(process.state)
