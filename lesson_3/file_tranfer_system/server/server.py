import asyncio
import os
import socket
import sys
from pathlib import Path

host = '127.0.0.1'
port = 8020
files_dir = '../files'


class Server:
    def __init__(self, host: str, port: int, files_dir: str):
        self.host = host
        self.port = port
        self.__files_dir = files_dir
        self.__forbidden_chars = r'[\\/:"*?<>|]'

    async def start(self):
        if self.__check_directory():
            server_socket = self.__create_server_socket()
            loop = asyncio.get_event_loop()
            await loop.sock_connect(server_socket, (self.host, self.port))
            while True:
                client_socket, _ = server_socket.accept()
                await asyncio.create_task(self.__handle(client_socket))

    async def __handle(self, client_socket):
        loop = asyncio.get_running_loop()
        while True:
            try:
                if request := await self.__get_request(client_socket, loop):
                    if request.startswith('LIST'):
                        await self.__send_files_list(client_socket, loop)
                    elif request.startswith('GET'):
                        _, filename = request.split('\n', 1)
                        if self.__check_filename(filename):
                            await self.__get_file(client_socket, filename, loop)
                        else:
                            await self.__send_response(client_socket,
                                                       self.__create_byte_data('ERROR', 'File not exists'), loop)
                    elif request.startswith('CHECK'):
                        _, filename = request.split('\n', 1)
                        # if check_filename(filename):
                        #     send_data(client_socket, create_byte_header('EXISTS'))
                        # else:
                        #     send_data(client_socket, create_byte_header('NOT_EXISTS'))
                    elif request.startswith('PUT'):
                        _, filename, filesize, act = request.split('\n', 3)
                        # if not re.search(forbidden_chars, filename):
                        #     put_file(client_socket, filename, int(filesize), act)
                        # else:
                        #     send_data(client_socket, create_byte_header('ERROR', 'Forbidden chars'))
                    elif request.startswith('DEL'):
                        _, filename = request.split('\n', 1)
                        # del_file(filename, client_socket)
                    elif request.startswith('QUIT'):
                        self.__disconnect(client_socket)
            except Exception as e:
                print(f"Error handling client: {e}")
            # finally:
            #     client_socket.close()

    def __check_filename(self, filename: str) -> bool:
        return os.path.exists(os.path.join(self.__files_dir, f"{filename}.txt"))

    @staticmethod
    def __disconnect(client_socket):
        print(f"Disconnected {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
        client_socket.close()
        sys.exit()

    def __create_server_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.setblocking(False)
        return server_socket

    @staticmethod
    async def __get_request(client_socket: socket.socket, loop: asyncio.AbstractEventLoop) -> str | None:
        data = await loop.sock_recv(client_socket, 512)
        return data.decode('utf-8').strip()

    @staticmethod
    async def __send_response(client_socket: socket.socket, data: bytes, loop: asyncio.AbstractEventLoop) -> None:
        await loop.sock_sendall(client_socket, data)

    @staticmethod
    def __create_byte_data(*args: str) -> bytes:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')

    def __check_directory(self) -> bool:
        try:
            if not os.path.exists(self.__files_dir):
                os.makedirs(self.__files_dir)
        except OSError as e:
            print(f"Catalog creation error '{self.__files_dir}': {e}")
            return False

        return True

    def __get_files_list(self) -> list:
        return [
            f"{Path(f).stem}:{os.path.getsize(os.path.join(self.__files_dir, f))}:{int(os.path.getmtime(os.path.join(self.__files_dir, f)))}"
            for f in os.listdir(self.__files_dir) if os.path.isfile(os.path.join(self.__files_dir, f))]

    async def __send_files_list(self, client_socket: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
        data = '\n'.join(self.__get_files_list()).encode('utf-8')
        await self.__send_response(client_socket, self.__create_byte_data('LIST', str(len(data))), loop)
        await self.__send_response(client_socket, data, loop)

    async def __get_file(self, client_socket, filename, loop: asyncio.AbstractEventLoop):
        fullpath = os.path.join(self.__files_dir, f"{filename}.txt")
        await self.__send_response(client_socket, self.__create_byte_data('GET', str(os.path.getsize(fullpath))), loop)
        with open(fullpath, 'rb') as f:
            while chunk := f.read(1024):
                await self.__send_response(client_socket, chunk, loop)


async def main():
    server = Server(host, port, files_dir)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
