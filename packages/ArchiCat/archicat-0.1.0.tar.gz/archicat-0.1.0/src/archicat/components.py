from typing import Any,Union,Literal,NamedTuple,Optional
from pydantic.dataclasses import dataclass
from pydantic_core import core_schema
from dataclasses import field,asdict,is_dataclass
from enum import Enum

class Id(str):
    @classmethod
    def __get_pydantic_core_schema__(cls,*args,**kwargs):
        return core_schema.no_info_after_validator_function(cls,core_schema.str_schema())

    def __repr__(self):
        return f'Id(\'{self}\')'
    
# type Id = str


class InputType(Enum):
    SHADOW = 1
    NO_SHADOW = 2
    OBSCURED_SHADOW = 3

class ValueType(Enum):
    FLOAT = 4
    UNSIGNED_FLOAT = 5
    UNSIGNED_INT = 6
    INT = 7
    ANGLE = 8
    COLOR = 9
    STRING = 10

class VariableType(Enum):
    MESSAGE = 11
    VARIABLE = 12
    LIST = 13

class VideoState(Enum):
    ON = 'on'
    OFF = 'off'
    FLIPPED = 'on-flipped'

class RotationStyle(Enum):
    ALL_AROUND = 'all around'
    LEFT_RIGHT = 'left-right'
    DONT_ROTATE = 'don\'t rotate'

class Warp(Enum):
    TRUE = 'true'
    FALSE = 'false'

class HasNext(Enum):
    TRUE = 'true'
    FALSE = 'false'



class Value(NamedTuple):
    type: Union[ValueType,VariableType]
    value: Any
    
class VariableValue(NamedTuple):
    type: VariableType
    value: Any
    id: Id
    x: Optional[int] = None
    y: Optional[int] = None

class Input(NamedTuple):
    type: InputType
    input: Union[Id,Value,VariableValue]
    shadow: Optional[Union[Id,Value,VariableValue]] = None
    
class Field(NamedTuple):
    value: Any
    id: Optional[Id] = None

class Variable(NamedTuple):
    name: str
    value: Any = ''
    cloud: bool = False
    
class List(NamedTuple):
    name: str
    value: list[Any] = field(default_factory = list)

@dataclass
class ListMonitor:
    id: Id
    opcode: str
    params: dict[str,Any] = field(default_factory=dict)
    mode: str = 'default'
    spriteName: Optional[str] = None
    value: Any = None
    width: int = 0
    height: int = 0
    x: int = 0
    y: int = 0
    visible: bool = True
    
@dataclass
class Monitor(ListMonitor):
    sliderMin: int = 0
    sliderMax: int = 100
    isDiscrete: bool = True
    
@dataclass
class Comment:
    text: str
    blockId: Optional[Id] = None
    minimized: bool = False
    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 100
    
@dataclass
class Meta:
    semver: str = '3.0.0'
    vm: str = '5.0.0'
    agent: str = ''

@dataclass
class Block:
    opcode: str
    inputs: dict[str,Input] = field(default_factory = dict)
    fields: dict[str,Field] = field(default_factory = dict)
    next: Optional[Id] = None
    parent: Optional[Id] = None
    shadow: bool = False 
    topLevel: bool = False

@dataclass
class CommentedBlock(Block):
    comment: Id = Id()

@dataclass
class HatBlock(Block):
    x: int = 0
    y: int = 0

@dataclass
class MutationBlock(Block):
    mutation: Optional['Mutation'] = None
    
@dataclass
class Mutation:
    tagName: str = 'mutation'
    children: list[Any] = field(default_factory = list)
    
@dataclass
class Procedure(Mutation):
    proccode: str = ''
    argumentids: str = ''
    warp: Warp | str = Warp.FALSE
    
@dataclass
class ProcedurePrototype(Procedure):
    argumentnames: str = ''
    argumentdefaults: str = ''
    
@dataclass
class ControlStop(Mutation):
    hasnext: HasNext | str = HasNext.TRUE
    
@dataclass
class Asset:
    assetId: str = ''
    name: str = ''
    md5ext: str = ''
    dataFormat: str = ''
    
@dataclass
class Costume(Asset):
    bitmapResolution: int = 1
    rotationCenterX: float = 0
    rotationCenterY: float = 0
    
@dataclass
class Sound(Asset):
    rate: float = 1
    sampleCount: int = 1
    
@dataclass
class Target:
    name: str
    isStage: bool = False
    variables: dict[Id,Variable] = field(default_factory = dict)
    lists: dict[Id,List] = field(default_factory = dict)
    broadcasts: dict[Id,str] = field(default_factory = dict)
    blocks: dict[Id,Block | VariableValue] = field(default_factory = dict)
    comments: dict[Id,Comment] = field(default_factory = dict)
    costumes: list[Costume] = field(default_factory = list)
    sounds: list[Sound] = field(default_factory = list)
    currentCostume: int = 1
    volume: int = 100
    
@dataclass
class Stage(Target):
    layerOrder: int = 0
    tempo: int = 120
    videoState: VideoState = VideoState.OFF
    videoTransparency: int = 50
    textToSpeechLanguage: str = 'English'
    
@dataclass
class Sprite(Target):
    layerOrder: int = 1
    visible: bool = True
    x: int = 0
    y: int = 0
    size: int = 100
    direction: int = 90
    draggable: bool = False
    rotationStyle: RotationStyle = RotationStyle.ALL_AROUND
    
@dataclass
class Project:
    targets: list[Sprite | Stage] = field(default_factory = list)
    monitors: list[Monitor] = field(default_factory = list)
    extensions: list[str] = field(default_factory = list)
    meta: Meta = field(default_factory = Meta)


def to_json(component: Any) -> Any:
    if isinstance(component,Asset) and not len(component.md5ext):
        component.md5ext = component.assetId + '.' + component.dataFormat 
    if isinstance(component,Variable):
        if component.cloud:
            return component
        else:
            return component.name,component.value
    elif isinstance(component,(Value,VariableValue,Input,Field,List)):
        return list(map(to_json,filter(lambda x: x is not None,component)))
    elif is_dataclass(component):
        return dict({k: to_json(getattr(component,k)) for k in component.__dataclass_fields__})
    elif isinstance(component,(tuple,list)):
        return list(map(to_json,component))
    elif isinstance(component,dict):
        return dict(zip(component.keys(),map(to_json,component.values())))
    elif isinstance(component,Enum):
        return component.value
    else:
        return component
    
def from_json(data: dict):
    return Project(**data)

