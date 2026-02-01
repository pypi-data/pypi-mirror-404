from composition import Composition

class MaterialStreamProps:
    def __init__(self, temperature, pressure, flow, composition: Composition):
        self._temperature = temperature
        self._pressure = pressure
        self._flow = flow
        self._composition = composition