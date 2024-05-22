import socket
import threading
import os

host = '127.0.0.1'
port = 8020

files_dir = './files'
encoding = 'utf-8'


def get_files_list() -> list:
    # return [f for f in os.listdir(files_dir) if os.path.isfile(f) and f.endswith('.txt')]
    # return [f for f in os.listdir(files_dir) if os.path.isfile(f)]
    return [f for f in os.listdir(files_dir)]


def send_files_list(client_socket):
    client_socket.sendall('\n'.join(get_files_list()).encode())
    client_socket.sendall(b'\nEND_OF_LIST')


def save_file(client_socket, filename: str, filesize: int):
    with open(files_dir + "/" + filename, 'wb') as f:
        count = filesize // 1024 + 1

        for i in range(1, count + 1):
            data = client_socket.recv(1024)
            f.write(data)
    client_socket.sendall(b'SUCCESS')


def check_filename(filename) -> bool:
    return os.path.exists(files_dir + "/" + filename)


def get_file(client_socket):
    pass


def del_file(filename: str, client_socket):
    if check_filename(filename):
        os.remove(files_dir + "/" + filename)
        client_socket.sendall(b'SUCCESS')
    else:
        client_socket.sendall(b'ERROR File not exist')


def handle(client_socket):
    while True:
        try:
            header = client_socket.recv(1024).decode(encoding).strip()

            if header.startswith('LIST'):
                send_files_list(client_socket)
            elif header.startswith('GET'):
                get_file(client_socket)
            elif header.startswith('PUT'):
                _, filename, filesize = header.split(' ', 2)

                if not check_filename(filename):
                    client_socket.sendall(b'ACK_FILENAME')
                    save_file(client_socket, filename, int(filesize))
                else:
                    client_socket.sendall(b'ERROR File exists')
            elif header.startswith('DEL'):
                _, filename = header.split(' ', 1)
                del_file(filename, client_socket)
            elif header == "":
                break

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
