from typing import List, Union, TypedDict, Any
from dataclasses import dataclass


@dataclass
class Col:
    src: str
    frame_id: str
    props: Any = None


@dataclass
class Row:
    cols: List[Col]
    props: Any = None


@dataclass
class Grid:
    rows: List[Row]


@dataclass
class Link:
    type: str
    href: str
    label: str
    props: Any = None


@dataclass
class Fetch:
    type: str
    url: str
    label: str
    options: Any = None
    framedata_field: Union[str, None] = None
    props: Any = None
    
    
@dataclass
class ComponentMethod:
    type: str
    label: str
    component: str
    method: str
    framedata_field: Union[str, None] = None
    kwargs: Any = None
    props: Union[dict, None] = None


@dataclass
class Panel:
    label: str
    links: List[Union[Link, Fetch, ComponentMethod]]


@dataclass
class Page:
    grid: Grid
    header: Union[Panel, None] = None
    footer: Union[Panel, None] = None

class ColDict(TypedDict):
    src: str
    frame_id: str = None
    props: Union[dict, None] = None

class RowDict(TypedDict):
    cols: List[ColDict]
    props: Union[dict, None] = None

class GridDict(TypedDict):
    rows: List[RowDict]

class LinkDict(TypedDict):
    type: str
    href: str
    label: str
    props: Union[dict, None] = None

class FetchDict(TypedDict):
    type: str
    url: str
    label: str
    options: Union[dict, None] = None
    framedata_field: Union[str, None] = None
    props: Union[dict, None] = None

class ComponentMethodDict(TypedDict):
    type: str
    label: str
    component: str
    method: str
    framedata_field: Union[str, None] = None
    kwargs: Union[dict, None] = None
    props: Union[dict, None] = None

class PanelDict(TypedDict):
    label: str
    links: List[Union[LinkDict, FetchDict]]

class PageDict(TypedDict):
    grid: GridDict
    header: PanelDict
    footer: PanelDict