from ..module import HysysModule
from ..module_type import HysysModuleType

class EnergyStream(HysysModule):
    def  __init__(self, object: any):
        super().__init__(object, HysysModuleType.ENERGY_STREAM)