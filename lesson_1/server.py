import socket
import threading
import os
import re
from pathlib import Path

host = '127.0.0.1'
port = 8020

files_dir = './files'
encoding = 'utf-8'
forbidden_chars = r'[\\/:"*?<>|]'
clients = []


def get_files_list() -> list:
    return [
        f"{Path(f).stem}:{os.path.getsize(os.path.join(files_dir, f))}:{int(os.path.getmtime(os.path.join(files_dir, f)))}"
        for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]


def send_files_list(client_socket):
    data = '\n'.join(get_files_list()).encode(encoding)
    client_socket.sendall(get_byte_header('LIST', str(len(data))))
    client_socket.sendall(data)


def put_file(client_socket, filename: str, filesize: int, act: str):
    mode = 'wb'

    if check_filename(filename) and act == 'ADD':
        mode = 'ab'

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
        with open(os.path.join(files_dir, filename) + ".txt", mode) as f:
            f.write(buffer)

        client_socket.sendall(get_byte_header('SUCCESS'))
    else:
        client_socket.sendall(get_byte_header('ERROR', 'No data'))


def check_filename(filename) -> bool:
    return os.path.exists(os.path.join(files_dir, filename) + ".txt")


def get_file(client_socket, filename):
    pass


def del_file(filename: str, client_socket):
    if check_filename(filename):
        os.remove(os.path.join(files_dir, filename) + ".txt")
        client_socket.sendall(get_byte_header('SUCCESS'))
    else:
        client_socket.sendall(get_byte_header('ERROR', 'File not exists'))


def get_byte_header(*args: str) -> bin:
    return '\n'.join(args).encode(encoding).ljust(512, b' ')


def handle(client_socket, client_address):
    client_socket.settimeout(300)
    while True:
        try:
            header = client_socket.recv(512).decode(encoding).strip()

            if header.startswith('LIST'):
                send_files_list(client_socket)
            elif header.startswith('GET'):
                _, filename = header.split('\n', 1)
                if check_filename(filename):
                    get_file(client_socket, filename)
                else:
                    client_socket.sendall(get_byte_header('ERROR', 'File not exists'))
            elif header.startswith('CHECK'):
                _, filename = header.split('\n', 1)
                if check_filename(filename):
                    client_socket.sendall(get_byte_header('EXISTS'))
                else:
                    client_socket.sendall(get_byte_header('NOT_EXISTS'))
            elif header.startswith('PUT'):
                _, filename, filesize, act = header.split('\n', 3)
                if not re.search(forbidden_chars, filename):
                    put_file(client_socket, filename, int(filesize), act)
                else:
                    client_socket.sendall(get_byte_header('ERROR', 'Forbidden chars'))
            elif header.startswith('DEL'):
                _, filename = header.split('\n', 1)
                del_file(filename, client_socket)
            elif header.startswith('QUIT'):
                print(f"Disconnected {client_address[0]}:{client_address[1]}")
                client_socket.close()
                break

        except (socket.timeout, ConnectionError, socket.error):
            print(f"Auto disconnected {client_address[0]}:{client_address[1]}")
            client_socket.close()
            break
        except Exception as e:
            print(f"An error occurred: {e}")


def check_directory() -> bool:
    try:
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)
    except OSError as e:
        print(f"Ошибка при создании каталога '{files_dir}': {e}")
        return False

    return True


def start_server():
    if check_directory():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen()
            print(f"Server is listening on {host}:{port}")

            while True:
                client_socket, client_address = server_socket.accept()
                # clients.append(client_socket)

                print(f"Connected {client_address[0]}:{client_address[1]}")
                client_thread = threading.Thread(target=handle, args=(client_socket, client_address))
                client_thread.start()


if __name__ == "__main__":
    start_server()
