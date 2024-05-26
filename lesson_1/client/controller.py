from lesson_1.client.model import ClientModel, ClientError
from lesson_1.client.view import ClientView


class ClientController:
    def __init__(self, model: ClientModel, view: ClientView):
        self.model = model
        self.view = view

    def start_client(self):
        try:
            self.model.set_connection()
        except ClientError as e:
            self.view.show_error(e)

        while True:
            try:
                choice = self.view.show_main_menu()
                self.model.check_connection()

                if choice == 0:
                    self.exit_client()
                    break
                elif choice == 1:
                    self.view.show_file_list(self.model.get_file_list())
                elif choice == 2:
                    self.upload_file()
                elif choice == 3:
                    self.delete_file()
                elif choice == 4:
                    self.download_file()
            except ClientError as e:
                self.view.show_error(e)
            except Exception as e:
                self.view.show_error(ClientError(f"{e}"))

    def exit_client(self):
        self.view.show_message("До свидания!!!")
        self.model.close_connection()

    def upload_file(self):
        while True:
            path = self.view.input_local_path_file()
            if self.model.is_local_file_exists(path):
                if self.model.is_local_file_filled(path):
                    self.view.show_error(ClientError(f"Файл {path} пуст"))
                    break
            else:
                self.view.show_error(ClientError(f"Файл {path} не найден"))

        if path and (filename := self.view.input_filename()):
            mode = 'WRITE'
            if self.model.is_server_file_exists(filename):
                mode = self.view.input_mode_fileexists()
            if mode in ['WRITE', 'ADD']:
                self.model.put_file(path, mode, filename)
                self.view.show_message(f"Файл {filename} успешно добавлен")

    def delete_file(self):
        if filename := self.view.input_filename():
            self.model.del_file(filename)
            self.view.show_message(f"Файл {filename} успешно удален")

    def download_file(self):
        if filename := self.view.input_filename():
            if self.model.is_server_file_exists(filename):
                if path := self.view.input_local_path_file():
                    mode = 'WRITE'
                    if self.model.is_server_file_exists(path):
                        mode = self.view.input_mode_fileexists()
                    if mode in ['WRITE', 'ADD']:
                        self.model.save_file(filename, path, mode)
                        self.view.show_message(f"Файл {path} успешно сохранен")
            else:
                self.view.show_error(ClientError(f"Файл {filename} не найден на сервере"))
