from typing import Literal, Optional, Union
from kivy.uix.boxlayout import BoxLayout as KivyBoxLayout
from kivy.uix.button import Button as KivyButton
from kivy.uix.floatlayout import FloatLayout as KivyFloatLayout
from kivy.uix.label import Label as KivyLabel
from kivy.uix.image import Image as KivyImage
from hrenpack.decorators import args_kwargs
from hrenpack.framework.kivy.mixins import LayoutMixin, WidgetMixin


class BoxLayout(KivyBoxLayout, LayoutMixin):
    @args_kwargs(args_name='children', copy_kwargs=False)
    def __init__(self, orientation: Literal['vertical', 'horizontal'] = 'vertical', parent=None, *children, padding=0,
                 spacing=0, **kwargs):
        super().__init__(orientation=orientation, padding=padding, spacing=spacing, **kwargs)
        if parent is not None:
            parent.add_widget(self)
        if children:
            self.add(*children)

    def cofficient(self, widget,
                   size_percent: Optional[Union[
                       int, float, tuple[float, float], tuple[int, int], list[int, int], list[float, float]]] = None,
                   pos_percent: Optional[Union[
                       int, float, tuple[float, float], tuple[int, int], list[int, int], list[float, float]]] = None,
                   ):
        def f(p):
            if isinstance(p, (int, float)):
                if p <= 0:
                    raise ValueError("Percent must be greater than zero")
                a, b = self.width * (p / 100), self.height * (p / 100)
            else:
                if p[0] <= 0 or p[1] <= 0:
                    raise ValueError("Percent must be greater than zero")
                a, b = self.width * (p[0] / 100), self.height * (p[1] / 100)
            return a, b

        if size_percent is None and pos_percent is None:
            raise ValueError("Either size_percent or pos_percent must be specified")
        if size_percent is not None:
            widget.size_hint = f(size_percent)
        if pos_percent is not None:
            widget.pos_hint = f(pos_percent)


class FloatLayout(KivyFloatLayout, LayoutMixin):
    @args_kwargs(args_name='children', copy_kwargs=False)
    def __init__(self, parent=None, *children, **kwargs):
        super().__init__(**kwargs)
        if parent is not None:
            parent.add_widget(self)
        if children:
            self.add(*children)


class Label(KivyLabel, WidgetMixin):
    def __init__(self, text='', parent=None, **kwargs):
        super().__init__(text=text, **kwargs)
        if parent is not None:
            parent.add_widget(self)

    def set_text(self, text):
        self.text = text


class Button(KivyButton, WidgetMixin):
    def __init__(self, text: str = '', parent=None, command=None, **kwargs):
        super().__init__(text=text, **kwargs)
        if parent is not None:
            parent.add_widget(self)
        if command:
            self.clicked_connect(command)

    def clicked_connect(self, command, **kwargs):
        self.bind(on_press=command, **kwargs)


class IconButton(KivyBoxLayout, WidgetMixin):
    def __init__(self, icon_path: str, text: str = '', parent=None, command=None, **kwargs):
        super(IconButton, self).__init__(**kwargs)
        self.orientation = 'horizontal'

        # Добавление кнопки с иконкой
        self.button = Button(
            text=text,
            size_hint=(None, None),
            size=(50, 50),
            background_normal=icon_path
        )
        self.add_widget(self.button)


class LoggingLabel(Label):
    state: Literal['success', 'warning', 'error'] = 'success'

    def __init__(self, text: str = '', parent=None, *disabling_widgets, disable_error: bool = False, **kwargs):
        super().__init__(text, parent, color=(0, 1, 0), **kwargs)
        self.disabling_widgets = list(disabling_widgets)
        self.disable_error = disable_error
        self.normal = text

    def set_success(self, text: Optional[str] = None):
        if text is None:
            text = self.normal
        self.color = (0, 1, 0)
        self.set_text(text)
        self.state = 'success'
        if self.disable_error:
            self.enable_widgets()

    def set_warning(self, text: str):
        if self.state != 'error':
            self.state = 'warning'
            self.color = (1, 1, 0)
            self.set_text(text)

    def set_error(self, text: str):
        self.color = (1, 0, 0)
        self.state = 'error'
        self.set_text(text)
        if self.disable_error:
            self.disable_widgets()

    def disable_widgets(self):
        for widget in self.disabling_widgets:
            widget.disable()

    def enable_widgets(self):
        for widget in self.disabling_widgets:
            widget.enable()

    def add_disabled(self, *widgets):
        for widget in widgets:
            self.disabling_widgets.append(widget)


class Image(KivyImage):
    def __init__(self, source: str, **kwargs):
        super().__init__(source=source, **kwargs)
