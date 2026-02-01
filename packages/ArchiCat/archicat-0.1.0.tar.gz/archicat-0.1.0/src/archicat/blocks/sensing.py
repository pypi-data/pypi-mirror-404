from ..block import *
from ..extension import Extension

from enum import Enum

class TouchingObjectOptions(Enum):
    MOUSE = '_mouse_'
    EDGE = '_edge_'

class DistanceToOptions(Enum):
    MOUSE = '_mouse_'

class KeyPressedOptions(Enum):
    SPACE = 'space'
    LEFT_ARROW = 'left arrow'
    RIGHT_ARROW = 'right arrow'
    UP_ARROW = 'up arrow'
    DOWN_ARROW = 'down arrow'
    ANY = 'any'

class SetDragModeOptions(Enum):
    DRAGGABLE = 'draggable'
    NOT_DRAGGABLE = 'not draggable'

class OfPropertyOptions(Enum):
    X = 'x position'
    Y = 'y position'
    DIRECTION = 'direction'
    COSTUME_NUMBER = 'costume #'
    COSTUME_NAME = 'costume name'
    BACKDROP_NUMBER = 'backdrop #'
    BACKDROP_NAME = 'backdrop name'
    SIZE = 'size'
    VOLUME = 'volume'

class OfObjectOptions(Enum):
    STAGE = '_stage_'

class CurrentOptions(Enum):
    YEAR = 'YEAR'
    MONTH = 'MONTH'
    DATE = 'DATE'
    DAY_OF_WEEK = 'DAYOFWEEK'
    HOUR = 'HOUR'
    MINUTE = 'MINUTE'
    SECOND = 'SECOND'


class CurrentMonitor(Monitor):
    def __call__(self,builder: 'ScratchFileBuilder',option: str | CurrentOptions,**kwargs) -> components.ListMonitor:
        monitor = super().__call__(builder,**kwargs)
        option = CurrentOptions(option)
        monitor.params = {'CURRENTMENU': option}
        monitor.id += '_' + option.value.lower()
        return monitor

ARCHICAT_EXTENSION = Extension('sensing')

ARCHICAT_EXTENSION.create_statements(
    Block('sensing_askandwait',QUESTION=string_input),
    Block('sensing_resettimer'),
    access=BlockAccessModifier.ALL
)

ARCHICAT_EXTENSION.create_statements(
    Block('sensing_setdragmode',DRAG_MODE=option_field(SetDragModeOptions)).attach_options(SetDragModeOptions),
    access=BlockAccessModifier.SPRITE
)

ARCHICAT_EXTENSION.create_reporters(
    Block('sensing_answer'),
    Block('sensing_keypressed',KEY_OPTION=option_input(KeyPressedOptions,KeyPressedOptions.SPACE,
                                Block('sensing_keyoptions',KEY_OPTION=option_field(KeyPressedOptions)))).attach_options(KeyPressedOptions),
    Block('sensing_mousedown'),
    Block('sensing_mousex'),
    Block('sensing_mousey'),
    Block('sensing_loudness'),
    Block('sensing_timer'),
    Block('sensing_of',OBJECT=option_input(OfObjectOptions,OfObjectOptions.STAGE,
                        Block('sensing_of_object_menu',OBJECT=option_field(OfObjectOptions))),
                        PROPERTY=option_field(OfPropertyOptions)).attach_options(OfObjectOptions),
    Block('sensing_current',CURRENT_MENU=option_field(CurrentOptions)).attach_options(CurrentOptions),
    Block('sensing_dayssince2000'),
    Block('sensing_username'),
    access=BlockAccessModifier.ALL
)

ARCHICAT_EXTENSION.create_reporters(
    Block('sensing_touchingobject',TOUCHINGOBJECTMENU=option_input(TouchingObjectOptions,TouchingObjectOptions.MOUSE,
                                    Block('sensing_touchingobjectmenu',TOUCHINGOBJECTMENU=option_field(TouchingObjectOptions)))
            ).attach_options(TouchingObjectOptions),
    Block('sensing_touchingcolor',COLOR=color_input),
    Block('sensing_coloristouchingcolor',COLOR=color_input,COLOR2=color_input),
    Block('sensing_distanceto',DISTANCETOMENU=option_input(DistanceToOptions,DistanceToOptions.MOUSE,
                                Block('sensing_distancetomenu',DISTANCETOMENU=option_field(DistanceToOptions)))
            ).attach_options(DistanceToOptions),
    access=BlockAccessModifier.SPRITE
)

ARCHICAT_EXTENSION.create_monitors(
    Monitor('sensing_username'),
    Monitor('sensing_answer'),
    Monitor('sensing_loudness'),
    Monitor('sensing_timer'),
    access=BlockAccessModifier.ALL,
)