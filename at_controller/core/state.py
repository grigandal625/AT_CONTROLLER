from dataclasses import dataclass, Field
import re
from typing import Optional, Literal, List, Union, Dict, Any, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine


@dataclass(kw_only=True)
class State:
    name: str
    label: str
    translation: Optional[str] = Field(None)


@dataclass(kw_only=True)
class Transition:
    name: str
    label: str
    translation: Optional[str] = Field(None)
    type: Literal['link', 'frame_handler']
    actions: List['Action']


@dataclass(kw_only=True)
class LinkTransition(Transition):
    name: str
    label: str
    translation: Optional[str] = Field(None)
    type: Literal['link'] = Field('link')
    actions: List['Action']
    position: Optional[Literal['header', 'footer', 'control']]
    icon: Optional[str] = Field(None)


@dataclass(kw_only=True)
class FrameHandlerTransition(Transition):
    name: str
    label: str
    translation: Optional[str] = Field(None)
    type: Literal['frame_handler'] = Field('frame_handler')
    actions: List['Action']
    test: str


@dataclass(kw_only=True)
class Action:
    type: str
    next: Optional[List['Action']] = Field(None)

    def perform(self, state_machine: 'StateMachine', frames: Dict[str, str]):
        
        result = self.action(state_machine, frames)

        for next_action in self.next:
            next_action.perform()

        return result

    def action(self, state_machine: 'StateMachine', frames: Dict[str, str]):
        pass


@dataclass(kw_only=True)
class SetAttributeAction(Action):
    type: Literal['set_attribute'] = Field('set_attribute')
    attribute: str
    value: Union[str, int, float, bool, list, dict, 'Function']

    def action(self, state_machine: 'StateMachine', frames: Dict[str, str]):
        value = self.value
        if isinstance(value, Function):
            value = value.exec(state_machine, frames, **value.kwargs)
        state_machine.attributes[self.attribute] = value

        result = {}
        result[self.attribute] = value
        return result


@dataclass(kw_only=True)
class Function:
    name: str
    kwargs: Optional[Dict[str, Union[str, int, float, bool, list, dict, 'Function']]] = Field(default_factory=dict)

    def call(self, state_machine: 'StateMachine', frames: Dict[str, str]):
        return self.exec(state_machine, frames, **self.kwargs)

    def exec(self, state_machine: 'StateMachine', frames: Dict[str, str], **kwargs):
        pass


class AttributeArg(TypedDict):
    attribute: str


@dataclass(kw_only=True)
class GetAttribute(Function):
    name: Literal['get_attribute'] = Field('get_attribute')
    kwargs: AttributeArg

    def exec(self, state_machine: 'StateMachine', frames: Dict[str, str], **kwargs):
        return state_machine.attributes.get(self.kwargs['attribute'])


class UrlRegexpSub(TypedDict):
    regexp: str
    group: int


class FrameUrlArg(TypedDict):
    frame_id: str
    parse: Optional(UrlRegexpSub)


@dataclass(kw_only=True)
class FrameUrl(Function):
    name: Literal['frame_url']
    kwargs: FrameUrlArg

    def exec(self, state_machine: 'StateMachine', frames: Dict[str, str], **kwargs):
        frame_id = self.kwargs['frame_id']
        url = frames.get(frame_id)

        if 'parse' not in self.kwargs or not self.kwargs.get('parse'):
            return url

        parse = self.kwargs['parse']
        return re.match(parse['regexp'], url).groups()[parse['group']]



