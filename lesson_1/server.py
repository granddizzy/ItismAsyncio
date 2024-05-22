import socket
import threading
import os

host = '127.0.0.1'
port = 8020

files_dir = "./"
encoding = 'utf-8'


def get_files_list() -> list:
    # return [f for f in os.listdir(files_dir) if os.path.isfile(f) and f.endswith('.txt')]
    return [f for f in os.listdir(files_dir) if os.path.isfile(f)]


def send_files_list(client_socket):
    client_socket.sendall('\n'.join(get_files_list()).encode())
    client_socket.sendall(b'\nEND_OF_LIST\n')


def save_file(client_socket):
    pass


def get_file(client_socket):
    pass


def handle(client_socket):
    while True:
        try:
            # начинаем принимать данные
            oper = client_socket.recv(1).decode(encoding)  # первый байт - вид операции

            if oper == "":
                pass
            elif oper == "0":  # запрос списка файлов
                print("Запрос получения списка файлов")
                send_files_list(client_socket)
            elif oper == "1":  # запрос получения файла
                get_file(client_socket)
            elif oper == "2":  # запрос записи файла
                save_file(client_socket)
            else:
                print(f"Не верный вид операции {oper}")

        except Exception as e:
            print(f"An error occurred: {e}")
            client_socket.close()
            break


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server is listening on {host}:{port}")

        while True:
            client_socket, _ = server_socket.accept()
            client_thread = threading.Thread(target=handle, args=(client_socket,))
            client_thread.start()


if __name__ == "__main__":
    start_server()
