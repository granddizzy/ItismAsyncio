import socket
import sys
import os

host = '127.0.0.1'
port = 8020

encoding = 'utf-8'


def set_connection(host, port) -> socket.socket | None:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        return client_socket
    except (ConnectionError, socket.error):
        return None


def is_connected(client_socket: socket.socket) -> bool:
    try:
        client_socket.settimeout(5)
        client_socket.sendall(b'TEST'.ljust(1024, b' '))
        return True
    except (ConnectionError, socket.error):
        return False


def check_connection(client_socket) -> socket.socket:
    if not client_socket or not is_connected(client_socket):
        print("Соединение с сервером не установлено. Переподключение...")

        if client_socket:
            client_socket.close()

        client_socket = set_connection(host, port)
        if not client_socket:
            print("Попытка не удачна")
        else:
            print("Соединение установлено")

    return client_socket


def start_client():
    client_socket = set_connection(host, port)
    if not client_socket:
        print("Соединение с сервером не установлено.")

    while True:
        try:
            choice = show_main_menu()

            if choice == 0:
                prog_exit(client_socket)
            elif choice in (1, 2, 3):
                if client_socket := check_connection(client_socket):
                    if choice == 1:
                        show_file_list(get_file_list(client_socket))
                    elif choice == 2:
                        path = input_path_file()
                        if path:
                            if check_local_file(path):
                                filename = input_filename()
                                if filename:
                                    mode = "WRITE"
                                    if check_server_file(filename, client_socket):
                                        choice_fileexists = show_fileexists_menu()
                                        if choice_fileexists == 0:
                                            mode = ''
                                        elif choice_fileexists == 1:
                                            mode = "ADD"

                                    if mode == 'WRITE' or mode == 'ADD':
                                        put_file(path, client_socket, mode, filename)
                    elif choice == 3:
                        filename = input_filename()
                        if filename:
                            del_file(filename, client_socket)
        # except ConnectionResetError:
        #     print("Disconnect")
        # except socket.error as e:
        #     print(e.message)
        except Exception as e:
            pass
            # print(f"An error occurred: {e}")


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
    return input("Введите путь к файлу:")


def input_filename() -> str:
    while True:
        filename = input("Введите имя файла на сервере :")
        if ' ' not in filename:
            return filename
        else:
            print("Имя файла не должно содержать пробелы")


def get_file_list(client_socket) -> list:
    files_list = []

    if client_socket := check_connection(client_socket):
        client_socket.settimeout(10)
        client_socket.sendall(b'LIST'.ljust(1024, b' '))
        header = client_socket.recv(1024).decode(encoding).strip()
        if header.startswith('LIST'):
            _, filesize = header.split(' ', 1)

            buffer = b''
            count = 0
            if int(filesize) > 1024:
                count = int(filesize) // 1024
            bytes_remainder = int(filesize) - 1024 * count
            for i in range(1, count + 1):
                buffer += client_socket.recv(1024)
            if bytes_remainder:
                buffer += client_socket.recv(bytes_remainder)

            files_list = buffer.split(b'\n')

    return list(map(lambda x: x.decode(encoding), files_list))


def show_file_list(files: list) -> None:
    print("\n" + "=" * 83)
    print(f"{'Имя файла':<40} {'Размер':<10}")
    print("=" * 83)
    if files:
        for filedata in files:
            filename, filesize = filedata.split(' ', 1)
            print(f"{filename:<40} {filesize:<10}")
    else:
        print("Файлов нет")
    print("=" * 83 + "\n")


def check_local_file(path: str) -> bool:
    fullpath = path + ".txt"
    if not os.path.isfile(fullpath):
        print(f"Локальный файл {fullpath} не найден")
        return False
    return True


def check_server_file(filename: str, client_socket) -> bool:
    if client_socket := check_connection(client_socket):
        client_socket.settimeout(5)
        client_socket.sendall(f'CHECK {os.path.basename(filename)}'.encode(encoding).ljust(1024, b' '))
        ack = client_socket.recv(1024).decode(encoding).strip()

        if ack == "EXISTS":
            return True

    return False


def put_file(path: str, client_socket, mode: str, filename: str) -> None:
    if client_socket := check_connection(client_socket):
        client_socket.settimeout(None)
        fullpath = path + ".txt"
        client_socket.sendall(f'PUT {filename} {os.path.getsize(fullpath)} {mode}'.encode(encoding).ljust(1024, b' '))

        with open(fullpath, 'rb') as f:
            while chunk := f.read(1024):
                client_socket.sendall(chunk)

        client_socket.settimeout(5)
        ack = client_socket.recv(1024).decode(encoding).strip()
        if ack == '':
            print("Долгий ответ от сервера")
        elif ack == 'SUCCESS':
            print("Файл успешно добавлен.")
        elif ack.startswith('ERROR'):
            print(get_error_message(ack))


def del_file(filename: str, client_socket) -> None:
    if client_socket := check_connection(client_socket):
        client_socket.settimeout(5)
        client_socket.sendall(f'DEL {filename}'.encode(encoding).ljust(1024, b' '))

        ack = client_socket.recv(1024).decode(encoding)
        if ack == '':
            print("Долгий ответ от сервера")
        elif ack == 'SUCCESS':
            print("Файл успешно удален.")
        elif ack.startswith('ERROR'):
            print(get_error_message(ack))


def prog_exit(client_socket):
    if client_socket:
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()
    print("До свидания!!!")
    sys.exit()


def get_error_message(msg):
    return msg.split(' ', 1)[1]


if __name__ == "__main__":
    start_client()
