from typing import Literal
from hrenpack.framework.kivy.widgets import BoxLayout, Label


class _WrapperLayout(BoxLayout):
    def __init__(self, orientation: Literal['vertical', 'horizontal'], widget, padding=0, spacing=0, **kwargs):
        super().__init__(orientation, padding=padding, spacing=spacing, **kwargs)
        self.widget = widget
        self.add_widget(self.widget)

    def get_child(self):
        return self.widget


class BoxLabel(_WrapperLayout):
    def __init__(self, orientation: Literal['vertical', 'horizontal'], padding=0, spacing=0, text: str = '', **kwargs):
        box_layout_kwargs: dict = kwargs.get('box_layout_kwargs', dict())
        label_kwargs: dict = kwargs.get('label_kwargs', dict())
        self.size_hint_y = kwargs.get('size_hint_y', None)
        super().__init__(orientation, Label(text, **label_kwargs), padding, spacing, **box_layout_kwargs)


