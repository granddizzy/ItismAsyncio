import socket
import sys
import os
import re
from builtins import isinstance
from datetime import datetime

host = '127.0.0.1'
port = 8020

encoding = 'utf-8'
forbidden_chars = r'[\\/:"*?<>|]'

client_socket: socket.socket | None = None


class ClientError:
    def __init__(self, message: str):
        self.message = message


def set_connection(host: str, port: int) -> None | ClientError:
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((host, port))
        return None
    except (socket.timeout, ConnectionError, socket.error) as e:
        return ClientError(f"{e}")


def is_connected() -> bool:
    global client_socket
    if not client_socket:
        return False

    if send_data(create_byte_header('TEST')) is None:
        return True

    return False


def check_connection() -> bool:
    global client_socket
    if not is_connected():
        show_message("Соединение с сервером потеряно. Переподключение...")

        if client_socket:
            client_socket.close()

        if isinstance(res := set_connection(host, port), ClientError):
            show_error(res)
            return False

        show_message("Соединение установлено")

    return True


def get_mode_fileexists(filename: str) -> str:
    mode = "WRITE"
    if check_server_file(filename):
        choice = show_fileexists_menu()
        if choice == 0:
            mode = ''
        elif choice == 1:
            mode = "ADD"
    return mode


def start_client():
    if isinstance(res := set_connection(host, port), ClientError):
        show_error(res)

    while True:
        try:
            choice = show_main_menu()

            if choice == 0:
                prog_exit()
            elif choice in (1, 2, 3):
                if check_connection():
                    if choice == 1:
                        if isinstance(res := get_file_list(), ClientError):
                            show_error(res)
                        else:
                            show_file_list(res)
                    elif choice == 2:
                        if (path := input_path_file()) and (filename := input_filename()):
                            if (mode := get_mode_fileexists(filename)) in ['WRITE', 'ADD']:
                                if isinstance(res := put_file(path, mode, filename), ClientError):
                                    show_error(res)
                                else:
                                    show_message(f"Файл {filename} успешно добавлен")
                    elif choice == 3:
                        if filename := input_filename():
                            if isinstance(res := del_file(filename), ClientError):
                                show_error(res)
                            else:
                                show_message(f"Файл {filename} успешно удален")
        except Exception as e:
            show_error(ClientError(f"{e}"))


def show_main_menu() -> int:
    print()
    print('Главное меню:')
    print('0.Выйти')
    print('1.Получить список файлов')
    print('2.Добавить файл')
    print('3.Удалить файл')
    print()
    return input_choice(4)


def show_fileexists_menu() -> int:
    print()
    print("Такой файл уже существует на сервере.")
    print('Выберите действие:')
    print('0.Отменить')
    print('1.Дописать')
    print('2.Заменить')
    print()
    return input_choice(3)


def input_choice(max_choice_num: int) -> int | None:
    while True:
        answer = input("Сделайте выбор:")
        if answer.isdigit() and 0 <= int(answer) <= max_choice_num:
            return int(answer)


def input_path_file() -> str:
    while True:
        path = input("Введите путь к текстовому файлу на вашем компьютере (имя файла без расширения):")
        if not path or check_local_file(path):
            return path


def input_filename() -> str:
    while True:
        filename = input("Введите имя файла на сервере :")
        if not re.search(forbidden_chars, filename):
            return filename
        else:
            print(f"Имя содержит запрещенные символы: {forbidden_chars}")


def get_file_list() -> list | ClientError:
    files_list = []

    if check_connection():
        if isinstance(res := send_data(create_byte_header('LIST')), ClientError):
            return res
        else:
            if isinstance(res := get_header(), ClientError):
                return res
            elif res.startswith('LIST'):
                _, filesize_str = res.split('\n', 1)

                filesize = int(filesize_str)
                buffer = b''
                count = 0
                if filesize > 1024:
                    count = filesize // 1024
                bytes_remainder = filesize - 1024 * count
                for i in range(1, count + 1):
                    buffer += client_socket.recv(1024)
                if bytes_remainder:
                    buffer += client_socket.recv(bytes_remainder)

                if buffer:
                    files_list = buffer.split(b'\n')

    return list(map(lambda x: x.decode(encoding), files_list))


def show_file_list(files: list) -> None:
    print("\n" + "=" * 83)
    print(f"{'Имя файла':<40} {'Размер':<10} {'Изменен':<10}")
    print("=" * 83)
    if files:
        for filedata in files:
            filename, filesize, modified = filedata.split(':', 2)
            modified_date = datetime.fromtimestamp(int(modified)).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{filename:<40} {filesize:<10} {modified_date:<10}")
    else:
        print("Файлов нет")
    print("=" * 83 + "\n")


def check_local_file(path: str) -> bool:
    fullpath = path + ".txt"
    if not os.path.isfile(fullpath):
        print(f"Локальный файл {fullpath} не найден")
        return False
    elif os.path.getsize(fullpath) == 0:
        print(f"Локальный файл {fullpath} пустой")
        return False
    return True


def check_server_file(filename: str) -> bool | ClientError:
    if check_connection() and send_data(create_byte_header('CHECK', filename)) is None:
        res = get_header()
        if isinstance(res, ClientError):
            return res
        elif res and res.startswith("EXISTS"):
            return True
    return False


def put_file(path: str, mode: str, filename: str) -> None | ClientError:
    fullpath = path + ".txt"
    if check_connection():
        if isinstance(res := send_data(create_byte_header('PUT', filename, str(os.path.getsize(fullpath)), mode)),
                      ClientError):
            return res
        else:
            try:
                with open(fullpath, 'rb') as f:
                    while chunk := f.read(1024):
                        if isinstance(res := send_data(chunk), ClientError):
                            return res
            except (IOError, OSError) as e:
                return ClientError("Ошибка чтения файла")

            if isinstance(res := get_header(), ClientError):
                return res
            elif res.startswith('ERROR'):
                return ClientError(get_error_message(res))


def del_file(filename: str) -> None | ClientError:
    if check_connection():
        if isinstance(res := send_data(create_byte_header('CHECK', filename)), ClientError):
            return res
        else:
            if isinstance(res := get_header(), ClientError):
                return res
            elif res.startswith("NOT_EXISTS"):
                return ClientError(f"Файла {filename} нет на сервере")

            if isinstance(res := send_data(create_byte_header('DEL', filename)), ClientError):
                return res
            else:
                if isinstance(res := get_header(), ClientError):
                    return res
                elif res.startswith('ERROR'):
                    return ClientError(get_error_message(res))


def get_header() -> str | ClientError:
    try:
        return client_socket.recv(512).decode(encoding).strip()
    except socket.timeout:
        return ClientError("Долгий ответ от сервера")
    except (ConnectionError, socket.error) as e:
        return ClientError("Ошибка соединения")


def send_data(data: bin) -> None | ClientError:
    try:
        client_socket.sendall(data)
    except (socket.timeout, ConnectionError, socket.error, Exception):
        return ClientError("Ошибка соединения")

    return None


def prog_exit() -> None:
    if client_socket:
        if is_connected():
            send_data(create_byte_header('QUIT'))
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except (ConnectionError, socket.error):
                pass

        client_socket.close()
    show_message("До свидания!!!")
    sys.exit()


def get_error_message(msg: str) -> str:
    return msg.split('\n', 1)[1]


def create_byte_header(*args) -> bin:
    return '\n'.join(args).encode(encoding).ljust(512, b' ')


def show_error(error: ClientError):
    print(f"Ошибка: {error.message}")


def show_message(msg):
    print(msg)


if __name__ == "__main__":
    start_client()
