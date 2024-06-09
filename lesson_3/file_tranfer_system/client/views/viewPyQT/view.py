import asyncio
import re
import sys
from datetime import datetime
import aioconsole
from lesson_3.file_tranfer_system.client.controller import Controller
from lesson_3.file_tranfer_system.client.model import ClientError
from lesson_3.file_tranfer_system.client.abstractView import View as AbstractView

from PyQt6 import QtWidgets

from lesson_3.file_tranfer_system.client.views.viewPyQT import mainWindow


class PyQtView(QtWidgets.QMainWindow, AbstractView):
    def __init__(self, controller: Controller = None):
        # tWidgets.QWidget.__init__(self, parent)
        super().__init__()
        self.controller = controller

        self.ui = mainWindow.Ui_Form()
        self.ui.setupUi(self)

        # connect signals
        # self.ui.pushButton_2.clicked.connect(self.close)
        self.ui.pushButton_uploadFile.clicked.connect(self.slot_upload_file)

        # self.ui.treeWidget.currentItemChanged.connect(self.show_description)

    async def show_main_menu(self) -> int:
        pass

    async def show_fileexists_menu(self) -> int:
        pass

    async def input_choice(self, max_choice_num: int) -> int | None:
        pass

    async def input_local_path_file(self) -> str:
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл", "",
                                                             "All Files (*);;Text Files (*.txt)")

        return file_name

    async def input_filename(self) -> str:
        pass

    def show_file_list(self, files: list) -> None:
        self.ui.tableWidget.setRowCount(0)
        for filedata in files:
            filename, filesize, modified = filedata.split(':', 2)
            modified_date = datetime.fromtimestamp(int(modified)).strftime('%Y-%m-%d %H:%M:%S')

            row_position = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(row_position)

            item1 = QtWidgets.QTableWidgetItem(filename)
            item2 = QtWidgets.QTableWidgetItem(filesize)
            item3 = QtWidgets.QTableWidgetItem(modified_date)
            self.ui.tableWidget.setItem(row_position, 0, item1)
            self.ui.tableWidget.setItem(row_position, 1, item2)
            self.ui.tableWidget.setItem(row_position, 2, item3)

    def show_error(self, error: ClientError):
        pass

    def show_message(self, msg):
        pass

    async def input_mode_fileexists(self) -> str:
        pass

    def slot_upload_file(self) -> None:
        asyncio.run(self.controller.upload_file_action())

    def showEvent(self, event):
        asyncio.run(self.controller.show_files_list())
