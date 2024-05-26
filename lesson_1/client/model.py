import socket
import os
import sys

encoding = 'utf-8'
forbidden_chars = r'[\\/:"*?<>|]'


class ClientError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ClientModel:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client_socket = None

    def set_connection(self) -> None:
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((self.host, self.port))
        except (socket.timeout, ConnectionError, socket.error) as e:
            raise ClientError(f"Ошибка соединения: {e}")

    def is_connected(self) -> bool:
        if not self.client_socket:
            return False
        try:
            self.send_data(self.create_byte_header('TEST'))
            return True
        except ClientError:
            return False

    def check_connection(self) -> None:
        if not self.is_connected():
            if self.client_socket:
                self.client_socket.close()
            self.set_connection()

    def get_file_list(self) -> list:
        files_list = []
        self.send_data(self.create_byte_header('LIST'))
        if (res := self.get_header()) and res.startswith('LIST'):
            _, filesize = res.split('\n', 1)
            data = self.receive_data(int(filesize))
            if data:
                files_list = data.split(b'\n')

        return list(map(lambda x: x.decode(encoding), files_list))

    def put_file(self, path: str, mode: str, filename: str) -> None:
        fullpath = f"{path}.txt"
        self.send_data(self.create_byte_header('PUT', filename, str(os.path.getsize(fullpath)), mode))
        try:
            with open(fullpath, 'rb') as f:
                while chunk := f.read(1024):
                    self.send_data(chunk)
        except (IOError, OSError) as e:
            raise ClientError(f"Ошибка чтения файла: {e}")

        if (res := self.get_header()) and res.startswith('ERROR'):
            raise ClientError(self.get_error_message(res))

    def receive_data(self, filesize: int) -> bytes:
        buffer = b''
        count = filesize // 1024
        bytes_remainder = filesize % 1024
        for _ in range(count):
            buffer += self.client_socket.recv(1024)
        if bytes_remainder:
            buffer += self.client_socket.recv(bytes_remainder)
        return buffer

    def del_file(self, filename: str) -> None:
        self.send_data(self.create_byte_header('CHECK', filename))
        if (res := self.get_header()) and res.startswith("NOT_EXISTS"):
            raise ClientError(f"Файла {filename} нет на сервере")

        self.send_data(self.create_byte_header('DEL', filename))
        if (res := self.get_header()) and res.startswith('ERROR'):
            raise ClientError(self.get_error_message(res))

    def save_file(self, filename: str, path: str, mode: str) -> None:
        self.send_data(self.create_byte_header('GET', filename))
        if (res := self.get_header()) and res.startswith("NOT_EXISTS"):
            raise ClientError(f"Файла {filename} нет на сервере")
        elif res.startswith("GET"):
            _, filesize = res.split('\n', 1)
            buffer = self.receive_data(int(filesize))

            try:
                if buffer:
                    with open(f"{path}.txt", 'ab' if mode == 'ADD' else 'wb') as f:
                        f.write(buffer)
            except (IOError, OSError) as e:
                raise ClientError(f"Ошибка записи файла: {e}")

    def create_byte_header(self, *args) -> bin:
        return '\n'.join(args).encode(encoding).ljust(512, b' ')

    def get_error_message(self, msg: str) -> str:
        return msg.split('\n', 1)[1]

    def close_connection(self) -> None:
        if self.client_socket:
            if self.is_connected():
                self.send_data(self.create_byte_header('QUIT'))
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except (ConnectionError, socket.error):
                    pass
            self.client_socket.close()
        sys.exit()

    def is_server_file_exists(self, filename: str) -> bool:
        self.send_data(self.create_byte_header('CHECK', filename))
        if (res := self.get_header()) and res.startswith("EXISTS"):
            return True
        return False

    def send_data(self, data: bin) -> None:
        try:
            self.client_socket.sendall(data)
        except (socket.timeout, ConnectionError, socket.error) as e:
            raise ClientError(f"Ошибка отправки данных: {e}")

    def is_local_file_exists(self, path: str) -> bool:
        return os.path.isfile(f"{path}.txt")

    def is_local_file_filled(self, path: str) -> bool:
        return os.path.getsize(f"{path}.txt") > 0

    def get_header(self) -> str:
        try:
            return self.client_socket.recv(512).decode(encoding).strip()
        except socket.timeout:
            raise ClientError("Долгий ответ от сервера")
        except (ConnectionError, socket.error) as e:
            raise ClientError(f"Ошибка соединения: {e}")
