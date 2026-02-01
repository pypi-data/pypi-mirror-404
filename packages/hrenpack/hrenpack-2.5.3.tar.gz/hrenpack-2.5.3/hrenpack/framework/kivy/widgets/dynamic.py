from typing import Optional
from kivy.core.window import Window
from kivy.properties import NumericProperty
from hrenpack.listwork import dict_keyf
from hrenpack.framework.kivy.widgets import Label


class DynamicLabel(Label):
    font_size = NumericProperty(20)

    def __init__(self, text='', parent=None, mul: float = 0.03, **kwargs):
        super().__init__(text, parent, **kwargs)
        self.mul = mul
        Window.bind(size=self.update_font_size)
        self.update_font_size(num=14)

    def update_font_size(self, *args, mul: Optional[float] = None, num: Optional[int] = None):
        window_width, window_height = Window.size
        if not num:
            self.font_size = max(16, window_width * (mul if mul else self.mul))
        else:
            self.font_size = '14pt'
