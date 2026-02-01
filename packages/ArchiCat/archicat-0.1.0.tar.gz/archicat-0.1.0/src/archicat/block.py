from archicat import components

from enum import EnumType,Enum
from typing import Optional,TYPE_CHECKING,Any,Callable,Type,Self

if TYPE_CHECKING:
    from .transformer import ScratchFileBuilder

class BlockAccessModifier(Enum):
    ALL = 'all'
    STAGE = 'stage'
    SPRITE = 'sprite'

def _enum_has_value(enum: EnumType,value: Any) -> bool:
    return value in set(item.value for item in enum)


type Value = str | float | int

type InputItem = components.Id | Value | None

type FieldOrInput = Callable[['ScratchFileBuilder',InputItem],components.Input | components.Field]


def field(builder: 'ScratchFileBuilder',value: str,id: Optional[components.Id] = None) -> components.Field:
    return components.Field(value,id)

def variable_field(builder: 'ScratchFileBuilder',name: str) -> components.Field:
    return field(builder,name,builder._get_variable(name))

def list_field(builder: 'ScratchFileBuilder',name: str) -> components.Field:
    return field(builder,name,builder._get_list(name))

def message_field(builder: 'ScratchFileBuilder',name: str) -> components.Field:
    return field(builder,name,builder._get_message(name))

def costume_field(builder: 'ScratchFileBuilder',name: str) -> components.Field:
    return field(builder,name)

def sound_field(builder: 'ScratchFileBuilder',name: str) -> components.Field:
    return field(builder,name)

def option_field(options: Optional[Type[EnumType]] = None) -> FieldOrInput:
    def _option_field(builder: 'ScratchFileBuilder',value: str | Enum) -> components.Field:
        if isinstance(value,options):
            return field(builder,value.value)
        elif isinstance(value,str) and (options is None or _enum_has_value(options,value)):
            return field(builder,value)
    return _option_field


def input(builder: 'ScratchFileBuilder',type: components.InputType | int,
          value: InputItem,shadow: Optional[InputItem] = None) -> components.Input:
    if isinstance(value,components.Id):
        if isinstance(block := builder._block_by_id(value),components.Block):
            block.parent = builder.parent_block_stack[-1]
        if components.InputType(type) == components.InputType.SHADOW:
            builder._block_by_id(value).shadow = True
    if isinstance(shadow,components.Id):
        builder._block_by_id(value).parent = builder.parent_block_stack[-1]
        builder._block_by_id(value).shadow = True
    return components.Input(type,value,shadow)

def bool_input(builder: 'ScratchFileBuilder',value: components.Id) -> components.Input:
    return input(builder,components.InputType.NO_SHADOW,value)

def _value_input(builder: 'ScratchFileBuilder',type: components.InputType,value: Any) -> components.Input:
    if isinstance(value,components.Id):
        return input(builder,components.InputType.OBSCURED_SHADOW,value,
                     components.Value(type,''))
    else:
        return input(builder,components.InputType.SHADOW,
                     components.Value(type,value))
    
def int_input(builder: 'ScratchFileBuilder',value: int | components.Id) -> components.Input:
    return _value_input(builder,components.ValueType.INT,value)

def float_input(builder: 'ScratchFileBuilder',value: float | components.Id) -> components.Input:
    return _value_input(builder,components.ValueType.FLOAT,value)

def unsigned_int_input(builder: 'ScratchFileBuilder',value: int | components.Id) -> components.Input:
    return _value_input(builder,components.ValueType.UNSIGNED_INT,value)

def unsigned_float_input(builder: 'ScratchFileBuilder',value: float | components.Id) -> components.Input:
    return _value_input(builder,components.ValueType.UNSIGNED_FLOAT,value)

def angle_input(builder: 'ScratchFileBuilder',value: float | components.Id) -> components.Input:
    return _value_input(builder,components.ValueType.ANGLE,value)

def color_input(builder: 'ScratchFileBuilder',value: str | components.Id) -> components.Input:
    return _value_input(builder,components.ValueType.COLOR,value)

def string_input(builder: 'ScratchFileBuilder',value: str | components.Id) -> components.Input:
    return _value_input(builder,components.ValueType.STRING,value)

def chain_input(builder: 'ScratchFileBuilder',value: components.Id) -> components.Input:
    return input(builder,components.InputType.NO_SHADOW,value)

def costume_input(builder: 'ScratchFileBuilder',value: components.Id | str) -> components.Input:
    input_block = Block('looks_costume',COSTUME=field)
    if isinstance(value,components.Id):
        return input(builder,components.InputType.OBSCURED_SHADOW,value,
                     input_block(builder,builder.current_target.costumes[0].name))
    else:
        return input(builder,components.InputType.SHADOW,input_block(builder,value))
    
def sound_input(builder: 'ScratchFileBuilder',value: components.Id | str) -> components.Input:
    input_block = Block('sound_sounds_menu',SOUNDS_MENU=field)
    if isinstance(value,components.Id):
        return input(builder,components.InputType.OBSCURED_SHADOW,value,
                     input_block(builder,builder.current_target.sounds[0].name))
    else:
        return input(builder,components.InputType.SHADOW,input_block(builder,value))

def option_input(options: Type[EnumType],shadow: str | Enum,input_block: 'Block') -> FieldOrInput:
    def _option_input(builder: 'ScratchFileBuilder',value: components.Id | str | Enum) -> components.Input:
        if isinstance(value,components.Id):
            return input(builder,components.InputType.OBSCURED_SHADOW,value,input_block(builder,shadow))
        elif isinstance(value,(options,value)):
            return input(builder,components.InputType.SHADOW,input_block(value.value))
        else:
            return input(builder,components.InputType.SHADOW,input_block(value))
    return _option_input

def message_input(builder: 'ScratchFileBuilder',message: components.Id | str) -> components.Input:
    if isinstance(message,components.Id):
        id,name = builder.stage.broadcasts.items()[0]
        return input(builder,components.InputType.OBSCURED_SHADOW,
                     message,components.VariableValue(components.VariableType,name,id))
    else:
        return input(builder,components.InputType.SHADOW,
                     components.VariableValue(components.VariableType.MESSAGE,message,
                        builder._get_message(message)))
    

class Block:
    opcode: str
    mutation: Optional[components.Mutation] = None
    args: list[tuple[str,FieldOrInput]]
    attached_options: EnumType

    def __init__(self,opcode: str,mutation: Optional[components.Mutation]=None,**kwargs: FieldOrInput):
        self.opcode = opcode
        self.mutation = mutation
        self.args = kwargs.items()
        self.attached_options = [None] * len(self.args)

    def attach_options(self,*args: EnumType,**kwargs: EnumType) -> Self:
        self.attached_options[:len(args)] = args
        for name,options in kwargs.items():
            self.attached_options[list(map(lambda arg: arg[0],self.args)).index(name)] = options
        return self
    
    def apply_args(self,builder: 'ScratchFileBuilder',*args: InputItem) -> components.Block:
        inputs = {}
        fields = {}
        for arg,(name,func) in zip(args,self.args):
            arg = func(builder,arg)
            if isinstance(arg,components.Field):
                fields[name] = arg
            elif isinstance(arg,components.Input) and arg[1] is not None:
                inputs[name] = arg
        if self.mutation is None:
            block = components.Block(self.opcode,inputs=inputs,fields=fields)
        else:
            block = components.MutationBlock(self.opcode,inputs=inputs,fields=fields,mutation=self.mutation)
        return block

    def __call__(self,builder: 'ScratchFileBuilder',*args: InputItem,id: Optional[components.Id] = None) -> components.Id:        
        return builder._register_block(self.apply_args(builder,*args),id)


class Monitor:
    opcode: str
    attached_options: Optional[EnumType]

    def __init__(self,opcode: str):
        self.opcode = opcode
        self.attached_options = None

    def attach_options(self,options: EnumType) -> Self:
        self.attached_options = options
        return self

    def __call__(self,builder: 'ScratchFileBuilder',x: int = 0,y: int = 0,visible: bool = True) -> components.Monitor:
        return components.ListMonitor(
            self.opcode.split('_',1)[-1],
            self.opcode,
            x=x,
            y=y,
            visible=visible
        )
    

class SpriteSpecificMonitor(Monitor):
    def __call__(self,builder: 'ScratchFileBuilder',*args,**kwargs) -> components.Monitor:
        monitor = super().__call__(builder,*args,**kwargs)
        if not builder.current_target.isStage:
            monitor.spriteName = builder.current_target.name
        return monitor