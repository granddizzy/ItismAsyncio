import asyncio

from lesson_3.file_tranfer_system.client.model import Client, ClientError
from lesson_3.file_tranfer_system.client.view import View


class Controller:
    def __init__(self, model: Client, view: View):
        self.model = model
        self.view = view
        self.tasks = []

    async def start_client(self):
        try:
            await self.model.set_connection()
        except ClientError as e:
            self.view.show_error(e)

        while True:
            try:
                choice = await self.view.show_main_menu()
                await self.model.check_connection()

                if choice == 0:
                    await self.exit_client()
                    break
                elif choice == 1:
                    task = asyncio.create_task(self.__show_files_list())
                    #self.tasks.append(task)
                elif choice == 2:
                    await self.upload_file()
                elif choice == 3:
                    await self.delete_file()
                elif choice == 4:
                    await self.download_file()
            except ClientError as e:
                self.view.show_error(e)
            except Exception as e:
                self.view.show_error(ClientError(f"{e}"))

        #await asyncio.gather(*self.tasks)

    async def exit_client(self):
        self.view.show_message("До свидания!!!")
        await self.model.close_connection()

    async def __show_files_list(self):
        file_list = await self.model.get_file_list()
        self.view.show_file_list(file_list)

    async def upload_file(self):
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
            if await self.model.is_server_file_exists(filename):
                mode = self.view.input_mode_fileexists()
            if mode in ['WRITE', 'ADD']:
                task = asyncio.create_task(self.__upload_file_to_server(path, mode, filename))

    async def __upload_file_to_server(self, path, mode, filename):
        await self.model.put_file(path, mode, filename)
        self.view.show_message(f"Файл {filename} успешно добавлен")

    async def delete_file(self):
        if filename := await self.view.input_filename():
            await self.model.del_file(filename)
            self.view.show_message(f"Файл {filename} успешно удален")

    async def download_file(self):
        if filename := await self.view.input_filename():
            if await self.model.is_server_file_exists(filename):
                if path := await self.view.input_local_path_file():
                    mode = 'WRITE'
                    if await self.model.is_server_file_exists(path):
                        mode = self.view.input_mode_fileexists()
                    if mode in ['WRITE', 'ADD']:
                        await self.model.save_file(filename, path, mode)
                        self.view.show_message(f"Файл {path} успешно сохранен")
            else:
                self.view.show_error(ClientError(f"Файл {filename} не найден на сервере"))
