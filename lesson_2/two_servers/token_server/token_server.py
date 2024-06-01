import random
import string
import select
import socket
import os

host = '127.0.0.1'
port = 8022


def check_bd() -> bool:
    if not os.path.exists('db'):
        try:
            with open('db', 'w') as f:
                pass
        except IOError as e:
            print(f"DB creation error ': {e}")
            return False
    return True


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sockets_list = []

    def disconnect(self, client_socket):
        self.sockets_list.remove(client_socket)
        # print(f"Disconnected {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
        client_socket.close()

    def start(self):
        if check_bd():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((host, port))
                server_socket.listen()
                print(f"Token server is listening on {host}:{port}")
                self.sockets_list = [server_socket]
                while True:
                    read_sockets, write_sockets, error_sockets = select.select(self.sockets_list, self.sockets_list,
                                                                               self.sockets_list)
                    for notified_socket in read_sockets:
                        try:
                            if notified_socket == server_socket:
                                client_socket, _ = server_socket.accept()
                                self.sockets_list.append(client_socket)
                            else:
                                if (request := self.get_request(notified_socket)) and request.startswith('GET'):
                                    client_id = self.generate_id()
                                    token = self.generate_token(32)
                                    self.save_to_storage(client_id, token)
                                    self.send_response(notified_socket, self.create_byte_header('GET',
                                                                                                f"{client_id}",
                                                                                                f"{token}"))
                                    print(f"Issued the token {token} to the client {notified_socket.getpeername()}")
                                    self.disconnect(notified_socket)
                                elif request.startswith('CHECK'):
                                    _, token = request.split('\n', 1)
                                    client_id = self.check_token(token)
                                    print(
                                        f"Sending a response to a token verification request {notified_socket.getpeername()}")
                                    self.send_response(notified_socket, self.create_byte_header('CHECK',
                                                                                                f"{token}",
                                                                                                f"{client_id}"))
                                elif request.startswith('TEST'):
                                    self.send_response(notified_socket, self.create_byte_header('TEST_SUCCESS'))
                        except Exception as e:
                            print(e)
                            self.disconnect(notified_socket)

                    for notified_socket in error_sockets:
                        print(f"Error socket {notified_socket}")

    def get_request(self, client_socket) -> str | None:
        return client_socket.recv(512).decode('utf-8').strip()

    def send_response(self, client_socket, data: bin) -> None:
        client_socket.sendall(data)

    def generate_token(self, length: int):
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_and_digits) for _ in range(length))

    def generate_id(self):
        # return random.randint(1000, 9999)
        try:
            with open('db', 'rb') as file:
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                if file_size:
                    file.seek(-2, os.SEEK_END)
                    while file.tell() > 0:
                        if file.read(1) == b'\n':
                            break
                        file.seek(-2, os.SEEK_CUR)
                    last_line = file.readline().decode().strip()
                    client_id, _ = last_line.split(':', 1)
                    return int(client_id) + 1
                else:
                    return 1
        except IOError as e:
            print(e)

    def save_to_storage(self, client_id: int, token: str):
        try:
            with open('db', 'a') as f:
                f.write(f"{client_id}:{token}\n")
        except IOError as e:
            print(e)

    def check_token(self, token: str) -> int:
        try:
            with open('db', 'r') as f:
                for line in f:
                    client_id, stored_token = line.strip().split(':')
                    if stored_token == token:
                        return client_id
        except IOError:
            return 0

    def create_byte_header(self, *args: str) -> bin:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')


if __name__ == "__main__":
    server = Server(host, port)
    server.start()
