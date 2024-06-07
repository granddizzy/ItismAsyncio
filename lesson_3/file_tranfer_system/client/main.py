from lesson_3.file_tranfer_system.client.controller import Controller
from lesson_3.file_tranfer_system.client.model import Client
from lesson_3.file_tranfer_system.client.view import View
import asyncio


async def main():
    model = Client("127.0.0.1", 8020)
    view = View()
    controller = Controller(model, view)
    await controller.start_client()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Client stopped manually.")
