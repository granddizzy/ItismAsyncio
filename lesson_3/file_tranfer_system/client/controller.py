import asyncio

from lesson_3.file_tranfer_system.client.model import Client, ClientError
from lesson_3.file_tranfer_system.client.view import View


class Controller:
    def __init__(self, model: Client, view: View):
        self.model = model
        self.view = view
        self.tasks = []

    async def start_client(self):
        # try:
        #     await self.model.set_connection()
        # except ClientError as e:
        #     self.view.show_error(e)

        try:
            await self.__process_choice()
        except ClientError as e:
            self.view.show_error(e)
        except Exception as e:
            self.view.show_error(ClientError(f"{e}"))

    async def __process_choice(self):
        while True:
            choice = await self.view.show_main_menu()
            # await self.model.check_connection()

            if choice == 0:
                await self.__exit_client()
                break
            elif choice == 1:
                task = asyncio.create_task(self.__show_files_list())
            elif choice == 2:
                await self.__upload_file_action()
            elif choice == 3:
                await self.__delete_file_action()
            elif choice == 4:
                await self.__download_file_action()

    async def __exit_client(self):
        self.view.show_message("До свидания!!!")
        await self.model.close_connection(self.model.get_client_socket())

    async def __show_files_list(self):
        client_socket = await self.model.set_temporary_connection()
        try:
            file_list = await self.model.get_file_list(client_socket)
            self.view.show_file_list(file_list)
        except ClientError as e:
            self.view.show_error(e)
        await self.model.close_connection(client_socket)

    async def __upload_file_action(self):
        while True:
            path = await self.view.input_local_path_file()
            if self.model.is_local_file_exists(path):
                if not self.model.is_local_file_filled(path):
                    self.view.show_error(ClientError(f"Файл {path} пуст"))
                else:
                    break
            else:
                self.view.show_error(ClientError(f"Файл {path} не найден"))

        if path and (filename := await self.view.input_filename()):
            mode = 'WRITE'
            client_socket = await self.model.set_temporary_connection()
            if await self.model.is_server_file_exists(client_socket, filename):
                mode = await self.view.input_mode_fileexists()
            if mode in ['WRITE', 'ADD']:
                task = asyncio.create_task(self.__upload_file_to_server(path, mode, filename))
            await self.model.close_connection(client_socket)

    async def __upload_file_to_server(self, path, mode, filename):
        client_socket = await self.model.set_temporary_connection()
        try:
            await self.model.put_file(client_socket, path, mode, filename)
            self.view.show_message(f"Файл {filename} успешно добавлен")
        except ClientError as e:
            self.view.show_error(e)
        await self.model.close_connection(client_socket)

    async def __delete_file_action(self):
        if filename := await self.view.input_filename():
            task = asyncio.create_task(self.__delete_file_from_server(filename))

    async def __delete_file_from_server(self, filename):
        client_socket = await self.model.set_temporary_connection()
        try:
            await self.model.del_file(client_socket, filename)
            self.view.show_message(f"Файл {filename} успешно удален")
        except ClientError as e:
            self.view.show_error(e)
        await self.model.close_connection(client_socket)

    async def __download_file_action(self):
        if filename := await self.view.input_filename():
            client_socket = await self.model.set_temporary_connection()
            if await self.model.is_server_file_exists(client_socket, filename):
                if path := await self.view.input_local_path_file():
                    mode = 'WRITE'
                    if self.model.is_local_file_exists(path):
                        mode = await self.view.input_mode_fileexists()
                    if mode in ['WRITE', 'ADD']:
                        task = asyncio.create_task(self.__download_file_from_server(filename, path, mode))
            else:
                self.view.show_error(ClientError(f"Файл {filename} не найден на сервере"))
            await self.model.close_connection(client_socket)

    async def __download_file_from_server(self, filename, path, mode):
        client_socket = await self.model.set_temporary_connection()
        try:
            await self.model.save_file(client_socket, filename, path, mode)
            self.view.show_message(f"Файл {path} успешно сохранен")
        except ClientError as e:
            self.view.show_error(e)
        await self.model.close_connection(client_socket)
