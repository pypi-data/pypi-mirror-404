from .transformer import transpile

from dataclasses import dataclass,field
from typing import Any,Optional,Self
from pathlib import Path

type Value = int | float | str | bool
type BlockArgument = 'Block' | 'Chain' | Value
type Comment = tuple[str,dict[str,Value]]
type Position = Optional[tuple[int,int]]

def _comment_to_code(comment: Comment,indent: int = 0) -> str:
    content,options = comment
    if len(options):
        code = f': "{content}" ' + '{\n'
        for name,value in options.items():
            code += '\t' * (indent + 1) + f'{name} = {to_code(value)}\n'
        code += '\t' * indent + '}'
    else:
        code = f': "{content}"'
    return code
        

class Writer:
    def generate_code(self) -> str: pass

class Block(Writer):
    opcode: str
    args: tuple[BlockArgument]
    comment: Optional[tuple[str,dict]] = None

    def __init__(self,opcode: str,*args: BlockArgument):
        self.opcode = opcode
        self.args = args

    def add_comment(self,text: str,**kwargs) -> Self:
        self.comment = (text,kwargs)
        return self

    def generate_code(self,indent: int = 0):
        return f'{self.opcode}({','.join(map(lambda arg: to_code(arg,indent),self.args))})' + \
            ('' if self.comment is None else _comment_to_code(self.comment,indent))
    
class Chain(list[Block],Writer):
    def __init__(self,*items: Block):
        super().__init__(items)

    def generate_code(self,indent: int = 0):
        indent += 1
        return '{\n' + '\t' * indent + ('\n' + '\t' * indent).join(map(lambda arg: to_code(arg,indent),self)) + '\n' + ('\t' * (indent - 1)) + '}'
    
class Target(Writer):
    name: str
    events: list[tuple[Block,Chain,Position]]
    procedures: list[tuple[str,tuple[str,...],bool,Position,Chain]]
    variables: list[tuple[str,Optional[Value]]]
    lists: list[tuple[str,list[Value]]]
    messages: list[str]
    costumes: list[tuple[str,str,dict]]
    sounds: list[tuple[str,str]]
    defaults: dict[str,Value]
    monitors: list[tuple[Block,dict[str,Value]]]
    comments: list[Comment]

    def __init__(self,name: str):
        self.name = name
        self.events = []
        self.procedures = []
        self.variables = []
        self.lists = []
        self.messages = []
        self.costumes = []
        self.sounds = []
        self.defaults = {}
        self.monitors = []
        self.comments = []

    def add_event_chain(self,block: Block,chain: Chain,position: Position = None):
        self.events.append((block,chain,position))

    def add_event(self,block: Block,*chain: Block,position: Position = None):
        self.add_event_chain(block,Chain(*chain),position)

    def add_procedure_chain(self,name: str,args: tuple[str],chain: Chain,warp: bool = False,position: Position = None):
        self.procedures.append((name,args,warp,position,chain))

    def add_procedure(self,name: str,args: tuple[str],*chain: Block,warp: bool = False,position: Position = None):
        self.add_procedure_chain(name,args,Chain(*chain),warp,position)

    def add_variable(self,name: str,value: Optional[Value] = None):
        self.variables.append((name,value))

    def add_list(self,name: str,items: list[Value]):
        self.lists.append((name,items))

    def add_message(self,name: str):
        self.messages.append(name)

    def add_costume(self,name: str,path: str,**options: Value):
        self.costumes.append((name,path,options))

    def add_sound(self,name: str,path: str):
        self.sounds.append((name,path))

    def add_default(self,name: str,value: Value):
        self.defaults[name] = value

    def add_monitor(self,block: Block,**options: Value):
        self.monitors.append((block,options))

    def add_comment(self,content: str,**options: Value):
        self.comments.append((content,options))

    def generate_code(self,indent: int = 0):
        code = ''
        for name,value in self.variables:
            code += '\t' * indent
            if value is None:
                code += f'var {name}\n'
            else:
                code += f'var {name} = {to_code(value)}\n'
        for name,items in self.lists:
            code += '\t' * indent
            code += f'list {name} = [{','.join(map(to_code,items))}]\n'
        for name in self.messages:
            code += '\t' * indent
            code += f'message {name}\n'
        for name,path,options in self.costumes:
            code += '\t' * indent
            if len(options):
                code += f'costume {name} = "{path}"' + " {\n"
                for option,value in options.items():
                    code += '\t' * (indent + 1) + f'{option} = {to_code(value)}\n'
                code += '\t' * indent + '}\n'
            else:
                code += f'costume {name} = "{path}"\n'
        for name,path in self.sounds:
            code += '\t' * indent
            code += f'sound {name} = {repr(path)}\n'
        for name,value in self.defaults.items():
            code += '\t' * indent
            code += f'default {name} = {to_code(value)}\n'
        for block,options in self.monitors:
            code += '\t' * indent
            code += f'monitor {to_code(block,indent)} ' + '{\n'
            for name,value in options.items():
                code += '\t' * (indent + 1)
                code += f'{name} = {to_code(value)}\n'
            code += '\t' * indent + '\n}'
        for block,chain,position in self.events:
            code += '\t' * indent
            position = '' if position is None else f'[{position[0]},{position[1]}]'
            code += f'on {block.generate_code(indent)}{position} {chain.generate_code(indent)}\n'
        for name,args,warp,position,chain in self.procedures:
            code += '\t' * indent
            position = '' if position is None else f'[{position[0]},{position[1]}]'
            if warp:
                code += f'warp {name} ({','.join(args)}){position} {chain.generate_code(indent)}\n'
            else:
                code += f'proc {name} ({','.join(args)}){position} {chain.generate_code(indent)}\n'
        for comment in self.comments:
            code += '\t' * indent
            code += _comment_to_code(comment,indent)
        return code
    
class Stage(Target):
    sprites: list['Sprite']

    def __init__(self):
        super().__init__('Stage')
        self.sprites = []

    def add_sprite(self,sprite: 'Sprite'):
        self.sprites.append(sprite)

    def generate_code(self,indent: int = 0):
        code = super().generate_code()
        for sprite in self.sprites:
            code += '\t' * indent
            code += sprite.generate_code()
        return code
    
    def transpile_into(self,path: str | Path,source_dir: Optional[Path | str] = None):
        transpile(self.generate_code(),path,source_dir)
    
class Sprite(Target):
    def generate_code(self,indent: int = 1):
        return f'sprite {self.name} ' + '{\n' + super().generate_code(indent) + '\n}'


def to_code(object: BlockArgument,indent: int = 0) -> str:
    if isinstance(object,str):
        return f'"{object}"'
    elif isinstance(object,(int,float)):
        return str(object)
    elif isinstance(object,bool):
        return 'true' if object else 'false'
    elif isinstance(object,Writer):
        return object.generate_code(indent)
    else:
        raise TypeError(f'Cannot convert {object} (type "{type(object)}") to code')
