import asyncio
import os
import socket
from asyncio import AbstractEventLoop

import aiofiles


class ClientError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ResponseHeader:
    def __init__(self, status: str, message: str = '', filesize: str = 0) -> None:
        self.status = status
        self.message = message
        self.filesize = int(filesize)


class ConnectedSocket:

    def __init__(self, model):
        self.connection = None
        self.model = model

    async def __aenter__(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.setblocking(False)
            loop = asyncio.get_event_loop()
            await loop.sock_connect(self.connection, (self.model.host, self.model.port))
            return self.connection
        except (socket.timeout, ConnectionError, socket.error) as e:
            raise ClientError(f"Ошибка соединения: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            if await self.model.is_connected(self.connection):
                loop = asyncio.get_event_loop()
                await self.model.send_header(loop, self.connection, command='QUIT')
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except (ConnectionError, socket.error):
                    pass
            self.connection.close()


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.__forbidden_chars = r'[\\/:"*?<>|]'

    async def is_connected(self, client_socket) -> bool:
        try:
            loop = asyncio.get_event_loop()
            await self.send_header(loop, client_socket, command='TEST')
            header = await self.__get_header(loop, client_socket)
            if header.status == 'SUCCESS':
                return True
        except OSError:
            return False

    async def get_file_list(self, client_socket: socket.socket) -> list:
        files_list = []
        loop = asyncio.get_event_loop()
        await self.send_header(loop, client_socket, command='GET_LIST')
        header = await self.__get_header(loop, client_socket)
        if header.status == 'LIST':
            data = await self.__receive_data(loop, client_socket, header.filesize)
            if data:
                files_list = data.split(b'\n')

        return list(map(lambda x: x.decode('utf-8'), files_list))

    async def put_file(self, client_socket: socket.socket, path: str, mode: str, filename: str) -> None:
        loop = asyncio.get_event_loop()
        filesize = os.path.getsize(path)
        await self.send_header(loop, client_socket, command='PUT', filename=filename, filesize=filesize,
                               mode=mode)
        header = await self.__get_header(loop, client_socket)
        if header.status == 'READY':
            buffer_size = 1024
            if filesize > 10_485_760:
                buffer_size = 65536

            try:
                async with aiofiles.open(path, 'rb') as f:
                    while chunk := await f.read(buffer_size):
                        await loop.sock_sendall(client_socket, chunk)
            except (IOError, OSError) as e:
                raise ClientError(f"Ошибка чтения файла: {e}")

            header = await self.__get_header(loop, client_socket)
            if header.status != 'SUCCESS':
                raise ClientError(header.message)
        else:
            raise ClientError(header.message)

    async def __receive_data(self, loop: AbstractEventLoop, client_socket: socket.socket, filesize: int) -> bytes:
        bytes_received = 0
        data = b''
        while bytes_received < filesize:
            chunk = await loop.sock_recv(client_socket, min(1024, filesize - bytes_received))
            if not chunk:
                break
            bytes_received += len(chunk)
            data += chunk
        return data

    async def del_file(self, client_socket: socket.socket, filename: str) -> None:
        loop = asyncio.get_event_loop()
        await self.send_header(loop, client_socket, command='CHECK', filename=filename)
        header = await self.__get_header(loop, client_socket)
        if header.status == "NOT_EXISTS":
            raise ClientError(f"Файла {filename} нет на сервере")

        await self.send_header(loop, client_socket, command='DEL', filename=filename)
        header = await self.__get_header(loop, client_socket)
        if header.status == 'ERROR':
            raise ClientError(header.message)

    async def save_file(self, client_socket: socket.socket, filename: str, path: str, mode: str) -> None:
        loop = asyncio.get_event_loop()
        await self.send_header(loop, client_socket, command='GET', filename=filename)
        header = await self.__get_header(loop, client_socket)
        if header.status == "NOT_EXISTS":
            raise ClientError(f"Файла {filename} нет на сервере")

        if header.status == 'READY':
            buffer_size = 1024
            if header.filesize > 10_485_760:
                buffer_size = 65536

            bytes_received = 0
            try:
                async with aiofiles.open(path, 'ab' if mode == 'ADD' else 'wb') as f:
                    while bytes_received < header.filesize:
                        chunk = await loop.sock_recv(client_socket,
                                                     min(buffer_size, header.filesize - bytes_received))
                        if not chunk:
                            break
                        await f.write(chunk)
                        bytes_received += len(chunk)
            except (IOError, OSError) as e:
                raise ClientError(f"Ошибка записи файла: {e}")

    async def is_server_file_exists(self, client_socket: socket.socket, filename: str) -> bool:
        loop = asyncio.get_event_loop()
        await self.send_header(loop, client_socket, command='CHECK', filename=filename)
        header = await self.__get_header(loop, client_socket)
        if header.status == "EXISTS":
            return True
        return False

    def is_local_file_exists(self, path: str) -> bool:
        return os.path.isfile(path)

    def is_local_file_filled(self, path: str) -> bool:
        return os.path.getsize(path) > 0

    async def __get_header(self, loop: asyncio.AbstractEventLoop,
                           client_socket: socket.socket) -> ResponseHeader | None:
        try:
            data = await asyncio.wait_for(loop.sock_recv(client_socket, 512), 5)
            str_data = data.decode('utf-8').strip()
            return ResponseHeader(*str_data.split('\n'))
        except asyncio.TimeoutError:
            return ResponseHeader('Error', 'Time out')

    async def send_header(self, loop: asyncio.AbstractEventLoop, client_socket: socket.socket, command: str,
                          filename: str = '',
                          filesize: int = 0, mode: str = 'WRITE') -> None:
        b_data = self.__create_byte_header(command, filename, str(filesize), mode)
        await loop.sock_sendall(client_socket, b_data)

    @staticmethod
    def __create_byte_header(*args: str) -> bytes:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')

