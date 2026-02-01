from ..block import *
from ..extension import Extension

from enum import Enum
from typing import Optional

class StopOptions(Enum):
    ALL = 'all'
    THIS_SCRIPT = 'this script'
    OTHER_SCRIPTS = 'other scripts in sprite'

class CreateCloneOfOptions(Enum):
    MYSELF = '_myself_'

class StopBlock(Block):
    def __call__(self,builder: 'ScratchFileBuilder',*args: InputItem | StopOptions,id: Optional[components.Id] = None) -> components.Id:
        id = super().__call__(builder,*args,id=id)
        block = builder._block_by_id(id)
        if StopOptions(block.fields['STOP_OPTION'].value) == StopOptions.OTHER_SCRIPTS:
            block.mutation = components.ControlStop()
        else:
            block.mutation = components.ControlStop(hasnext=components.HasNext.FALSE)
        return id

ARCHICAT_EXTENSION = Extension('control')

ARCHICAT_EXTENSION.create_statements(
    Block('control_wait',DURATION=unsigned_float_input),
    Block('control_repeat',TIMES=unsigned_int_input,SUBSTACK=chain_input),
    Block('control_forever',SUBSTACK=chain_input,
          mutation=components.ControlStop(hasnext=components.HasNext.FALSE)),
    Block('control_if',CONDITION=bool_input,SUBSTACK=chain_input),
    Block('control_if_else',CONDITION=bool_input,SUBSTACK=chain_input,SUBSTACK2=chain_input),
    Block('control_wait_until',CONDITION=bool_input),
    Block('control_repeat_until',CONDITION=bool_input,SUBSTACK=chain_input),
    StopBlock('control_stop',STOP_OPTION=option_field(StopOptions)).attach_options(StopOptions),
    Block('control_create_clone_of',CLONE_OPTION=option_input(CreateCloneOfOptions,CreateCloneOfOptions.MYSELF,
            Block('control_create_clone_of_options',CLONE_OPTIONS=option_field(CreateCloneOfOptions)))
    ).attach_options(CreateCloneOfOptions),
    access=BlockAccessModifier.ALL
)

ARCHICAT_EXTENSION.create_statements(
    Block('control_delete_this_clone',
          mutation=components.ControlStop(hasnext=components.HasNext.FALSE))
)

ARCHICAT_EXTENSION.create_hats(
    Block('control_start_as_clone'),
    access=BlockAccessModifier.SPRITE
)