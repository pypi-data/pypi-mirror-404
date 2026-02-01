from ..block import *
from ..extension import Extension

from enum import Enum

class WhenGreaterThanOptions(Enum):
    LOUDNESS = 'LOUDNESS'
    TIMER = 'TIMER'

ARCHICAT_EXTENSION = Extension('event')

ARCHICAT_EXTENSION.create_statements(
    Block('event_broadcast',BROADCAST_INPUT=message_input),
    Block('event_broadcastandwait',BROADCAST_INPUT=message_input),
    access=BlockAccessModifier.ALL,
)

ARCHICAT_EXTENSION.create_hats(
    Block('event_whenflagclicked'),
    Block('event_whenkeypressed',KEY_OPTION=field),
    Block('event_whenbackdropswitchesto',backdrop=costume_field),
    Block('event_whengreaterthan',WHENGREATERTHANMENU=option_field(WhenGreaterThanOptions),VALUE=unsigned_float_input
          ).attach_options(WhenGreaterThanOptions),
    Block('event_whenbroadcastreceived',BROADCAST_OPTION=message_field),
    access=BlockAccessModifier.ALL,
)

ARCHICAT_EXTENSION.create_hats(
    Block('event_whenthisspriteclicked'),
    access=BlockAccessModifier.SPRITE,
)

ARCHICAT_EXTENSION.create_hats(
    Block('event_whenstageclicked'),
    access=BlockAccessModifier.STAGE,
)