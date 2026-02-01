from .types import HysysObject, HysysObjManager
from .modules import HysysModule
from .app import Hysys

def setup():
    HysysObject._set_constructor(HysysObjManager.construct)
    HysysModule._set_loader(Hysys)
    Hysys.init(HysysObjManager.construct)