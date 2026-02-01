from archicat import components
from .block import Block,bool_input,string_input
from .extension import ExtensionManager,Extension
from .parser import parse

from lark import Tree
from lark.visitors import Interpreter,v_args
from zipfile import ZipFile
from pathlib import Path
from typing import Optional,Type,Callable
from uuid import uuid4
from enum import Enum
from json import dumps as dump_json,loads as load_json
from hashlib import md5
from wave import open as open_wav
from mutagen.mp3 import MP3
from enum import Enum,auto


def random_id(name: str = '') -> components.Id:
    return components.Id(name + '_' * bool(len(name)) + uuid4().hex)


class IdentifierType(Enum):
    VARIABLE = 'variable'
    LIST = 'list'
    MESSAGE = 'message'

class ArgumentType(Enum):
    STRING = auto()
    BOOL = auto()


@v_args(inline=True)
class ScratchFileBuilder(Interpreter):
    assets: list[tuple[str,Path]]
    project: components.Project
    stage: components.Stage
    current_target: components.Target
    block_stack: list[ExtensionManager]
    expands_file: Optional[Path] = None
    parent_block_stack: list[components.Id]
    identifier_type_stack: list[IdentifierType]
    available_options_stack: list[Type[Enum]]
    secondary_callbacks: list[tuple[Callable,components.Target,Extension]]
    source_path: Optional[Path]

    def __init__(self,source_path: Optional[Path]):
        self.assets = []
        self.stage = components.Stage('Stage',True)
        self.current_target = self.stage
        self.block_stack = [ExtensionManager(self)]
        self.block_stack[-1].add_extension(Extension('custom'))
        self.parent_block_stack = [None]
        self.identifier_type_stack = []
        self.available_options_stack = []
        self.secondary_callbacks = []
        self.expands_file = None
        self.project = components.Project(targets=[self.stage])
        self.source_path = source_path

    def save(self,path: Path | str):
        for callback,self.current_target,self.block_stack in self.secondary_callbacks:
            callback()
        with ZipFile(str(path),'w') as zipfile:
            zipfile.writestr('project.json',data := dump_json(components.to_json(self.project),indent=4))
            # print(data)
            for name,path in self.assets:
                zipfile.writestr(name,path.read_bytes())
            if self.expands_file is not None:
                with ZipFile(self.expands_file,'r') as srcfile:
                    for asset in srcfile.namelist():
                        if asset != 'project.json':
                            zipfile.writestr(asset,srcfile.read(asset))

    def _secondary_decorator(self,callback: Callable):
        self.secondary_callbacks.append((callback,self.current_target,self.block_stack.copy()))

    def _get_variable(self,name: str) -> components.Id:
        return next(id for id,variable in (*self.current_target.variables.items(),
                    *self.stage.variables.items()) if variable.name == name)
    
    def _get_list(self,name: str) -> components.Id:
        return next(id for id,list in (*self.current_target.lists.items(), 
                    *self.stage.lists.items()) if list.name == name)
    
    def _get_message(self,name: str) -> components.Id:
        return next(id for id,msgname in self.stage.broadcasts.items() 
                    if name == msgname)
    
    def _block_by_id(self,id: components.Id) -> components.Block:
        return self.current_target.blocks[id]
    
    def _register_block(self,block: components.Block | components.VariableValue,id: Optional[components.Id] = None) -> components.Id:
        self.current_target.blocks[id or (id := random_id())] = block
        return id
    
    # def _statement_blocks(self) -> dict[str,Block]:
    #     return (stage_statement_blocks if self.current_target.isStage else sprite_statement_blocks) | self.procedure_scope_stack[-1]
    
    # def _reporter_blocks(self) -> dict[str,Block]:
    #     return stage_reporter_blocks if self.current_target.isStage else sprite_reporter_blocks
    
    # def _hat_blocks(self) -> dict[str,Block]:
    #     return stage_hat_blocks if self.current_target.isStage else sprite_hat_blocks
    
    def _transform_block(self,block: Block,comment: Tree | None,*args: Tree) -> components.Id:
        self.parent_block_stack.append(block_id := random_id())
        processed_args = []
        for arg,arg_option in zip(args,block.attached_options):
            self.available_options_stack.append(arg_option)
            processed_args.append(self.visit(arg))
            self.available_options_stack.pop()
        block(self,*processed_args,id=block_id)
        if comment is not None:
            self.current_target.comments[comment_id := self.visit(comment)].blockId = block_id
            self.current_target.blocks[block_id] = components.CommentedBlock(**vars(self._block_by_id(block_id)),comment=comment_id)
        return self.parent_block_stack.pop()
    
    def _create_procedure(self,procname: str,chain: Tree,position: Tree,*arguments: Tree,warp: bool):
        x,y = self.visit(position)
        arguments = list(map(self.visit,arguments))
        argument_names = []
        argument_types = []
        argument_ids = []
        argument_defaults = []
        argument_blocks = []
        prototype_id = random_id()
        for name,type in arguments:
            argument_names.append(name)
            argument_types.append(type)
            argument_ids.append(random_id())
            argument_defaults.append('false' if type == ArgumentType.BOOL else '')
            if type == ArgumentType.STRING:
                argument_blocks.append(self._register_block(
                    components.Block('argument_reporter_string_number',fields = {'VALUE': components.Field(name)},shadow=True,parent=prototype_id)))
            else:
                argument_blocks.append(self._register_block(
                    components.Block('argument_reporter_boolean',fields = {'VALUE': components.Field(name)},shadow=True,parent=prototype_id)))
        definition_id = self._register_block(components.HatBlock('procedures_definition',inputs = {
                'custom_block': components.Input(components.InputType.SHADOW,prototype_id)
            },topLevel=True,x=x,y=y))
        self._register_block(components.MutationBlock('procedures_prototype',inputs = {
                id: components.Input(components.InputType.SHADOW,argument_block) for id,argument_block in zip(argument_ids,argument_blocks)
            },shadow=True,parent=definition_id,mutation=components.ProcedurePrototype(
                proccode=(proccode := procname + ' ' + ' '.join('%b' if type == ArgumentType.BOOL else '%s' for _,type in arguments)),
                argumentids=dump_json(argument_ids),
                argumentnames=dump_json(argument_names),
                argumentdefaults=dump_json(argument_defaults),
                warp=components.Warp.TRUE if warp else components.Warp.FALSE
            )),id=prototype_id)
        
        self.block_stack[-1].get_extension('custom').create_statement(procname,
            Block('procedures_call',components.Procedure(
                proccode=proccode,
                argumentids=dump_json(argument_ids),
                warp=components.Warp.TRUE if warp else components.Warp.FALSE
            ),**{argument_id: (bool_input if argument_type == ArgumentType.BOOL else string_input) 
                            for argument_id,argument_type in zip(argument_ids,argument_types)}))
        
        @self._secondary_decorator
        def secondary():
            self._block_by_id(definition_id).next = chain_id = self.visit(chain)
            if chain_id is not None:
                self._block_by_id(chain_id).parent = definition_id

    def start(self,*declarations):
        self.current_target = self.stage
        for declaration in declarations:
            self.visit(declaration)
        return self.project

    def sprite(self,name,*declarations):
        self.block_stack.append(self.block_stack[-1].update('custom',Extension('custom')))
        if targets := list(target for target in self.project.targets if target.name == name):
            self.current_target = targets[0]
        else:
            self.current_target = components.Sprite(name)
            self.project.targets.append(self.current_target)
        for declaration in declarations:
            self.visit(declaration)
        self.current_target = self.stage
        self.block_stack.pop()

    def expand(self,file):
        self.expands_file = Path(file[1:-1])
        if self.source_path is not None:
            self.expands_file = self.source_path.joinpath(self.expands_file)
        with ZipFile(str(self.expands_file)) as zipfile:
            self.project = components.from_json(load_json(zipfile.read('project.json')))
            self.stage = next(target for target in self.project.targets if target.isStage)
            self.current_target = self.stage

    def config_option(self,name,value):
        setattr(self.current_target,name,self.visit(value))

    def config(self,*options):
        for option in options:
            self.visit(option)

    def monitor_option(self,name,value):
        return name,self.visit(value)
    
    def monitor(self,name,arg,*options):
        monitor = self.block_stack[-1].get_monitor(name)
        self.available_options_stack.append(monitor.attached_options)
        if arg is None:
            self.project.monitors.append(monitor(self,**dict(map(self.visit,options))))
        else:
            self.project.monitors.append(monitor(self,self.visit(arg),**dict(map(self.visit,options))))
        self.available_options_stack.pop(0)

    def comment(self,content: str,*options: Tree) -> components.Id:
        self.current_target.comments[id := random_id()] = components.Comment(text=content[1:-1],**dict(map(self.visit,options)))
        return id

    def variable(self,name,value=None):
        self.current_target.variables[random_id()] = \
            components.Variable(name.value,self.visit(value) if value is not None else '')

    def list(self,name,*values):
        self.current_target.lists[random_id()] = \
            components.List(name.value,list(map(self.visit,values)))
        
    def message(self,name):
        self.stage.broadcasts[random_id()] = name.value

    def costume(self,name,path,*options):
        path = Path(path[1:-1])
        if self.source_path is not None:
            path = self.source_path.joinpath(path)
        hash = md5(path.read_bytes()).hexdigest()
        suffix = path.suffix.lstrip('.').lower()
        options = dict(map(self.visit,options))
        self.current_target.costumes.append(components.Costume(
            assetId=hash,
            name=name,
            md5ext=hash + '.' + suffix,
            dataFormat=suffix,
            bitmapResolution=options.get('bitmapResolution',1),
            rotationCenterX=options.get('rotationCenterX',0),
            rotationCenterY=options.get('rotationCenterY',0)
        ))
        self.assets.append((hash + '.' + suffix,path))

    def sound(self,name,path):
        path = Path(path[1:-1])
        path = Path(path[1:-1])
        if self.source_path is not None:
            path = self.source_path.joinpath(path)
        hash = md5(path.read_bytes()).hexdigest()
        suffix = path.suffix.lstrip('.').lower()
        if path.suffix.lstrip('.').lower() == 'wav':
            with open_wav(str(path)) as wav:
                rate = wav.getframerate()
                sample_count = wav.getnframes()
        elif path.suffix.lstrip('.').lower() == 'mp3':
            audio = MP3(path)
            rate = audio.info.sample_rate
            sample_count = int(round(rate * audio.info.length))
            
        self.current_target.sounds.append(components.Sound(
            assetId=hash,
            name=name,
            md5ext=hash + '.' + suffix,
            dataFormat=suffix,
            rate=rate,
            sampleCount=sample_count
        ))
        self.assets.append((hash + '.' + suffix,path))

    def option(self,name):
        if self.available_options_stack[-1] is not None:
            return self.available_options_stack[-1]._member_map_[name]
        raise NameError(f'Option {name} not found')
        
    def identifier(self,name): return name

    def event(self,hat,position,chain):
        @self._secondary_decorator
        def secondary():
            nonlocal hat,chain
            x,y = self.visit(position)
            hat = self.visit(hat)
            chain = self.visit(chain)
            self._block_by_id(hat).topLevel = True
            self._block_by_id(hat).next = chain
            self._block_by_id(hat).x = x
            self._block_by_id(hat).y = y
            if chain is not None:
                self._block_by_id(chain).parent = hat

    def procedure(self,name,*args):
        *args,position,chain = args
        self._create_procedure(name,chain,position,*args,warp=False)

    def warp_procedure(self,name,*args):
        *args,position,chain = args
        self._create_procedure(name,chain,position,*args,warp=True)

    def string_argument(self,name):
        return name,ArgumentType.STRING
    
    def bool_argument(self,name):
        return name,ArgumentType.BOOL
    
    def position(self,x=0,y=0):
        return int(x),int(y)

    def chain(self,*blocks):
        blocks = list(map(self.visit,blocks))
        for n,block in enumerate(blocks):
            if n > 0: self._block_by_id(blocks[n - 1]).next = block
            if n + 1 < len(blocks): self._block_by_id(blocks[n + 1]).parent = block
        if len(blocks):
            return blocks[0]

    def statement_block(self,name,*args):
        *args,comment = args
        return self._transform_block(self.block_stack[-1].get_statement(name),comment,*args)
    
    def reporter_block(self,name,*args):
        *args,comment = args
        return self._transform_block(self.block_stack[-1].get_reporter(name),comment,*args)
    
    def hat_block(self,name,*args):
        *args,comment = args
        return self._transform_block(self.block_stack[-1].get_hat(name),comment,*args)

    def int(self,value):
        return int(value)
    
    def float(self,value):
        return float(value)
    
    def string(self,value):
        return str(value[1:-1])
    
    def color(self,value):
        return str(value)
    
    def true(self):
        return True
    
    def false(self):
        return False


def transform(tree: Tree) -> components.Project:
    builder = ScratchFileBuilder()
    builder.visit(tree)
    return builder

def transpile(source: str,target: Path | str,source_dir: Optional[dict | str] = None):
    target = str(target)
    builder = ScratchFileBuilder(Path(source_dir))
    builder.visit(parse(source))
    builder.save(target)

def transpile_file(source: Path | str,target: Path | str):
    with open(str(source)) as file:
        transpile(file.read(),target,Path(source).parent)