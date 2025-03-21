import pytest
import yaml

from at_controller.core.fsm import StateMachine
from at_controller.diagram.models.actions import SetAttributeActionModel
from at_controller.diagram.models.diagram import DiagramModel
from at_controller.diagram.state.functions import EventData


@pytest.fixture
def diagram():
    return yaml.safe_load(open("./tests/fixtures/scenario.yaml"))


@pytest.fixture
def set_attibte_as_event_data():
    return yaml.safe_load(
        """
set_attribute:
  attribute: skills_result
  value: $event_data"""
    )


def test_action(set_attibte_as_event_data):
    action_model = SetAttributeActionModel(**set_attibte_as_event_data)
    action = action_model.to_internal()
    assert action.attribute == "skills_result"
    assert isinstance(action.value, EventData)


def test_diagram_model(diagram):
    diagram_model = DiagramModel(**diagram)
    diagram = diagram_model.to_internal()
    machine = StateMachine(None, None, diagram)
    assert machine.state == "kb_start"
