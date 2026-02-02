import ui
from PySide6.QtWidgets import QDialog
from PySide6.QtGui import QIcon
from hrenpack.framework.Pyside6 import exit
from hrenpack.filework import ConfigurationFile
from hrenpack.kwargswork import kwarg_return


class DialogDefault(QDialog):
    def __init__(self, config: ConfigurationFile, icon_path: str, parent=None, **kwargs):
        super().__init__(parent)
        self.ui = ui.default_ui.Ui_Default()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(icon_path))
        self.config = config
        self.ui.label.setText(kwarg_return(kwargs, 'label_text', self.ui.label.text()))
        self.sections: dict = kwarg_return(kwargs, 'sections', {})
        self.exit = lambda: exit(self)
        self.ui.btn_yes.clicked.connect(lambda: self.default(kwarg_return(kwargs, 'delete', False)))
        self.ui.btn_no.clicked.connect(self.exit)

    def default(self, delete: bool = False):
        if self.sections:
            for section, block in self.sections.items():
                self.config.edit_section(section, block, delete)
        self.exit()
