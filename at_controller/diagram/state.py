import re
from dataclasses import dataclass, field
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional, Literal, List, Union, Dict, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine
    

@dataclass(kw_only=True)
class Frame:
    frame_id: str
    src: str
    redirect: Optional[str] = field(default=None)
    redirect_param: Optional[str] = field(default='to')
    frame_id_param: Optional[str] = field(default='frame_id')
    type: Literal['basic', 'format_attributes'] = field(default='basic')
    span: Optional[Union[int, str]] = field(default='auto')
    
    def format_src(self, state_machine: 'StateMachine'):
        if self.type == 'format_attributes':
            return self.src.format_map(state_machine.attributes)
        return self.src
    
    
    def format_redirect(self, state_machine: 'StateMachine'):
        if self.type == 'format_attributes' and self.redirect is not None:
            return self.redirect.format_map(state_machine.attributes)
        return self.redirect
    
    
    def get_src(self, state_machine: 'StateMachine'):
        src = self.format_src(state_machine)
        if self.redirect is not None:
            redirect = self.format_redirect(state_machine)
            parsed_url = urlparse(src)
            parsed_query = parse_qs(parsed_url.query)
            
            redirect_param = self.redirect_param or 'to'
            parsed_query[redirect_param] = [redirect]
            
            frame_id_param = self.frame_id_param or 'frame_id'
            parsed_query[frame_id_param] = [self.frame_id]
            
            new_query_string = urlencode(parsed_query, doseq=True)
            
            final_src = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query_string,
                parsed_url.fragment
            ))
            
            return final_src
        return src
    
    def get_column(self, state_machine: 'StateMachine'):
        return {
            'src': self.get_src(state_machine),
            'frame_id': self.frame_id,
            'props': {
                'flex': self.span,
                'style': {'height': '100%'}
            }    
        }


@dataclass(kw_only=True)
class State:
    name: str
    label: str
    frame_rows: List[List[Frame]] 
    control_label: Optional[str] = field(default=None)
    control_subtitle: Optional[str] = field(default=None)
    translation: Optional[str] = field(default=None)
    initial: Optional[bool] = field(default=False)
    
    @property
    def annotation(self):
        return self.name
    
    def get_page(self, state_machine: 'StateMachine'):
        link_transitions: List[LinkTransition] = [t for t in state_machine.diagram.get_state_exit_transitions(self) if t.type == 'link']
        frame_handler_transitions: List[FrameHandlerTransition] = [t for t in state_machine.diagram.get_state_exit_transitions(self) if t.type == 'frame_handler']
        
        header = {
            'label': self.label,
            'links': [{
                'type': 'component_method',
                'label': transition.label,
                'component': 'ATController',
                'method': 'trigger_transition',
                'kwargs': {
                    'trigger': transition.name,
                },
                'framedata_field': 'frames'
            } for transition in link_transitions if transition.position == 'header']
        }
        
        footer = {
            'links': [{
                'type': 'component_method',
                'label': transition.label,
                'component': 'ATController',
                'method': 'trigger_transition',
                'kwargs': {
                    'trigger': transition.name,
                },
                'framedata_field': 'frames'
            } for transition in link_transitions if transition.position == 'footer']
        }

        control = {
            'label': self.control_label or "",
            'subtitle': self.control_subtitle or "",
            'links': [{
                'type': 'component_method',
                'label': transition.label,
                'component': 'ATController',
                'method': 'trigger_transition',
                'kwargs': {
                    'trigger': transition.name,
                },
                'framedata_field': 'frames'
            } for transition in link_transitions if transition.position == 'control']
        }
        
        handlers = [{
            'type': 'component_method',
            'component': 'ATController',
            'method': 'trigger_transition',
            'test': transition.test,
            'frame_id': transition.frame_id,
            'kwargs': {
                'trigger': transition.name,
            },
            'framedata_field': 'frames'
        } for transition in frame_handler_transitions]
        
        result = {
            'grid': {
                'rows': [
                    {
                        'props': {
                            'style': {'height': '100%'}
                        },
                        'cols': [frame.get_column(state_machine) for frame in frame_row]
                    } 
                    for frame_row in self.frame_rows
                ]
            },
            'header': header,
            'handlers': handlers
        }
        
        if footer['links']:
            result['footer'] = footer
        if control['label'] or control['subtitle'] or control['links']:
            result['control'] = control
        
        return result
        


@dataclass(kw_only=True)
class Transition:
    name: str
    source: Union[str, State]
    dest: Union[str, State]
    type: Literal['link', 'frame_handler']
    actions: List['Action']
    translation: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)
    
    @property
    def annotation(self):
        return {'trigger': self.name, 'source': self.source.annotation if isinstance(self.source, State) else self.source, 'dest': self.dest.annotation if isinstance(self.dest, State) else self.dest}
    

@dataclass(kw_only=True)
class LinkTransition(Transition):
    name: str
    label: str
    actions: List['Action']
    position: Optional[Literal['header', 'footer', 'control']] = field(default='header')
    translation: Optional[str] = field(default=None)
    type: Literal['link'] = field(default='link')
    icon: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)


@dataclass(kw_only=True)
class FrameHandlerTransition(Transition):
    name: str
    frame_id: str
    actions: List['Action'] = field(default=None)
    test: str
    type: Literal['frame_handler'] = field(default='frame_handler')
    translation: Optional[str] = field(default=None)
    tags: Optional[List[str]] = field(default=None)


@dataclass(kw_only=True)
class Action:
    type: str
    next: Optional[List['Action']] = field(default=None)

    def perform(self, state_machine: 'StateMachine', frames: Dict[str, str]):
        
        result = self.action(state_machine, frames)

        if self.next:
            for next_action in self.next:
                next_action.perform()

        return result

    def action(self, state_machine: 'StateMachine', frames: Dict[str, str]):
        pass


@dataclass(kw_only=True)
class SetAttributeAction(Action):
    type: Literal['set_attribute'] = field(default='set_attribute')
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
    kwargs: Optional[Dict[str, Union[str, int, float, bool, list, dict, 'Function']]] = field(default_factory=dict)

    def _search_and_call_functions(self, value: dict, state_machine: 'StateMachine', frames: Dict[str, str]) -> dict:
        for k, v in value.items():
            if isinstance(v, Function):
                value[k] = v.call(state_machine, frames)
            elif isinstance(v, dict):
                value[k] = self._search_and_call_functions(v, state_machine, frames)
            elif isinstance(v, list):
                value[k] = [self._search_and_call_functions(item, state_machine, frames) for item in v]
        return value

    def call(self, state_machine: 'StateMachine', frames: Dict[str, str]):
        
        kwargs = self._search_and_call_functions(self.kwargs, state_machine, frames)
        return self.exec(state_machine, frames, **kwargs)

    def exec(self, state_machine: 'StateMachine', frames: Dict[str, str], **kwargs):
        pass


class AttributeArg(TypedDict):
    attribute: str


@dataclass(kw_only=True)
class GetAttribute(Function):
    name: Literal['get_attribute'] = field(default='get_attribute')
    kwargs: AttributeArg

    def exec(self, state_machine: 'StateMachine', frames: Dict[str, str], **kwargs):
        return state_machine.attributes.get(kwargs['attribute'])


class UrlRegexpSub(TypedDict):
    regexp: str
    group: Optional[int]


class QueryParamSub(TypedDict):
    param: str
    index: Optional[int]


class FrameUrlArg(TypedDict):
    frame_id: str
    parse: Optional[UrlRegexpSub]
    query_param: Optional[QueryParamSub]


@dataclass(kw_only=True)
class FrameUrl(Function):
    name: Literal['frame_url']
    kwargs: FrameUrlArg

    def exec(self, state_machine: 'StateMachine', frames: Dict[str, str], **kwargs):
        frame_id = kwargs['frame_id']
        url = frames.get(frame_id)

        if 'parse' in kwargs:
            parse = kwargs['parse']
            match = re.match(parse['regexp'], url)
            if match is None:
                return None
            return match.groups()[parse['group']]
        
        if 'query_params' in kwargs:
            query_params = kwargs['query_params']
            query_string = urlparse(url).query
            query_params = parse_qs(query_string)
            if 'index' in kwargs['query_params']:
                return query_params.get(kwargs['query_params']['param'], [None] * (kwargs['query_params']['index'] + 1))[kwargs['query_params']['index']]
            else:
                return query_params.get(kwargs['query_params'], [None])[0]
            
        return url
    

@dataclass(kw_only=True)
class AuthToken(Function):
    name: Literal['auth_token']
    kwargs: Dict
    
    def exec(self, state_machine: 'StateMachine', frames: Dict[str, str], **kwargs):
        return state_machine.auth_token

@dataclass(kw_only=True)
class Diagram:
    states: List[State]
    transitions: List[Transition]
    
    @property
    def annotation(self):
        return {
            'states': [state.annotation for state in self.states], 
            'transitions': [transition.annotation for transition in self.transitions],
            'initial': next((state.annotation for state in self.states if state.initial), None)
        }
        
    def get_state(self, name: str):
        return next((state for state in self.states if state.name == name), None)
    
    def get_transition(self, name: str):
        return next((transition for transition in self.transitions if transition.name == name), None)
    
    def get_state_exit_transitions(self, state: Union[str, State]):
        if isinstance(state, State):
            state = state.annotation
            
        return [transition for transition in self.transitions if transition.annotation['source'] == state]
    
    def get_state_enter_transitions(self, state: Union[str, State]):
        if isinstance(state, State):
            state = state.annotation
            
        return [transition for transition in self.transitions if transition.annotation['dest'] == state]
    
    def get_state_all_transitions(self, state: Union[str, State]):
        return self.get_state_exit_transitions(state) + self.get_state_enter_transitions(state)

