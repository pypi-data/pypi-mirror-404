from ..block import *
from ..extension import Extension

from enum import Enum

class EffectOptions(Enum):
    PITCH = 'PITCH'
    PAN = 'PAN'

ARCHICAT_EXTENSION = Extension('sound')

ARCHICAT_EXTENSION.create_statements(
    Block('sound_playuntildone',SOUND_MENU=sound_input),
    Block('sound_play',SOUND_MENU=sound_input),
    Block('sound_changeeffectby',EFFECT=option_field(EffectOptions),CHANGE=float_input).attach_options(EffectOptions),
    Block('sound_seteffectto',EFFECT=option_field(EffectOptions),VALUE=unsigned_float_input).attach_options(EffectOptions),
    Block('sound_cleareffects'),
    Block('sound_changevolumeby',VOLUME=float_input),
    Block('sound_setvolumeto',VOLUME=float_input),
    access=BlockAccessModifier.ALL,
)

ARCHICAT_EXTENSION.create_reporters(
    Block('sound_volume'),
    access=BlockAccessModifier.ALL,
)

ARCHICAT_EXTENSION.create_monitors(
    SpriteSpecificMonitor('sound_volume'),
    access=BlockAccessModifier.ALL
)