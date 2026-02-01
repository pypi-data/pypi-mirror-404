from .constant import HysysConstant
from .object_type import HysysObjectType

class HysysArray(HysysConstant):
    def __init__(self, object):
        super().__init__(object, HysysObjectType.ARRAY)

    def at(self, index) -> any:
        return self._object[index]