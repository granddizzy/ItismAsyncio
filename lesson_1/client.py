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

            print('Подключение установлено')

            while True:
                show_main_menu()
                choice = input_choice(4)

                if choice == 0:
                    prog_exit(client_socket)
                elif choice == 1:
                    show_file_list(get_file_list(client_socket))
                elif choice == 2:
                    path = input_path_file()
                    send_file(path, client_socket)
                elif choice == 3:
                    del_file(input_filename(), client_socket)
    except Exception as e:
        print(f"An error occurred: {e}")


def show_main_menu() -> None:
    print()
    print('Главное меню:')
    print('0.Выйти')
    print('1.Получить список файлов')
    print('2.Добавить файл')
    print('3.Удалить файл')
    print()


def input_choice(max_choice_num: int) -> int | None:
    while True:
        answer = input("Сделайте выбор:")
        if answer.isdigit() and 0 <= int(answer) <= max_choice_num:
            return int(answer)


def input_path_file() -> str:
    path = input("Введите путь к файлу:")
    return path


def input_filename() -> str:
    filename = input("Введите имя файла:")
    return filename


def get_file_list(client_socket) -> list:
    files_list = []

    client_socket.send(b'LIST')

    data = client_socket.recv(1024).decode(encoding)
    while data:
        if 'END_OF_LIST' in data:
            break
        files_list.append(data.strip())
        data = client_socket.recv(1024).decode(encoding)

    return files_list


def show_file_list(files: list) -> None:
    if files:
        print("\n" + "=" * 83)
        for filename in files:
            print(filename)

        print("=" * 83 + "\n")
    else:
        print("Файлов нет")


def send_file(path: str, client_socket) -> None:
    if not os.path.isfile(path):
        print("Такого файла не существует")
        return None

    client_socket.sendall(f'PUT {os.path.basename(path)} {os.path.getsize(path)}'.encode(encoding))
    ack = client_socket.recv(1024).decode(encoding).strip()

    if ack != 'ACK_FILENAME':
        print("Filename exists")
        return None

    with open(path, 'rb') as f:
        while chunk := f.read(1024):
            client_socket.sendall(chunk)

    ack = client_socket.recv(1024).decode(encoding).strip()
    if ack == 'SUCCESS':
        print("File successfully transferred.")
    else:
        print("Failed to transfer file.")


def del_file(filename: str, client_socket) -> None:
    client_socket.sendall(f'DEL {filename}'.encode(encoding))

    ack = client_socket.recv(1024).decode(encoding)
    if ack == 'SUCCESS':
        print("File successfully deleted.")
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
