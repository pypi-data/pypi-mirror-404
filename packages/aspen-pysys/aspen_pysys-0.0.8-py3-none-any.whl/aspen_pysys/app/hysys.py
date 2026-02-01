from typing import Optional
import win32com.client as win32
from pywintypes import com_error

from ..constants import _TYPE_STR
from ..types import HysysObject
from ..modules import HysysModuleType, HysysModule, MaterialStream, EnergyStream, UnitOperation
from .helpers import convert_to_user_prop

PropDict = dict[str, str]

class Hysys:
    _app = None
    _active_flowsheet = None

    _names: dict[HysysModuleType, tuple[str]] = {
        HysysModuleType.MATERIAL_STREAM: (),
        HysysModuleType.ENERGY_STREAM: (),
        HysysModuleType.UNIT_OPERATION: ()
    }

    _prop_dict: Optional[dict[HysysModuleType, PropDict | dict[str, PropDict]]] = {
        HysysModuleType.MATERIAL_STREAM: dict(),
        HysysModuleType.ENERGY_STREAM: dict(),
        HysysModuleType.UNIT_OPERATION: dict()
    }

    _object_constructor: function[any, Optional[HysysObject]]

    @staticmethod
    def init(object_constructor: function[any, Optional[HysysObject]]) -> None:
        try:
            Hysys._app = win32.gencache.EnsureDispatch('HYSYS.Application')
            Hysys._active_flowsheet = Hysys._app.ActiveDocument.Flowsheet
            Hysys._object_constructor = object_constructor

            Hysys.load_object_names()
            Hysys._load_prop_dict()

            print(Hysys._app)
        except com_error as e:
            print(e)
        except Exception as e:
            print(e)

    @staticmethod
    def refresh() -> None:
        Hysys.init(Hysys._object_constructor)

    @staticmethod
    def load_object_names() -> None:
        Hysys._names.update({
            HysysModuleType.MATERIAL_STREAM: Hysys._active_flowsheet.MaterialStreams.Names
        })

        Hysys._names.update({
            HysysModuleType.ENERGY_STREAM: Hysys._active_flowsheet.EnergyStreams.Names
        })

        Hysys._names.update({
            HysysModuleType.UNIT_OPERATION: Hysys._active_flowsheet.Operations.Names
        })

    @staticmethod
    def _load_prop_dict() -> None:
        Hysys._prop_dict.update({
            HysysModuleType.MATERIAL_STREAM: Hysys._load_material_stream_props()
        })

        Hysys._prop_dict.update({
            HysysModuleType.ENERGY_STREAM: Hysys._load_energy_stream_props()
        })

        Hysys._prop_dict.update({
            HysysModuleType.UNIT_OPERATION: Hysys._load_operation_props()
        })

    @staticmethod
    def get_prop_dict(module_type: HysysModuleType):
        return Hysys._prop_dict.get(module_type)

    @staticmethod
    def get_module(module_name: str) -> Optional[HysysModule]:
        if module_name in Hysys.get_names(HysysModuleType.MATERIAL_STREAM):
            com_object = Hysys._active_flowsheet.MaterialStreams.Item(module_name)
            return MaterialStream(com_object)
        elif module_name in Hysys.get_names(HysysModuleType.ENERGY_STREAM):
            com_object = Hysys._active_flowsheet.EnergyStreams.Item(module_name)
            return EnergyStream(com_object)
        elif module_name in Hysys.get_names():
            com_object = Hysys._active_flowsheet.Operations.Item(module_name)
            return UnitOperation(com_object)

        return None

    @staticmethod
    def get_names(module_type: HysysModuleType=None) -> list[str]:
        if module_type is not None:
            return Hysys._names.get(module_type)

        return (name for names in Hysys._names.values() for name in names)

    @staticmethod
    def _load_operation_props():
        prop_dict_by_type = dict()

        # TODO: Find an alternative to load operation props
        for operation in Hysys._active_flowsheet.Operations:
            operation_type = operation.VisibleTypeName

            if operation_type not in prop_dict_by_type:
                prop_list = dir(operation)
                prop_dict = dict()

                for prop in prop_list:
                    if not prop.startswith("_"):
                        readable_prop = convert_to_user_prop(prop)
                        prop_dict.update({readable_prop: prop})

                prop_dict_by_type.update({operation_type: prop_dict})

        return prop_dict_by_type

    @staticmethod
    def _load_material_stream_props():
        prop_dict = dict()

        # TODO: Find an alternative to load material stream props
        for prop in dir(Hysys._active_flowsheet.MaterialStreams.Item(0)):
            if not prop.startswith("_"):
                readable_prop = convert_to_user_prop(prop)
                prop_dict.update({readable_prop: prop})

        return prop_dict

    @staticmethod
    def _load_energy_stream_props():
        prop_dict = dict()

        # TODO: Find an alternative to load energy stream props
        for prop in dir(Hysys._active_flowsheet.EnergyStreams.Item(0)):
            if not prop.startswith("_"):
                readable_prop = convert_to_user_prop(prop)
                prop_dict.update({readable_prop: prop})

        return prop_dict