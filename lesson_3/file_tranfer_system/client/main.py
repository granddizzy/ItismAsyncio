import sys

from PyQt6 import QtWidgets

from lesson_3.file_tranfer_system.client.controller import Controller
from lesson_3.file_tranfer_system.client.model import Client
import asyncio

from lesson_3.file_tranfer_system.client.views.viewConsole.view import ConsoleView
from lesson_3.file_tranfer_system.client.views.viewPyQT.view import PyQtView

#run_type = "console"
run_type = "gui"

async def run_console_app():
    model = Client("127.0.0.1", 8020)
    view = ConsoleView()
    controller = Controller(model, view)
    await controller.start_client()


def run_gui_app():
    app = QtWidgets.QApplication(sys.argv)
    model = Client("127.0.0.1", 8020)
    controller = Controller(model, None)
    view = PyQtView(controller)
    controller.view = view
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # if '--gui' in sys.argv:
    if run_type == "console":
        try:
            asyncio.run(run_console_app())
        except KeyboardInterrupt:
            print("Client stopped manually.")
    else:
        run_gui_app()
