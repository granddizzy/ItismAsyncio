import socket
import sys
import os

host = '127.0.0.1'
port = 8020

encoding = 'utf-8'


def start_client():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))

            print('Соединение с сервером установлено')

            while True:
                choice = show_main_menu()

                if choice == 0:
                    prog_exit(client_socket)
                elif choice == 1:
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

    client_socket.send(b'LIST')
    ack = client_socket.recv(1024).decode(encoding).strip()

    if ack.startswith('ACK'):
        _, filesize = ack.split(' ', 1)

        count = int(filesize) // 1024 + 1

        for i in range(1, count + 1):
            data = client_socket.recv(1024)
            files_list = data.split(b'\n')

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
    client_socket.sendall(f'CHECK {os.path.basename(filename)}'.encode(encoding))
    ack = client_socket.recv(1024).decode(encoding).strip()

    if ack == "EXISTS":
        return True

    return False


def put_file(path: str, client_socket, mode: str, filename: str) -> None:
    fullpath = path + ".txt"
    client_socket.sendall(f'PUT {filename} {os.path.getsize(fullpath)} {mode}'.encode(encoding))

    with open(fullpath, 'rb') as f:
        while chunk := f.read(1024):
            client_socket.sendall(chunk)

    ack = client_socket.recv(1024).decode(encoding).strip()
    if ack == 'SUCCESS':
        print("Файл успешно отправлен.")
    else:
        print(get_error_message(ack))


def del_file(filename: str, client_socket) -> None:
    client_socket.sendall(f'DEL {filename}'.encode(encoding))

    ack = client_socket.recv(1024).decode(encoding)
    if ack == 'SUCCESS':
        print("Файл успешно удален.")
    else:
        print(get_error_message(ack))


def prog_exit(client_socket):
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    print("До свидания!!!")
    sys.exit()


def get_error_message(msg):
    return msg.split(' ', 1)[1]


if __name__ == "__main__":
    start_client()
