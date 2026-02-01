from .module_type import HysysModuleType
from ..constants import _NAME_STR, _TYPE_STR
from typing import Optional
from ..types.object import HysysObject

PropDict = dict[str, str]

class HysysModule(HysysObject):
    @staticmethod
    def _set_loader(loader):
        HysysModule._loader = loader

    def  __init__(self, object: any, type: HysysModuleType):
        super().__init__(object)
        self._type = type

    @staticmethod
    def from_hysys_obj(obj: HysysObject) -> Optional[HysysModule]:
        return HysysModule._loader.get_module(obj.name())

    def _prop_dict(self) -> PropDict:
        prop_dict = HysysModule._loader.get_prop_dict(self._type)

        if self._type == HysysModuleType.UNIT_OPERATION:
            operation_type = getattr(self._object, _TYPE_STR)
            prop_dict = prop_dict.get(operation_type)

        return prop_dict

    def attr(self, user_prop: str) -> Optional[HysysObject]:
        hysys_prop = self._prop_dict().get(user_prop)

        result = HysysModule._loader \
            ._object_constructor(getattr(self._object, hysys_prop))

        module = HysysModule._loader \
            .get_module(result.name())

        if module is not None:
            return module

        return result

    def attrs(self) -> tuple[str]:
        return tuple(self._prop_dict().keys())