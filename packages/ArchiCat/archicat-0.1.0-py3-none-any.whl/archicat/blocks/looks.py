from ..block import *
from ..extension import Extension

from enum import Enum

class SwitchBackdropToOptions(Enum):
    NEXT_BACKDROP = 'next backdrop'
    PREVIOUS_BACKDROP = 'previous backdrop'
    RANDOM_BACKDROP = 'random backdrop'

class EffectOptions(Enum):
    COLOR = 'COLOR'
    FISHEYE = 'FISHEYE'
    WHIRL = 'WHIRL'
    PIXELATE = 'PIXELATE'
    MOSAIC = 'MOSAIC'
    BRIGHTNESS = 'BRIGHTNESS'
    GHOST = 'GHOST'

class GoToFrontBackOptions(Enum):
    FRONT = 'front'
    BACK = 'back'

class GoForwardBackwardLayersOptions(Enum):
    FORWARD = 'forward'
    BACKWARD = 'backward'

class NumberNameOptions(Enum):
    NUMBER = 'number'
    NAME = 'name'


class BackdropNumberNameMonitor(Monitor):
    def __call__(self,builder: 'ScratchFileBuilder',option: str | NumberNameOptions,**kwargs) -> components.ListMonitor:
        monitor = super().__call__(builder,**kwargs)
        option = NumberNameOptions(option)
        monitor.id = monitor.id + '_' + option.value
        monitor.params = {'NUMBER_NAME': option}
        return monitor
    

class CostumeNumberNameMonitor(BackdropNumberNameMonitor,SpriteSpecificMonitor): pass


ARCHICAT_EXTENSION = Extension('looks')

ARCHICAT_EXTENSION.create_statements(
    Block('looks_switchbackdropto',BACKDROP=option_input(SwitchBackdropToOptions,SwitchBackdropToOptions.NEXT_BACKDROP,
                                                         Block('looks_backdrop',BACKDROP=option_field(SwitchBackdropToOptions)))
            ).attach_options(SwitchBackdropToOptions),
    access=BlockAccessModifier.ALL,
)

ARCHICAT_EXTENSION.create_statements(
    Block('looks_sayforsecs',MESSAGE=string_input,SECS=unsigned_float_input),
    Block('looks_say',MESSAGE=string_input),
    Block('looks_thinkforsecs',MESSAGE=string_input,SECS=unsigned_float_input),
    Block('looks_think',MESSAGE=string_input),
    Block('looks_switchcostumeto',COSTUME=costume_input),
    Block('looks_nextcostume'),
    Block('looks_changesizeby',SIZE=float_input),
    Block('looks_setsizeto',SIZE=unsigned_float_input),
    Block('looks_changeeffectby',EFFECT=option_field(EffectOptions),CHANGE=float_input).attach_options(EffectOptions),
    Block('looks_seteffect',EFFECT=option_field(EffectOptions),VALUE=unsigned_float_input).attach_options(EffectOptions),
    Block('looks_cleargraphicseffect'),
    Block('looks_show'),
    Block('looks_hide'),
    Block('looks_gotofrontback',FRONT_BACK=option_field(GoToFrontBackOptions)).attach_options(GoToFrontBackOptions),
    Block('looks_goforwardbackwardlayers',FORWARD_BACKWARD=option_field(GoForwardBackwardLayersOptions)
          ).attach_options(GoForwardBackwardLayersOptions),
    access=BlockAccessModifier.SPRITE,
)

ARCHICAT_EXTENSION.create_statements(
    Block('looks_switchbackdroptoandwait',BACKDROP=option_input(SwitchBackdropToOptions,SwitchBackdropToOptions.NEXT_BACKDROP,
                                                                Block('looks_backdrops',BACKDROP=option_field(SwitchBackdropToOptions)))
            ).attach_options(SwitchBackdropToOptions),
    access=BlockAccessModifier.STAGE,
)

ARCHICAT_EXTENSION.create_reporters(
    Block('looks_backdropnumbername',NUMBER_NAME=option_field(NumberNameOptions)).attach_options(NumberNameOptions),
    access=BlockAccessModifier.ALL,
)

ARCHICAT_EXTENSION.create_reporters(
    Block('looks_costumenumbername',NUMBER_NAME=option_field(NumberNameOptions)).attach_options(NumberNameOptions),
    Block('looks_size'),
    access=BlockAccessModifier.SPRITE,
)

ARCHICAT_EXTENSION.create_monitors(
    CostumeNumberNameMonitor('looks_costumenumbername').attach_options(NumberNameOptions),
    access=BlockAccessModifier.ALL
)

ARCHICAT_EXTENSION.create_monitors(
    BackdropNumberNameMonitor('looks_backdropnumbername').attach_options(NumberNameOptions),
    SpriteSpecificMonitor('looks_size'),
    access=BlockAccessModifier.SPRITE,
)