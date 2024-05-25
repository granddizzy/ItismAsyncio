import socket
import sys
import os
import re
from datetime import datetime

host = '127.0.0.1'
port = 8020

encoding = 'utf-8'
forbidden_chars = r'[\\/:"*?<>|]'

client_socket: socket.socket | None = None


def set_connection(host: str, port: int) -> bool:
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((host, port))
        return True
    except (socket.timeout, ConnectionError, socket.error) as e:
        print(e)
        return False


def is_connected() -> bool:
    global client_socket
    if not client_socket:
        return False

    try:
        client_socket.sendall(get_byte_header('TEST'))
        return True
    except (socket.timeout, ConnectionError, socket.error):
        return False


def check_connection() -> bool:
    global client_socket
    if not is_connected():
        print("Соединение с сервером потеряно. Переподключение...")

        if client_socket:
            client_socket.close()

        if not set_connection(host, port):
            print("Попытка не удачна")
            return False

        print("Соединение установлено")

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
    if not set_connection(host, port):
        print("Соединение с сервером не установлено.")

    while True:
        try:
            choice = show_main_menu()

            if choice == 0:
                prog_exit()
            elif choice in (1, 2, 3):
                if check_connection():
                    if choice == 1:
                        show_file_list(get_file_list())
                    elif choice == 2:
                        if (path := input_path_file()) and (filename := input_filename()):
                            if (mode := get_mode_fileexists(filename)) in ['WRITE', 'ADD']:
                                put_file(path, mode, filename)
                    elif choice == 3:
                        if filename := input_filename():
                            del_file(filename)
        except Exception as e:
            print(f"An error occurred: {e}")


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


def get_file_list() -> list:
    files_list = []

    if check_connection():
        try:
            client_socket.sendall(get_byte_header('LIST'))
            header = client_socket.recv(512).decode(encoding).strip()
        except socket.timeout:
            print("Долгий ответ от сервера")
            return files_list
        except (ConnectionError, socket.error):
            return files_list

        if header.startswith('LIST'):
            _, filesize_str = header.split('\n', 1)

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


def check_server_file(filename: str) -> bool:
    if check_connection():
        try:
            client_socket.sendall(get_byte_header('CHECK', filename))
            ack = client_socket.recv(512).decode(encoding).strip()
        except socket.timeout:
            print("Долгий ответ от сервера")
            return False
        except (ConnectionError, socket.error):
            return False

        if ack.startswith("EXISTS"):
            return True

    return False


def put_file(path: str, mode: str, filename: str) -> None:
    if check_connection():
        try:
            fullpath = path + ".txt"
            client_socket.sendall(get_byte_header('PUT', filename, str(os.path.getsize(fullpath)), mode))

            with open(fullpath, 'rb') as f:
                while chunk := f.read(1024):
                    client_socket.sendall(chunk)

            ack = client_socket.recv(512).decode(encoding).strip()
        except socket.timeout:
            print("Долгий ответ от сервера")
            return None
        except (ConnectionError, socket.error):
            return None

        if ack.startswith('SUCCESS'):
            print("Файл успешно добавлен.")
        elif ack.startswith('ERROR'):
            print(get_error_message(ack))


def del_file(filename: str) -> None:
    if check_connection():
        try:
            client_socket.sendall(get_byte_header('CHECK', filename))
            ack = client_socket.recv(512).decode(encoding).strip()
            if ack.startswith("NOT_EXISTS"):
                print(f"Файла {filename} нет на сервере")
                return None

            client_socket.sendall(get_byte_header('DEL', filename))
            ack = client_socket.recv(512).decode(encoding).strip()

        except socket.timeout:
            print("Долгий ответ от сервера")
            return None
        except (ConnectionError, socket.error):
            return None

        if ack.startswith('SUCCESS'):
            print(f"Файл {filename} успешно удален.")
        elif ack.startswith('ERROR'):
            print(get_error_message(ack))


def prog_exit() -> None:
    if client_socket:
        if is_connected():
            try:
                client_socket.sendall(get_byte_header('QUIT'))
                client_socket.shutdown(socket.SHUT_RDWR)
            except (ConnectionError, socket.error):
                pass

        client_socket.close()
    print("До свидания!!!")
    sys.exit()


def get_error_message(msg: str) -> str:
    return msg.split('\n', 1)[1]


def get_byte_header(*args) -> bin:
    return '\n'.join(args).encode(encoding).ljust(512, b' ')


if __name__ == "__main__":
    start_client()
