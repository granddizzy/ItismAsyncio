import asyncio
import os
import re
import sys
from datetime import datetime
import aioconsole
from PyQt6.QtCore import QTimer
from qasync import QtCore
from qasync import QEventLoop, asyncSlot

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
        self.ui.pushButton_uploadFile.clicked.connect(self.slot_upload_file)
        self.ui.pushButton_refresh.clicked.connect(self.slot_refresh)
        self.ui.pushButton_downloadFile.clicked.connect(self.slot_download_file)
        self.ui.pushButton_delete.clicked.connect(self.slot_delete_file)

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
        QtWidgets.QMessageBox.information(self, "Error", error.message)

    def show_message(self, msg):
        QtWidgets.QMessageBox.information(self, "Внимане", msg)

    async def input_mode_fileexists(self) -> str:
        pass

    def slot_upload_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите файл", "",
                                                        "All Files (*);;Text Files (*.txt)")
        filename = os.path.basename(path)
        task = asyncio.create_task(self.controller.upload_file_to_server(path, 'WRITE', filename))

    def slot_refresh(self) -> None:
        task = asyncio.create_task(self.controller.show_files_list())

    def showEvent(self, event):
        pass

    def slot_download_file(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;Text Files (*.txt)")
        filename = ""
        selected_items = self.ui.tableWidget.selectedItems()

        if selected_items:
            selected_row = selected_items[0].row()
            # QtWidgets.QMessageBox.information(self, "Selected Row", f"Selected Row: {selected_row}")
            item = self.ui.tableWidget.item(selected_row, 0)
            task = asyncio.create_task(self.controller.download_file_from_server(item.text(), path, 'WRITE'))
        else:
            # QMessageBox.information(self, "Selected Row", "No row selected")
            pass

    def slot_delete_file(self):
        selected_items = self.ui.tableWidget.selectedItems()

        if selected_items:
            selected_row = selected_items[0].row()
            #QtWidgets.QMessageBox.information(self, "Selected Row", f"Selected Row: {selected_row}")
            item = self.ui.tableWidget.item(selected_row, 0)
            task = asyncio.create_task(self.controller.delete_file_from_server(item.text()))
        else:
            # QMessageBox.information(self, "Selected Row", "No row selected")
            pass

    def closeEvent(self, event):
        QtCore.QCoreApplication.instance().exit()
