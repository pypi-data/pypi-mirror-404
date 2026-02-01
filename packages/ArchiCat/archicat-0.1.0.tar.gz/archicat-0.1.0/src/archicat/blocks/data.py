from ..block import *
from ..extension import Extension


class VariableMonitor(Monitor):
    def __call__(self,builder: 'ScratchFileBuilder',variable: str,mode: str = 'default',
                 sliderMin: int = 0,sliderMax: int = 100,isDiscrete: bool = True,**kwargs) -> components.Monitor:
        monitor = super().__call__(builder,**kwargs)
        monitor.id = builder._get_variable(variable)
        monitor.params = {'VARIABLE': variable}
        if not builder.current_target.isStage:
            monitor.spriteName = builder.current_target.name
        monitor.mode = mode
        monitor.sliderMin = sliderMin
        monitor.sliderMax = sliderMax
        monitor.isDiscrete = isDiscrete
        return monitor
    
class ListMonitor(Monitor):
    def __call__(self,builder: 'ScratchFileBuilder',list: str,width: int = 100,height: int = 200,**kwargs) -> components.ListMonitor:
        monitor = super().__call__(builder,**kwargs)
        monitor.id = builder._get_list(list)
        monitor.params = {'LIST': list}
        if not builder.current_target.isStage:
            monitor.spriteName = builder.current_target.name
        monitor.mode = 'list'
        monitor.value = []
        monitor.width = width
        monitor.height = height
        return monitor

ARCHICAT_EXTENSION = Extension('data')

ARCHICAT_EXTENSION.create_statements(
    Block('data_setvariableto',VARIABLE=variable_field,VALUE=string_input),
    Block('data_changevariableby',VARIABLE=variable_field,VALUE=float_input),
    Block('data_showvariable',VARIABLE=variable_field),
    Block('data_hidevariable',VARIABLE=variable_field),
    Block('data_addtolist',LIST=list_field,ITEM=string_input),
    Block('data_deleteoflist',LIST=list_field,INDEX=unsigned_int_input),
    Block('data_deletealloflist',LIST=list_field),
    Block('data_insertatlist',LIST=list_field,INDEX=unsigned_int_input,ITEM=string_input),
    Block('data_replaceitemoflist',LIST=list_field,INDEX=unsigned_int_input,ITEM=string_input),
    Block('data_showlist',LIST=list_field),
    Block('data_hidelist',LIST=list_field),
    access=BlockAccessModifier.ALL
)

ARCHICAT_EXTENSION.create_reporters(
    Block('data_variable',VARIABLE=variable_field),
    Block('data_listcontents',LIST=list_field),
    Block('data_itemoflist',LIST=list_field,INDEX=unsigned_int_input),
    Block('data_itemnumoflist',LIST=list_field,ITEM=string_input),
    Block('data_lengthoflist',LIST=list_field),
    Block('data_listcontainsitem',LIST=list_field,ITEM=string_input),
    access=BlockAccessModifier.ALL
)

ARCHICAT_EXTENSION.create_monitors(
    VariableMonitor('data_variable'),
    ListMonitor('data_listcontents')
)