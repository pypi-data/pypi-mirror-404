from typing import Optional
from ..constants import _NAMES_STR
from .object import HysysObject
from .object_type import HysysObjectType
from .non_module import HysysNonModule

class HysysDict(HysysNonModule):
    def __init__(self, object):
        super().__init__(object, HysysObjectType.DICT)

    def __str__(self):
        return str(getattr(self._object, _NAMES_STR))

    def dict(self) -> dict[str, any]:
        return {key: self.get(key) for key in self.keys()}

    def keys(self) -> tuple[str]:
        return getattr(self._object, _NAMES_STR)

    def contains(self, key: str) -> bool:
        return key in self.keys()

    def get(self, key: str) -> Optional[HysysObject]:
        if self.contains(key):
            value = self._object.Item(key)
            return HysysObject._constructor(value)

        return None