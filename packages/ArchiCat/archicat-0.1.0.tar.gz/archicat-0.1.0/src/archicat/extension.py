from .block import *

from pathlib import Path
from pkgutil import iter_modules
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transformer import ScratchFileBuilder

type ExtensionBlockDict = dict[str,tuple[Block,BlockAccessModifier]]


class Extension:
    name: str
    statement_blocks: ExtensionBlockDict
    reporter_blocks: ExtensionBlockDict
    hat_blocks: ExtensionBlockDict
    monitors: dict[str,tuple[Monitor,BlockAccessModifier]]

    def __init__(self,name: str = ''):
        self.name = name.lower()
        self.statement_blocks = {}
        self.reporter_blocks = {}
        self.hat_blocks = {}
        self.monitors = {}

    def _format_name(self,name: str) -> str:
        return name.lower().removeprefix(self.name + '_').replace('_','')

    def create_statement(self,name: str,block: Block,access: BlockAccessModifier = BlockAccessModifier.ALL):
        self.statement_blocks[self._format_name(name)] = (block,access)

    def create_reporter(self,name: str,block: Block,access: BlockAccessModifier = BlockAccessModifier.ALL):
        self.reporter_blocks[self._format_name(name)] = (block,access)

    def create_hat(self,name: str,block: Block,access: BlockAccessModifier = BlockAccessModifier.ALL):
        self.hat_blocks[self._format_name(name)] = (block,access)

    def create_monitor(self,name: str,monitor: Monitor,access: BlockAccessModifier = BlockAccessModifier.ALL):
        self.monitors[self._format_name(name)] = (monitor,access)

    def create_statements(self,*blocks: Monitor,access: BlockAccessModifier = BlockAccessModifier.ALL):
        for block in blocks:
            self.create_statement(block.opcode,block,access)

    def create_reporters(self,*blocks: Block,access: BlockAccessModifier = BlockAccessModifier.ALL):
        for block in blocks:
            self.create_reporter(block.opcode,block,access)

    def create_hats(self,*blocks: Block,access: BlockAccessModifier = BlockAccessModifier.ALL):
        for block in blocks:
            self.create_hat(block.opcode,block,access)

    def create_monitors(self,*monitors: Monitor,access: BlockAccessModifier = BlockAccessModifier.ALL):
        for monitor in monitors:
            self.create_monitor(monitor.opcode,monitor,access)

    def has_statement(self,name: str,context: BlockAccessModifier) -> bool:
        return self._format_name(name) in self.statement_blocks and \
            ((access := self.statement_blocks[self._format_name(name)][1]) == context or access == BlockAccessModifier.ALL)
    
    def has_reporter(self,name: str,context: BlockAccessModifier) -> bool:
        return self._format_name(name) in self.reporter_blocks and \
            ((access := self.reporter_blocks[self._format_name(name)][1]) == context or access == BlockAccessModifier.ALL)
    
    def has_hat(self,name: str,context: BlockAccessModifier) -> bool:
        return self._format_name(name) in self.hat_blocks and \
            ((access := self.hat_blocks[self._format_name(name)][1]) == context or access == BlockAccessModifier.ALL)
    
    def has_monitor(self,name: str,context: BlockAccessModifier) -> bool:
        return self._format_name(name) in self.monitors and \
            ((access := self.monitors[self._format_name(name)][1]) == context or access == BlockAccessModifier.ALL)

    def get_statement(self,name: str) -> Block:
        return self.statement_blocks[self._format_name(name)][0]
    
    def get_reporter(self,name: str) -> Block:
        return self.reporter_blocks[self._format_name(name)][0]
    
    def get_hat(self,name: str) -> Block:
        return self.hat_blocks[self._format_name(name)][0]
    
    def get_monitor(self,name: str) -> Monitor:
        return self.monitors[self._format_name(name)][0]
    

class ExtensionManager:
    src: str
    extensions: list[Extension]
    builder: 'ScratchFileBuilder'

    def __init__(self,builder: 'ScratchFileBuilder',src: str = 'archicat.blocks'):
        self.src = src
        self.builder = builder
        self.extensions = []
        
        for module in iter_modules(import_module(self.src).__path__):
            if not module.ispkg:
                self.extensions.append(import_module(f'{self.src}.{module.name}').ARCHICAT_EXTENSION)

    def load_extension(self,name: str):
        self.extensions.append(extension := import_module(f'{self.src}.extensions.{name}').ARCHICAT_EXTENSION)
        self.builder.project.extensions.append(extension.name)

    def add_extension(self,extension: Extension):
        self.extensions.append(extension)

    def update(self,name: str,extension: Extension):
        new = ExtensionManager(self.builder,self.src)
        for new_extension in self.extensions:
            if new_extension.name == name:
                new.add_extension(extension)
            else:
                new.add_extension(new_extension)
        return new

    def get_extension(self,name: str) -> Extension:
        return next(extension for extension in self.extensions if extension.name == name)

    def get_statement(self,name: str) -> Block:
        for extension in self.extensions:
            if extension.has_statement(name,BlockAccessModifier.STAGE 
                                       if self.builder.current_target.isStage else 
                                       BlockAccessModifier.SPRITE):
                return extension.get_statement(name)
            
    def get_reporter(self,name: str) -> Block:
        for extension in self.extensions:
            if extension.has_reporter(name,BlockAccessModifier.STAGE 
                                       if self.builder.current_target.isStage else 
                                       BlockAccessModifier.SPRITE):
                return extension.get_reporter(name)
            
    def get_hat(self,name: str) -> Block:
        for extension in self.extensions:
            if extension.has_hat(name,BlockAccessModifier.STAGE 
                                       if self.builder.current_target.isStage else 
                                       BlockAccessModifier.SPRITE):
                return extension.get_hat(name)
            
    def get_monitor(self,name: str) -> Monitor:
        for extension in self.extensions:
            if extension.has_monitor(name,BlockAccessModifier.STAGE
                                        if self.builder.current_target.isStage else
                                        BlockAccessModifier.SPRITE):
                return extension.get_monitor(name)
    
