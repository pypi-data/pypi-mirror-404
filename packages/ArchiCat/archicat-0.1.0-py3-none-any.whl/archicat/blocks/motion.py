from ..block import *
from ..extension import Extension

from enum import Enum

class GotoOptions(Enum):
    RANDOM = '_random_'
    MOUSE = '_mouse_'

class SetRotationStyleOptions(Enum):
    ALL_AROUND = 'all around'
    LEFT_RIGHT = 'left-right'
    DONT_ROTATE = 'don\'t rotate'

ARCHICAT_EXTENSION = Extension('motion')

ARCHICAT_EXTENSION.create_statements(
    Block('motion_movesteps',STEPS=float_input),
    Block('motion_turnright',DEGREES=float_input),
    Block('motion_turnleft',DEGREES=float_input),
    Block('motion_goto',TO=option_input(GotoOptions,GotoOptions.MOUSE,
                                        Block('motion_goto_menu',TO=option_field(GotoOptions)))).attach_options(GotoOptions),
    Block('motion_gotoxy',X=float_input,Y=float_input),
    Block('motion_glideto',TO=option_input(GotoOptions,GotoOptions.RANDOM,
                                           Block('motion_glideto_menu',TO=option_field(GotoOptions)))).attach_options(GotoOptions),
    Block('motion_pointindirection',DIRECTION=angle_input),
    Block('motion_pointtowards',TO=option_input(GotoOptions,GotoOptions.RANDOM,
                                                Block('motion_pointtowardsmenu',TO=option_field(GotoOptions)))).attach_options(GotoOptions),
    Block('motion_changexby',DX=float_input),
    Block('motion_setx',X=float_input),
    Block('motion_changeyby',DY=float_input),
    Block('motion_sety',Y=float_input),
    Block('motion_setrotationstyle',STYLE=option_field(SetRotationStyleOptions)).attach_options(SetRotationStyleOptions),
    Block('motion_ifonedgebounce'),
    access=BlockAccessModifier.SPRITE,
)

ARCHICAT_EXTENSION.create_reporters(
    Block('motion_xposition'),
    Block('motion_yposition'),
    Block('motion_direction'),
    access=BlockAccessModifier.SPRITE,
)

ARCHICAT_EXTENSION.create_monitors(
    SpriteSpecificMonitor('motion_xposition'),
    SpriteSpecificMonitor('motion_yposition'),
    SpriteSpecificMonitor('motion_direction'),
    access=BlockAccessModifier.SPRITE
)