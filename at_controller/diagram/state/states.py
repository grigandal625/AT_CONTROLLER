from dataclasses import dataclass
from dataclasses import field
from logging import getLogger
from typing import List
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union
from urllib.parse import parse_qs
from urllib.parse import quote_plus
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse


if TYPE_CHECKING:
    from at_controller.core.fsm import StateMachine
    from at_controller.diagram.state.transitions import LinkTransition, FrameHandlerTransition

logger = getLogger(__name__)


@dataclass(kw_only=True)
class Frame:
    frame_id: str
    src: str
    redirect: Optional[str] = field(default=None)
    redirect_param: Optional[str] = field(default="to")
    frame_id_param: Optional[str] = field(default="frame_id")
    type: Literal["basic", "format_attributes", "docs"] = field(default="basic")
    span: Optional[Union[int, str]] = field(default="auto")

    def format_src(self, state_machine: "StateMachine"):
        if self.type == "format_attributes" or self.type == "docs":
            return self.src.format(**state_machine.attributes)
        return self.src

    def format_redirect(self, state_machine: "StateMachine"):
        if self.type == "format_attributes" and self.redirect is not None:
            return self.redirect.format_map(state_machine.attributes)
        return self.redirect

    def get_src(self, state_machine: "StateMachine"):
        if self.type == "docs":
            src = "/docview?asFrame=true&viewing=true&docs="
            docs = self.format_src(state_machine)
            formatted_docs = quote_plus(docs)
            src += formatted_docs
            return src
        src = self.format_src(state_machine)
        if self.redirect is not None:
            redirect = self.format_redirect(state_machine)
            parsed_url = urlparse(src)
            parsed_query = parse_qs(parsed_url.query)

            redirect_param = self.redirect_param or "to"
            parsed_query[redirect_param] = [redirect]

            frame_id_param = self.frame_id_param or "frame_id"
            parsed_query[frame_id_param] = [self.frame_id]

            new_query_string = urlencode(parsed_query, doseq=True)

            final_src = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query_string,
                    parsed_url.fragment,
                )
            )

            return final_src
        return src

    def get_column(self, state_machine: "StateMachine"):
        return {
            "src": self.get_src(state_machine),
            "frame_id": self.frame_id,
            "props": {"flex": self.span, "style": {"height": "100%"}},
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

    def get_page(self, state_machine: "StateMachine"):
        link_transitions: List["LinkTransition"] = [
            t for t in state_machine.diagram.get_state_exit_transitions(self) if t.type == "link"
        ]
        frame_handler_transitions: List["FrameHandlerTransition"] = [
            t for t in state_machine.diagram.get_state_exit_transitions(self) if t.type == "frame_handler"
        ]

        header = {
            "label": self.label,
            "links": [
                {
                    "type": "component_method",
                    "label": transition.label,
                    "component": "ATController",
                    "method": "trigger_transition",
                    "kwargs": {
                        "trigger": transition.name,
                    },
                    "framedata_field": "frames",
                }
                for transition in link_transitions
                if transition.position == "header"
            ],
        }

        footer = {
            "links": [
                {
                    "type": "component_method",
                    "label": transition.label,
                    "component": "ATController",
                    "method": "trigger_transition",
                    "kwargs": {
                        "trigger": transition.name,
                    },
                    "framedata_field": "frames",
                }
                for transition in link_transitions
                if transition.position == "footer"
            ]
        }

        control = {
            "label": self.control_label or "",
            "subtitle": self.control_subtitle or "",
            "links": [
                {
                    "type": "component_method",
                    "label": transition.label,
                    "component": "ATController",
                    "method": "trigger_transition",
                    "kwargs": {
                        "trigger": transition.name,
                    },
                    "framedata_field": "frames",
                }
                for transition in link_transitions
                if transition.position == "control"
            ],
        }

        handlers = [
            {
                "type": "component_method",
                "component": "ATController",
                "method": "trigger_transition",
                "test": transition.test,
                "frame_id": transition.frame_id,
                "kwargs": {
                    "trigger": transition.name,
                },
                "framedata_field": "frames",
            }
            for transition in frame_handler_transitions
        ]

        result = {
            "grid": {
                "rows": [
                    {
                        "props": {"style": {"height": "100%"}},
                        "cols": [frame.get_column(state_machine) for frame in frame_row],
                    }
                    for frame_row in self.frame_rows
                ]
            },
            "header": header,
            "handlers": handlers,
        }

        if footer["links"]:
            result["footer"] = footer
        if control["label"] or control["subtitle"] or control["links"]:
            result["control"] = control

        return result
