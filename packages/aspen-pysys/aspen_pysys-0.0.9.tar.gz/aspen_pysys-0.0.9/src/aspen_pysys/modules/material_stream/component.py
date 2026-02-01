class Component:
    def __init__(self, full_name: str, short_name: str):
        self._full_name = full_name
        self._short_name = short_name

    def __eq__(self, value):
        return self._full_name.lower() == value.lower()

    def get_full_name(self):
        return self._full_name

    def get_short_name(self):
        return self._short_name

    # TODO: Return a new HysysComponent instead?
    def set_short_name(self, text):
        self.set_short_name = text