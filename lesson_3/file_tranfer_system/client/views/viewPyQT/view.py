import re
import sys
from datetime import datetime
import aioconsole

from lesson_3.file_tranfer_system.client.controller import Controller
from lesson_3.file_tranfer_system.client.model import ClientError
from lesson_3.file_tranfer_system.client.abstractView import View

from PyQt6 import QtWidgets

from lesson_3.file_tranfer_system.client.views.viewPyQT import mainWindow


class PyQtView(QtWidgets.QWidget, View):
    def __init__(self, parent=None, controller: Controller = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.controller = controller

        self.ui = mainWindow.Ui_Form()
        self.ui.setupUi(self)

        # connect signals
        # self.ui.pushButton_2.clicked.connect(self.close)
        # self.ui.pushButton.clicked.connect(self.search)

        # self.ui.treeWidget.currentItemChanged.connect(self.show_description)

    async def show_main_menu(self) -> int:
        pass

    async def show_fileexists_menu(self) -> int:
        pass

    async def input_choice(self, max_choice_num: int) -> int | None:
        pass

    async def input_local_path_file(self) -> str:
        pass

    async def input_filename(self) -> str:
        pass

    def show_file_list(self, files: list) -> None:
        pass

    def show_error(self, error: ClientError):
        pass

    def show_message(self, msg):
        pass

    async def input_mode_fileexists(self) -> str:
        pass
