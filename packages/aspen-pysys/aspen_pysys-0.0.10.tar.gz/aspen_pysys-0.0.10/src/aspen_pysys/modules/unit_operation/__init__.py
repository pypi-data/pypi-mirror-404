from ..module import HysysModule
from ..module_type import HysysModuleType
from ...constants import _TYPE_STR

class UnitOperation(HysysModule):
    def  __init__(self, object: any):
        super().__init__(object, HysysModuleType.UNIT_OPERATION)

    def operation_type(self) -> str:
        return self.attr(_TYPE_STR)