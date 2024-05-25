from lesson_1.client.model import ClientModel, ClientError
from lesson_1.client.viev import ClientView


class ClientController:
    def __init__(self, model: ClientModel, view: ClientView):
        self.model = model
        self.view = view

    def start_client(self):
        if isinstance(res := self.model.set_connection(), ClientError):
            self.view.show_error(res)

        while True:
            try:
                choice = self.view.show_main_menu()

                if choice == 0:
                    self.model.close_connection()
                elif choice in (1, 2, 3):
                    if self.model.check_connection():
                        if choice == 1:
                            if isinstance(res := self.model.get_file_list(), ClientError):
                                self.view.show_error(res)
                            else:
                                self.view.show_file_list(res)
                        elif choice == 2:
                            while True:
                                path = self.view.input_path_file()
                                if isinstance(res := self.model.check_local_file(path), ClientError):
                                    self.view.show_error(res)
                                else:
                                    break
                            if path and (filename := self.view.input_filename()):
                                mode = 'WRITE'
                                if self.model.check_server_file(filename):
                                    mode = self.view.input_mode_fileexists()
                                if mode in ['WRITE', 'ADD']:
                                    if isinstance(res := self.model.put_file(path, mode, filename), ClientError):
                                        self.view.show_error(res)
                                    else:
                                        self.view.show_message(f"Файл {filename} успешно добавлен")
                        elif choice == 3:
                            if filename := self.view.input_filename():
                                if isinstance(res := self.model.del_file(filename), ClientError):
                                    self.view.show_error(res)
                                else:
                                    self.view.show_message(f"Файл {filename} успешно удален")
            except Exception as e:
                self.view.show_error(ClientError(f"{e}"))
