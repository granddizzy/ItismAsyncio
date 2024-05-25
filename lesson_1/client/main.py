from lesson_1.client.controller import ClientController
from lesson_1.client.model import ClientModel
from lesson_1.client.view import ClientView

model = ClientModel("127.0.0.1", 8020)
view = ClientView()
controller = ClientController(model, view)

if __name__ == "__main__":
    controller.start_client()
