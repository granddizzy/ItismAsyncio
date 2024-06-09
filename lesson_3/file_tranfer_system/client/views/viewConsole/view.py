import re
from datetime import datetime
import aioconsole
from lesson_3.file_tranfer_system.client.model import ClientError
from lesson_3.file_tranfer_system.client.abcView import View

forbidden_chars = r'[\\/:"*?<>|]'


class ConsoleView(View):
    async def show_main_menu(self) -> int:
        print()
        print('Главное меню:')
        print('0.Выйти')
        print('1.Получить список файлов')
        print('2.Добавить файл')
        print('3.Удалить файл')
        print('4.Получить файл')
        print()
        return await self.input_choice(5)

    async def show_fileexists_menu(self) -> int:
        print()
        print("Такой файл уже существует на сервере.")
        print('Выберите действие:')
        print('0.Отменить')
        print('1.Дописать')
        print('2.Заменить')
        print()
        return await self.input_choice(3)

    async def input_choice(self, max_choice_num: int) -> int | None:
        while True:
            answer = await aioconsole.ainput("Сделайте выбор:")
            if answer.isdigit() and 0 <= int(answer) <= max_choice_num:
                return int(answer)

    async def input_local_path_file(self) -> str:
        return await aioconsole.ainput("Введите путь к файлу на вашем компьютере:")

    async def input_filename(self) -> str:
        while True:
            filename = await aioconsole.ainput("Введите имя файла на сервере :")
            if not re.search(forbidden_chars, filename):
                return filename
            else:
                print(f"Имя содержит запрещенные символы: {forbidden_chars}")

    def show_file_list(self, files: list) -> None:
        print("\n" + "=" * 83)
        print(f"{'Имя файла':<40} {'Размер':<10} {'Изменен':<10}")
        print("=" * 83)
        if files:
            for filedata in files:
                filename, filesize, modified = filedata.split(':', 2)
                modified_date = datetime.fromtimestamp(int(modified)).strftime('%Y-%m-%d %H:%M:%S')
                print(f"{filename:<40} {filesize:<10} {modified_date:<20}")
        else:
            print("Файлов нет")
        print("=" * 83 + "\n")

    def show_error(self, error: ClientError):
        print(f"Ошибка: {error.message}")

    def show_message(self, msg):
        print(msg)

    async def input_mode_fileexists(self) -> str:
        choice = await self.show_fileexists_menu()
        if choice == 0:
            return ''
        elif choice == 1:
            return "ADD"
        return 'WRITE'
