import asyncio

host = '127.0.0.1'
port = 8020
files_dir = '../files'


class Server:
    def __init__(self, host: str, port: int, files_dir: str):
        self.host = host
        self.port = port
        self.__forbidden_chars = r'[\\/:"*?<>|]'

    def start(self):
        pass

    def __get_request(self, client_socket) -> str | None:
        return client_socket.recv(512).decode('utf-8').strip()

    def __send_response(self, client_socket, data: bin) -> None:
        client_socket.sendall(data)

    def __create_byte_data(self, *args: str) -> bin:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')


if __name__ == "__main__":
    server = Server(host, port, files_dir)
    server.start()
