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
        self.__workserver_socket = None
        self.__tokenserver_socket = None
        self.client_id = 0
        self.token = ''

    def start(self):
        while True:
            try:
                if not self.__is_connected(self.__tokenserver_socket):
                    self.__set_connection_to_tokenserver()
                else:
                    self.__send_request(self.__tokenserver_socket, self.__create_byte_header('GET'))
                    if (response := self.__get_response(self.__tokenserver_socket)) and response.startswith('GET'):
                        _, self.client_id, self.token = response.split('\n')
                    self.__tokenserver_socket.close()
                    break
            except Exception as e:
                print(e)
                if self.__tokenserver_socket:
                    self.__tokenserver_socket.close()

        while True:
            try:
                if not self.__is_connected(self.__workserver_socket):
                    self.__set_connection_to_workserver()
                else:
                    self.__send_request(self.__workserver_socket,
                                        self.__create_byte_header('GET', self.token))
                    if response := self.__get_response(self.__workserver_socket):
                        _, res = response.split('\n', 1)
                        print(f"{self.client_id} {res}")
            except Exception as e:
                print(e)
                if self.__workserver_socket:
                    self.__workserver_socket.close()

    def __is_connected(self, used_socket: socket.socket) -> bool:
        if used_socket:
            try:
                self.__send_request(used_socket, self.__create_byte_header('TEST'))
                if (response := self.__get_response(used_socket)) and response.startswith('TEST_SUCCESS'):
                    return True
            except:
                pass
        return False

    def __set_connection_to_workserver(self) -> None:
        self.__workserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__workserver_socket.settimeout(5)
        self.__workserver_socket.connect((self.host, self.port))

    def __set_connection_to_tokenserver(self) -> None:
        self.__tokenserver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__tokenserver_socket.settimeout(5)
        self.__tokenserver_socket.connect((self.tokenserver_host, self.tokenserver_port))

    def __send_request(self, used_socket, data: bin) -> None:
        used_socket.sendall(data)

    def __get_response(self, used_socket: socket.socket) -> str | None:
        return used_socket.recv(512).decode('utf-8').strip()

    def __create_byte_header(self, *args) -> bin:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')


if __name__ == "__main__":
    for _ in range(0, 20):
        client = Client(workserver_host, workserver_port, tokenserver_host, tokenserver_port)
        process = multiprocessing.Process(target=client.start)
        process.start()
