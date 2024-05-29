import random
import string
import select
import socket
import os

host = '127.0.0.1'
port = 8021


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sockets_list = []

    def disconnect(self, client_socket):
        self.sockets_list.remove(client_socket)
        print(f"Disconnected {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
        client_socket.close()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen()
            print(f"Work server is listening on {host}:{port}")
            self.sockets_list = [server_socket]
            while True:
                read_sockets, write_sockets, error_sockets = select.select(self.sockets_list, self.sockets_list,
                                                                           self.sockets_list)

                for notified_socket in read_sockets:
                    if notified_socket == server_socket:
                        client_socket, _ = server_socket.accept()
                        self.sockets_list.append(client_socket)
                    else:
                        try:
                            request = self.get_request(notified_socket)
                            if request:
                                if request.startswith('GET'):
                                    _, client_id, token = request.split('\n', 2)

                        except:
                            self.disconnect(notified_socket)

    def get_request(self, client_socket) -> str | None:
        try:
            return client_socket.recv(512).decode('utf-8').strip()
        except socket.timeout:
            print(f"Timeout {client_socket.getpeername()}")
        except (ConnectionError, socket.error) as e:
            print(e)

    def send_response(self, client_socket, data: bin) -> bool:
        try:
            client_socket.sendall(data)
            return True
        except (socket.timeout, ConnectionError, socket.error):
            return False

    def check_token(self, token: str) -> int:
        return 0

    def create_byte_header(self, *args: str) -> bin:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')


if __name__ == "__main__":
    server = Server(host, port)
    server.start()
