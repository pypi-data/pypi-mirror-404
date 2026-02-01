from pywintypes import com_error
import win32api

from typing import Optional
from ..constants import _VALUE_STR, _VALUES_STR, _NAMES_STR, _GET_VALUES_STR
from .object import HysysObject
from .constant import HysysConstant
from .array import HysysArray
from .dictionary import HysysDict

primitive_types = (bool, str, int, float)
collection_types = (list, tuple)

class HysysObjManager:
    @staticmethod
    def construct(obj: any) -> Optional[HysysObject]:
        if obj is None:
            return None

        if isinstance(obj, primitive_types):
            return HysysConstant(obj)

        if hasattr(obj, _VALUE_STR):
            return HysysConstant(getattr(obj, _VALUE_STR))

        if isinstance(obj, collection_types):
            return HysysArray(obj)

        try:
            if hasattr(obj, _VALUES_STR):
                getter = getattr(obj, _GET_VALUES_STR)
                return HysysArray(getter())

            if hasattr(obj, _NAMES_STR):
                return HysysDict(obj)
        except:
            return None

        return HysysObject(obj)