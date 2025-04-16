from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel

from at_controller.diagram.state.states import Frame
from at_controller.diagram.state.states import State


class FrameModel(BaseModel):
    src: str
    redirect: Optional[str] = Field(default=None)
    redirect_param: Optional[str] = Field(default="to")
    frame_id_param: Optional[str] = Field(default="frame_id")
    type: Literal["basic", "format_attributes", "docs"] = Field(default="basic")
    span: Optional[Union[int, str]] = Field(default="auto")

    def to_internal(self, **kwargs):
        data = self.model_dump()
        data.update(kwargs)
        return Frame(**data)


class FrameRowModel(RootModel[Dict[str, Union[str, FrameModel]]]):
    def to_internal(self, **kwargs):
        result = []
        for key, value in self.root.items():
            if isinstance(value, str):
                value = FrameModel(src=value)
            result.append(value.to_internal(frame_id=key))
        return result


class StateModel(BaseModel):
    label: Optional[str]
    frame_rows: Union[FrameRowModel, List[FrameRowModel]]
    control_label: Optional[str] = Field(default=None)
    control_subtitle: Optional[str] = Field(default=None)
    translation: Optional[str] = Field(default=None)
    initial: Optional[bool] = Field(default=False)

    def to_internal(self, **kwargs):
        data = self.model_dump()
        data.update(kwargs)
        if isinstance(self.frame_rows, FrameRowModel):
            data["frame_rows"] = [self.frame_rows.to_internal()]
        else:
            data["frame_rows"] = [row.to_internal() for row in self.frame_rows]
        return State(**data)


class States(RootModel[Dict[str, StateModel]]):
    def to_internal(self, **kwargs):
        result = []
        for key, value in self.root.items():
            result.append(value.to_internal(name=key))
        return result
