from at_controller.diagram.states import STATES, get_triggering_transitions


def get_state_page(state: STATES, frame_id, frame_src):
    return {
        'grid': {
            'rows': [
                {
                    'props': {
                        'style': {'height': '100%'}
                    },
                    'cols': [
                        {
                            'src': frame_src,
                            'frame_id': frame_id,
                            'props': {
                                'flex': 'auto',
                                'style': {'height': '100%'}
                            }    
                        }
                    ]
                }
            ]
        },
        'header': {
            'label': state.name,
            'links': [{
                'type': 'component_method',
                'label': transition.name,
                'component': 'ATController',
                'method': 'trigger_transition',
                'kwargs': {
                    'transition': transition.name,
                },
                'framedata_field': 'frames'
            } for transition in get_triggering_transitions(state)]
        }
    }

PAGES = {
    STATES.UNAUTHORIZED: get_state_page(STATES.UNAUTHORIZED, 'kb_editor', 'http://45.148.245.134:5000/'),
    STATES.AUTHORIZED_INITIAL: get_state_page(STATES.AUTHORIZED_INITIAL, 'kb_editor', 'http://185.17.141.230:8787/token?default&frame_id=kb_editor'),
    STATES.AUTHORIZED_SELECTING: get_state_page(STATES.AUTHORIZED_SELECTING, 'kb_editor', 'http://185.17.141.230:8787/token?default&frame_id=kb_editor'),
    STATES.WORK1: get_state_page(STATES.WORK1, 'kb_editor', 'http://185.17.141.230:8787/token?token=default&frame_id=kb_editor'),
    STATES.CREATE_EMPTY_KB: get_state_page(STATES.CREATE_EMPTY_KB, 'kb_editor', 'http://185.17.141.230:8787/token?token=default&frame_id=kb_editor'),
    STATES.LOAD_KB: get_state_page(STATES.LOAD_KB, 'kb_editor', 'http://185.17.141.230:8787/token?token=default&frame_id=kb_editor'),
    STATES.BUILD_TYPES: get_state_page(STATES.BUILD_TYPES, 'kb_editor', 'http://185.17.141.230:8787/token?token=default&frame_id=kb_editor'),
    STATES.BUILD_BASIC_OBJECTS: get_state_page(STATES.BUILD_BASIC_OBJECTS, 'kb_editor', 'http://185.17.141.230:8787/token?token=default&frame_id=kb_editor'),
}