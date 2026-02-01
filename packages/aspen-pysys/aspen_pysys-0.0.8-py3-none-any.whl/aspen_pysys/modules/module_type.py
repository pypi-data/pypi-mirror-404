from enum import Enum
from typing import Optional

MATERIAL_STREAM_STR = "Material Stream"
ENERGY_STREAM_STR = "Energy Stream"
UNIT_OPERATION_STR = "Operation"

class HysysModuleType(Enum):
    MATERIAL_STREAM = 0
    ENERGY_STREAM = 1
    UNIT_OPERATION = 2

    @staticmethod
    def from_str(text: str) -> Optional[HysysModuleType]:
        if text == MATERIAL_STREAM_STR:
            return HysysModuleType.MATERIAL_STREAM
        elif text ==  ENERGY_STREAM_STR:
            return HysysModuleType.ENERGY_STREAM
        elif text ==  UNIT_OPERATION_STR:
            return HysysModuleType.UNIT_OPERATION

        return None

    def __str__(self):
        if self == HysysModuleType.MATERIAL_STREAM:
            return MATERIAL_STREAM_STR
        elif self == HysysModuleType.ENERGY_STREAM:
            return ENERGY_STREAM_STR
        elif self == HysysModuleType.UNIT_OPERATION:
            return ENERGY_STREAM_STR

        return "None"