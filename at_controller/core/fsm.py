from transitions.extensions import GraphMachine
from at_queue.core.at_component import ATComponent

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from at_controller.diagram.state import Diagram

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


class StateMachine(object):
    comaponent: ATComponent
    auth_token: str
    attributes: Dict[str, Any]
    diagram: 'Diagram'

    def __init__(self, component, auth_token, diagram: 'Diagram'):
        self.component = component
        self.auth_token = auth_token
        self.attributes = SafeDict()
        self.attributes['auth_token'] = auth_token
        self.diagram = diagram
        
        self.translated_machine = GraphMachine(
            model=self, 
            **diagram.annotation
        )
        
    
        

# Пример использования машины состояний и генерации диаграммы
if __name__ == "__main__":
    process = StateMachine()
    print(process.state)
