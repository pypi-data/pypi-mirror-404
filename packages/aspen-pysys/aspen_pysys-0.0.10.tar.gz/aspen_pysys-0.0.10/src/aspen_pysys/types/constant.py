from .non_module import HysysNonModule
from .object_type import HysysObjectType

class HysysConstant(HysysNonModule):
    def __init__(self, object, object_type=HysysObjectType.CONSTANT):
        super().__init__(object, object_type)

    def __str__(self):
        return str(self.get())

    def get(self) -> any:
        return self._object