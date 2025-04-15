import pytest
import yaml

from at_controller.core.fsm import StateMachine
from at_controller.diagram.models.actions import SetAttributeActionModel
from at_controller.diagram.models.diagram import DiagramModel
from at_controller.diagram.models.transitions import Transitions
from at_controller.diagram.state.functions import Function
from at_controller.diagram.state.functions import InitialEventData


@pytest.fixture
def diagram():
    return yaml.safe_load(open("./tests/fixtures/scenario.yaml"))


@pytest.fixture
def set_attibte_as_event_data():
    return yaml.safe_load(
        """
set_attribute:
  attribute: skills_result
  value: $initial_event_data"""
    )


@pytest.fixture
def combined_condition_in_transition():
    return yaml.safe_load(
        """
errors_in_update_type:
  type: event
  event: kbTypes/update
  source: building_types
  dest: building_types
  trigger_condition:
    or:
      - not:
          has_attr:
            left_value: { get_attribute: skills_result }
            right_value: stage_done
      - and:
          - has_attr:
              left_value: { get_attribute: skills_result }
              right_value: stage_done
          - not:
              get_attr:
                left_value: { get_attribute: skills_result }
                right_value: stage_done

all_types_updated:
  type: event
  event: kbTypes/update
  source: building_types
  dest: building_types
  trigger_condition:
    and:
      - has_attr:
          left_value: { get_attribute: skills_result }
          right_value: stage_done
      - get_attr:
          left_value: { get_attribute: skills_result }
          right_value: stage_done
"""
    )


def test_action(set_attibte_as_event_data):
    action_model = SetAttributeActionModel(**set_attibte_as_event_data)
    action = action_model.to_internal()
    assert action.attribute == "skills_result"
    assert isinstance(action.value, InitialEventData)


def test_diagram_model(diagram):
    diagram_model = DiagramModel(**diagram)
    diagram = diagram_model.to_internal()
    machine = StateMachine(None, None, diagram)
    assert machine.state == "kb_start"


def test_combined_condition_in_transition(combined_condition_in_transition):
    transitions_model = Transitions(**combined_condition_in_transition)
    transitions = transitions_model.to_internal()
    assert len(transitions) == 2
    assert isinstance(transitions[0].trigger_condition, Function)
    assert transitions[0].trigger_condition.name == "or"
    assert isinstance(transitions[1].trigger_condition, Function)
    assert transitions[1].trigger_condition.name == "and"
