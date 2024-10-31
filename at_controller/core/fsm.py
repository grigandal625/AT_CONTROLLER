from typing import Any
from typing import Dict
from typing import TYPE_CHECKING

from at_queue.core.at_component import ATComponent
from transitions.extensions import GraphMachine

if TYPE_CHECKING:
    from at_controller.diagram.state import Diagram


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


class StateMachine(object):
    component: ATComponent
    auth_token: str
    attributes: Dict[str, Any]
    diagram: "Diagram"

    def __init__(self, component: 'ATComponent', auth_token: 'str', diagram: "Diagram"):
        self.component = component
        self.auth_token = auth_token
        self.attributes = SafeDict()
        self.attributes["auth_token"] = auth_token
        self.diagram = diagram
        self.attributes.update(diagram.initial_attributes or {})

        self.translated_machine = GraphMachine(
            model=self, **diagram.annotation)


# Пример использования машины состояний и генерации диаграммы
if __name__ == "__main__":
    process = StateMachine()
    print(process.state)
