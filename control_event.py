import pyautogui as pag
from icecream import ic

class ControlEvent:
    def __init__(self, click: bool = False, coordinates: tuple[int, int] = None, keypress: bool = False, key: str = None):
        self._click = False
        self._coordinates = None
        self._keypress = False
        self._key = None
        self.click = click
        self.coordinates = coordinates
        self.keypress = keypress
        self.key = key

    @property
    def click(self):
        return self._click

    @click.setter
    def click(self,value):
        if not isinstance(value, bool):
            raise ValueError("Value passed to click attribute of ControlEvent was not a boolean")
        if self.keypress and value:
            raise ValueError("A keypress for this specific ControlEvent exists so a click could not be assigned.")
        self._click = value

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self,value):
        if not self.click and value:
            raise ValueError("A set of coordinates could not be assigned because ControlEvent is not a click")
        self._coordinates = value

    @property
    def keypress(self):
        return self._keypress

    @keypress.setter
    def keypress(self,value):
        if not isinstance(value,bool):
            raise ValueError("Value passed to keypress attribute of ControlEvent was not a boolean")
        if self.click and value:
            raise ValueError("A click for this specific ControlEvent exists so a keypress could not be assigned.")
        self._keypress = value

    @property
    def key(self):
        return self._keypress

    @key.setter
    def key(self,value):
        ic(f"keysetter called", value)
        ic(self.keypress)
        ic(not self.keypress and value)
        if not self.keypress and value:
            raise ValueError("A key could not be assigned because ControlEvent is not a keypress")
        self._key = value

    def execute_event(self):
        if (self.click and self.keypress) or (not self.click and not self.keypress):
            raise ValueError("A ControlEvent was executed while being both states or having no states")
        if self.click:
            x,y = self.coordinates
            pag.click(x,y)
        if self.keypress:
            ic(self.key)
            pag.press(self.key)

    def __repr__(self):
        return f"ControlEvent(click={self.click}, coordinates={self.coordinates}, keypress={self.keypress}, key={self.key})"

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return 69


