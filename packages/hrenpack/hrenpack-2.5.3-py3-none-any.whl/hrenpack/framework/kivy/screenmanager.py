from kivy.uix.screenmanager import Screen as KivyScreen, ScreenManager as KivyScreenManager, ScreenManagerException


class ScreenManager(KivyScreenManager):
    screens_dict = dict()

    def setCurrentScreen(self, name: str):
        self.current = name

    def getCurrentScreen(self):
        return self.screens_dict[self.current]

    def add_screen(self, screen, name: str, **kwargs):
        screen.manager = self
        screen.name = name
        if kwargs.get('add_layout_to_app', False):
            exec(f'screen.app.screen_{name}Layout = screen.layout')
        self.screens.append(screen)
        self.screens_dict[name] = screen
        if self.current is None:
            self.current = screen.name


class Screen(KivyScreen):
    def __init__(self, manager=None, name: str = '', **kwargs):
        super().__init__(**kwargs)
        if manager is not None and name != '':
            manager.add_widget(self, name=name)
        elif manager is not None:
            manager.add_widget(self)

    def add(self, *widgets):
        for widget in widgets:
            self.add_widget(widget)
