import multiprocessing
import socket

workserver_host = '127.0.0.1'
workserver_port = 8021

tokenserver_host = '127.0.0.1'
tokenserver_port = 8022


class Client:
    def __init__(self, workserver_host: str, workserver_port: int, tokenserver_host: str, tokenserver_port: int):
        self.host = workserver_host
        self.port = workserver_port
        self.tokenserver_host = tokenserver_host
        self.tokenserver_port = tokenserver_port
        self.workserver_socket = None
        self.tokenserver_socket = None
        self.client_id = 0
        self.token = ''

    def start(self):
        while True:
            try:
                if not self.is_connected(self.tokenserver_socket):
                    self.set_connection_to_tokenserver()
                else:
                    self.send_request(self.tokenserver_socket, self.create_byte_header('GET'))
                    if (response := self.get_response(self.tokenserver_socket)) and response.startswith('GET'):
                        _, self.client_id, self.token = response.split('\n')
                    self.tokenserver_socket.close()
                    break
            except Exception as e:
                print(e)
                if self.tokenserver_socket:
                    self.tokenserver_socket.close()

        while True:
            try:
                if not self.is_connected(self.workserver_socket):
                    self.set_connection_to_workserver()
                else:
                    self.send_request(self.workserver_socket,
                                      self.create_byte_header('GET', self.token))
                    if response := self.get_response(self.workserver_socket):
                        _, res = response.split('\n', 1)
                        print(f"{self.client_id} {res}")
            except Exception as e:
                print(e)
                if self.workserver_socket:
                    self.workserver_socket.close()

    def is_connected(self, used_socket: socket.socket) -> bool:
        if used_socket:
            try:
                self.send_request(used_socket, self.create_byte_header('TEST'))
                if (response := self.get_response(used_socket)) and response.startswith('TEST_SUCCESS'):
                    return True
            except:
                pass
        return False

    def set_connection_to_workserver(self) -> None:
        self.workserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.workserver_socket.settimeout(5)
        self.workserver_socket.connect((self.host, self.port))

    def set_connection_to_tokenserver(self) -> None:
        self.tokenserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tokenserver_socket.settimeout(5)
        self.tokenserver_socket.connect((self.tokenserver_host, self.tokenserver_port))

    def send_request(self, used_socket, data: bin) -> None:
        used_socket.sendall(data)

    def get_response(self, used_socket: socket.socket) -> str | None:
        return used_socket.recv(512).decode('utf-8').strip()

    def create_byte_header(self, *args) -> bin:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')


if __name__ == "__main__":
    for _ in range(0, 20):
        client = Client(workserver_host, workserver_port, tokenserver_host, tokenserver_port)
        process = multiprocessing.Process(target=client.start)
        process.start()
