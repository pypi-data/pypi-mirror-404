from component import Component
# from helpers import get_molar_frac_label

class Composition:
    def __init__(self, components: tuple[Component]):
        self._data = {comp: 0.0 for comp in components}

    def update(self, component: Component, value):
        if Composition._is_valid(value):
            self._data[component] = value

    # def to_dict(self):
    #     return {get_molar_frac_label(comp): value for (comp, value) in self._data.items()}

    # TODO: Checks validity for only molar frac
    @staticmethod
    def _is_valid(value):
        return 0.0 <= value <= 1.0