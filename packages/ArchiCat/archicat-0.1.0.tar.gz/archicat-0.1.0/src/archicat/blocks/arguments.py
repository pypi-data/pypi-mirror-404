from ..block import *
from ..extension import Extension

ARCHICAT_EXTENSION = Extension('arguments')

ARCHICAT_EXTENSION.create_reporters(
    Block('argument_reporter_boolean',VALUE=field),
    Block('argument_reporter_string_number',VALUE=field),
    access=BlockAccessModifier.ALL
)