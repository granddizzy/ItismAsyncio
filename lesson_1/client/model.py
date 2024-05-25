import socket
import os

encoding = 'utf-8'

forbidden_chars = r'[\\/:"*?<>|]'
client_socket: socket.socket | None = None


class ClientError:
    def __init__(self, message: str):
        self.message = message


def get_header() -> str | ClientError:
    try:
        return client_socket.recv(512).decode(encoding).strip()
    except socket.timeout:
        return ClientError("Долгий ответ от сервера")
    except (ConnectionError, socket.error) as e:
        return ClientError("Ошибка соединения")


class ClientModel:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client_socket = None

    def set_connection(self) -> None | ClientError:
        global client_socket
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.host, self.port))
            return None
        except (socket.timeout, ConnectionError, socket.error) as e:
            return ClientError(f"{e}")

    def is_connected(self) -> bool:
        global client_socket
        if not client_socket:
            return False

        if self.send_data(self.create_byte_header('TEST')) is None:
            return True

        return False

    def check_connection(self) -> bool:
        global client_socket
        if not self.is_connected():
            # show_message("Соединение с сервером потеряно. Переподключение...")

            if client_socket:
                client_socket.close()

            if isinstance(res := self.set_connection(), ClientError):
                # show_error(res)
                return False

            # show_message("Соединение установлено")

        return True

    def get_file_list(self) -> list | ClientError:
        files_list = []

        if self.check_connection():
            if isinstance(res := self.send_data(self.create_byte_header('LIST')), ClientError):
                return res
            else:
                if isinstance(res := get_header(), ClientError):
                    return res
                elif res.startswith('LIST'):
                    _, filesize_str = res.split('\n', 1)

                    filesize = int(filesize_str)
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
                        files_list = buffer.split(b'\n')

        return list(map(lambda x: x.decode(encoding), files_list))

    def put_file(self, path: str, mode: str, filename: str) -> None | ClientError:
        fullpath = path + ".txt"
        if self.check_connection():
            if isinstance(res := self.send_data(
                    self.create_byte_header('PUT', filename, str(os.path.getsize(fullpath)), mode)),
                          ClientError):
                return res
            else:
                try:
                    with open(fullpath, 'rb') as f:
                        while chunk := f.read(1024):
                            if isinstance(res := self.send_data(chunk), ClientError):
                                return res
                except (IOError, OSError) as e:
                    return ClientError("Ошибка чтения файла")

                if isinstance(res := get_header(), ClientError):
                    return res
                elif res.startswith('ERROR'):
                    return ClientError(self.get_error_message(res))

    def del_file(self, filename: str) -> None | ClientError:
        if self.check_connection():
            if isinstance(res := self.send_data(self.create_byte_header('CHECK', filename)), ClientError):
                return res
            else:
                if isinstance(res := get_header(), ClientError):
                    return res
                elif res.startswith("NOT_EXISTS"):
                    return ClientError(f"Файла {filename} нет на сервере")

                if isinstance(res := self.send_data(self.create_byte_header('DEL', filename)), ClientError):
                    return res
                else:
                    if isinstance(res := get_header(), ClientError):
                        return res
                    elif res.startswith('ERROR'):
                        return ClientError(self.get_error_message(res))

    def create_byte_header(self, *args) -> bin:
        return '\n'.join(args).encode(encoding).ljust(512, b' ')

    def get_error_message(self, msg: str) -> str:
        return msg.split('\n', 1)[1]

    def close_connection(self) -> None:
        if client_socket:
            if self.is_connected():
                self.send_data(self.create_byte_header('QUIT'))
                try:
                    client_socket.shutdown(socket.SHUT_RDWR)
                except (ConnectionError, socket.error):
                    pass

            client_socket.close()

    def check_server_file(self, filename: str) -> bool | ClientError:
        if self.check_connection() and self.send_data(self.create_byte_header('CHECK', filename)) is None:
            res = get_header()
            if isinstance(res, ClientError):
                return res
            elif res and res.startswith("EXISTS"):
                return True
        return False

    def send_data(self, data: bin) -> None | ClientError:
        try:
            client_socket.sendall(data)
        except (socket.timeout, ConnectionError, socket.error, Exception):
            return ClientError("Ошибка соединения")

        return None

    def check_local_file(self, path: str) -> bool | ClientError:
        fullpath = path + ".txt"
        if not os.path.isfile(fullpath):
            return ClientError(f"Локальный файл {fullpath} не найден")
        elif os.path.getsize(fullpath) == 0:
            return ClientError(f"Локальный файл {fullpath} пустой")
        return True
