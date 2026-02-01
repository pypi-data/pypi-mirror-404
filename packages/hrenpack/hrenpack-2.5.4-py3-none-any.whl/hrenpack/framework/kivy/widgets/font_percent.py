from typing import Optional, Union, Literal
from kivy.core.window import Window
from hrenpack.framework.kivy.widgets import BoxLayout, Label, Button


class FontPercentLabel(Label):
    def __init__(self, text='', parent=None, font_size_cof: float = 0.02, **kwargs):
        super().__init__(text, parent, **kwargs)
        fs = self.font_size
        self.font_size = max(fs, Window.size[0] * font_size_cof)


class FontPercentButton(Button):
    def __init__(self, text: str = '', parent=None, command=None, font_size_cof: float = 0.02, **kwargs):
        super().__init__(text, parent, command, **kwargs)
        fs = self.font_size
        self.font_size = max(fs, Window.size[0] * font_size_cof)
