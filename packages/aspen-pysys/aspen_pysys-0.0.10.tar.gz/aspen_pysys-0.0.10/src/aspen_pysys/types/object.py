from typing import Optional
from ..constants import _NAME_STR
from .object_type import HysysObjectType

class HysysObject:
    @staticmethod
    def _set_constructor(func):
        HysysObject._constructor = func

    def __init__(self, object, object_type=HysysObjectType.OBJECT):
        self._object = object
        self._obj_type = object_type

    def type(self) -> HysysObjectType:
        return self._obj_type

    def name(self) -> str:
        return str(getattr(self._object, _NAME_STR)) if hasattr(self._object, _NAME_STR) else "None"

    def __str__(self):
        return self.name()

