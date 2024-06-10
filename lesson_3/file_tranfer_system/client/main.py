import sys

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal, QObject

from qasync import QEventLoop, asyncSlot

from lesson_3.file_tranfer_system.client.controller import Controller
from lesson_3.file_tranfer_system.client.model import Client
import asyncio

from lesson_3.file_tranfer_system.client.views.viewConsole.view import ConsoleView
from lesson_3.file_tranfer_system.client.views.viewPyQT.view import PyQtView

# run_type = "console"
run_type = "gui"


async def run_console_app():
    model = Client("127.0.0.1", 8020)
    view = ConsoleView()
    controller = Controller(model, view)
    await controller.start_client()


def run_gui_app():
    app = QtWidgets.QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    model = Client("127.0.0.1", 8020)
    controller = Controller(model, None)
    view = PyQtView(controller)
    controller.view = view

    view.show()
    # app.exec()
    # sys.exit(app.exec())

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    # if '--gui' in sys.argv:
    if run_type == "console":
        try:
            asyncio.run(run_console_app())
        except KeyboardInterrupt:
            print("Client stopped manually.")
    else:
        run_gui_app()
