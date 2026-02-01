from ..block import *
from ..extension import Extension

from enum import Enum

def _operation(opcode):
    return Block(opcode,NUM1=float_input,NUM2=float_input)

def _comparison(opcode):
    return Block(opcode,OPERAND1=float_input,OPERAND2=float_input)

def _bool_operation(opcode):
    return Block(opcode,OPERAND1=bool_input,OPERAND2=bool_input)

class MathOpOptions(Enum):
    ABS = 'abs'
    FLOOR = 'floor'
    CEILING = 'ceiling'
    SQRT = 'sqrt'
    SIN = 'sin'
    COS = 'cos'
    TAN = 'tan'
    ASIN = 'asin'
    ACOS = 'acos'
    ATAN = 'atan'
    POWER_E = 'e ^'
    POWER_10 = '10 ^'

ARCHICAT_EXTENSION = Extension('operator')

ARCHICAT_EXTENSION.create_reporters(
    _operation('operator_add'),
    _operation('operator_subtract'),
    _operation('operator_multiply'),
    _operation('operator_divide'),
    Block('operator_random',FROM=float_input,TO=float_input),
    _comparison('operator_equals'),
    _comparison('operator_gt'),
    _comparison('operator_lt'),
    _bool_operation('operator_and'),
    _bool_operation('operator_or'),
    Block('operator_not',OPERAND=bool_input),
    Block('operator_join',STRING1=string_input,STRING2=string_input),
    Block('operator_letter_of',STRING=string_input),
    Block('operator_length',STRING=string_input),
    _operation('operator_mod'),
    Block('operator_round',NUM=float_input),
    Block('operator_mathop',OPERATION=option_field(MathOpOptions),NUM=float_input).attach_options(MathOpOptions),
    access=BlockAccessModifier.ALL
)