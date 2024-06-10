import asyncio
import os

from lesson_3.file_tranfer_system.client.model import Client, ClientError
from lesson_3.file_tranfer_system.client.abstractView import View
from lesson_3.file_tranfer_system.client.model import ConnectedSocket


class Controller:
    def __init__(self, model: Client, view: View | None):
        self.model = model
        self.view = view
        self.tasks = []

    async def start_client(self):
        try:
            await self.__process_choice()
        except ClientError as e:
            self.view.show_error(e)
        except Exception as e:
            self.view.show_error(ClientError(f"{e}"))

    async def __process_choice(self):
        while True:
            choice = await self.view.show_main_menu()

            if choice == 0:
                await self.__exit_client()
                break
            elif choice == 1:
                task = asyncio.create_task(self.show_files_list())
            elif choice == 2:
                await self.upload_file_action()
            elif choice == 3:
                await self.__delete_file_action()
            elif choice == 4:
                await self.__download_file_action()

    async def __exit_client(self):
        self.view.show_message("До свидания!!!")

    async def show_files_list(self):
        async with ConnectedSocket(self.model) as connection:
            try:
                file_list = await self.model.get_file_list(connection)
                self.view.show_file_list(file_list)
            except ClientError as e:
                self.view.show_error(e)

    async def upload_file_action(self):
        while True:
            path = await self.view.input_local_path_file()
            if not path:
                break
            elif self.model.is_local_file_exists(path):
                if not self.model.is_local_file_filled(path):
                    self.view.show_error(ClientError(f"Файл {path} пуст"))
                else:
                    break
            else:
                self.view.show_error(ClientError(f"Файл {path} не найден"))

        if path and (filename := await self.view.input_filename()):
        # if path:
            filename = os.path.basename(path)
            mode = 'WRITE'
            async with ConnectedSocket(self.model) as connection:
                if await self.model.is_server_file_exists(connection, filename):
                    mode = await self.view.input_mode_fileexists()
                if mode in ['WRITE', 'ADD']:
                    task = asyncio.create_task(self.upload_file_to_server(path, mode, filename))

    async def upload_file_to_server(self, path, mode, filename):
        async with ConnectedSocket(self.model) as connection:
            try:
                await self.model.put_file(connection, path, mode, filename)
                self.view.show_message(f"Файл {filename} успешно добавлен")
            except ClientError as e:
                self.view.show_error(e)

    async def __delete_file_action(self):
        if filename := await self.view.input_filename():
            task = asyncio.create_task(self.delete_file_from_server(filename))

    async def delete_file_from_server(self, filename):
        async with ConnectedSocket(self.model) as connection:
            try:
                await self.model.del_file(connection, filename)
                self.view.show_message(f"Файл {filename} успешно удален")
            except ClientError as e:
                self.view.show_error(e)

    async def __download_file_action(self):
        if filename := await self.view.input_filename():
            async with ConnectedSocket(self.model) as connection:
                if await self.model.is_server_file_exists(connection, filename):
                    if path := await self.view.input_local_path_file():
                        mode = 'WRITE'
                        if self.model.is_local_file_exists(path):
                            mode = await self.view.input_mode_fileexists()
                        if mode in ['WRITE', 'ADD']:
                            task = asyncio.create_task(self.download_file_from_server(filename, path, mode))
                else:
                    self.view.show_error(ClientError(f"Файл {filename} не найден на сервере"))

    async def download_file_from_server(self, filename, path, mode):
        async with ConnectedSocket(self.model) as connection:
            try:
                await self.model.save_file(connection, filename, path, mode)
                self.view.show_message(f"Файл {path} успешно сохранен")
            except ClientError as e:
                self.view.show_error(e)
