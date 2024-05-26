import socket
import sys
import threading
import os
import re
from pathlib import Path

host = '127.0.0.1'
port = 8020
timeout = 300

files_dir = '../files'
encoding = 'utf-8'
forbidden_chars = r'[\\/:"*?<>|]'


# clients = []


def get_files_list() -> list:
    return [
        f"{Path(f).stem}:{os.path.getsize(os.path.join(files_dir, f))}:{int(os.path.getmtime(os.path.join(files_dir, f)))}"
        for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]


def send_files_list(client_socket: socket.socket) -> bool:
    data = '\n'.join(get_files_list()).encode(encoding)
    if send_data(client_socket, create_byte_header('LIST', str(len(data)))) and send_data(client_socket, data):
        return True
    return False


def put_file(client_socket, filename: str, filesize: int, act: str) -> None:
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
        with open(os.path.join(files_dir, f"{filename}.txt"), mode) as f:
            f.write(buffer)

        send_data(client_socket, create_byte_header('SUCCESS'))
    else:
        send_data(client_socket, create_byte_header('ERROR', 'No data'))


def check_filename(filename: str) -> bool:
    return os.path.exists(os.path.join(files_dir, f"{filename}.txt"))


def get_file(client_socket, filename):
    fullpath = os.path.join(files_dir, f"{filename}.txt")
    send_data(client_socket, create_byte_header('GET', str(os.path.getsize(fullpath))))
    with open(fullpath, 'rb') as f:
        while chunk := f.read(1024):
            send_data(client_socket, chunk)


def del_file(filename: str, client_socket: socket.socket) -> None:
    if check_filename(filename):
        os.remove(os.path.join(files_dir, f"{filename}.txt"))
        send_data(client_socket, create_byte_header('SUCCESS'))
    else:
        send_data(client_socket, create_byte_header('ERROR', 'File not exists'))


def create_byte_header(*args: str) -> bin:
    return '\n'.join(args).encode(encoding).ljust(512, b' ')


def get_header(client_socket) -> str | None:
    try:
        return client_socket.recv(512).decode(encoding).strip()
    except socket.timeout:
        print(f"Timeout {client_socket.getpeername()}")
    except (ConnectionError, socket.error) as e:
        print(e)

    disconnect(client_socket)


def send_data(client_socket, data: bin) -> bool:
    try:
        client_socket.sendall(data)
        return True
    except (socket.timeout, ConnectionError, socket.error):
        return False


def handle(client_socket: socket.socket):
    while True:
        try:
            if (header := get_header(client_socket)) is not None:
                if header.startswith('LIST'):
                    send_files_list(client_socket)
                elif header.startswith('GET'):
                    _, filename = header.split('\n', 1)
                    if check_filename(filename):
                        get_file(client_socket, filename)
                    else:
                        client_socket.sendall(create_byte_header('ERROR', 'File not exists'))
                elif header.startswith('CHECK'):
                    _, filename = header.split('\n', 1)
                    if check_filename(filename):
                        send_data(client_socket, create_byte_header('EXISTS'))
                    else:
                        send_data(client_socket, create_byte_header('NOT_EXISTS'))
                elif header.startswith('PUT'):
                    _, filename, filesize, act = header.split('\n', 3)
                    if not re.search(forbidden_chars, filename):
                        put_file(client_socket, filename, int(filesize), act)
                    else:
                        send_data(client_socket, create_byte_header('ERROR', 'Forbidden chars'))
                elif header.startswith('DEL'):
                    _, filename = header.split('\n', 1)
                    del_file(filename, client_socket)
                elif header.startswith('QUIT'):
                    disconnect(client_socket)
        except Exception as e:
            print(f"An error occured {e}")


def disconnect(client_socket):
    print(f"Disconnected {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
    client_socket.close()
    sys.exit()


def check_directory() -> bool:
    try:
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)
    except OSError as e:
        print(f"Catalog creation error '{files_dir}': {e}")
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
                client_socket, _ = server_socket.accept()
                client_socket.settimeout(timeout)
                # clients.append(client_socket)

                print(f"Connected {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
                client_thread = threading.Thread(target=handle, args=(client_socket,))
                client_thread.start()


if __name__ == "__main__":
    start_server()
