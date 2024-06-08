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


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client_socket = None
        self.forbidden_chars = r'[\\/:"*?<>|]'

    async def set_connection(self) -> None:
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.setblocking(False)
            loop = asyncio.get_event_loop()
            await loop.sock_connect(self.client_socket, (self.host, self.port))
        except (socket.timeout, ConnectionError, socket.error) as e:
            raise ClientError(f"Ошибка соединения: {e}")

    async def is_connected(self) -> bool:
        try:
            loop = asyncio.get_event_loop()
            await self.__send_header(loop, command='TEST')
            header = await self.__get_header(loop)
            if header.status == 'SUCCESS':
                return True
        except OSError:
            return False

    async def check_connection(self) -> None:
        if not await self.is_connected():
            await self.set_connection()

    async def get_file_list(self) -> list:
        files_list = []
        loop = asyncio.get_event_loop()
        await self.__send_header(loop, command='GET_LIST')
        header = await self.__get_header(loop)
        if header.status == 'LIST':
            data = await self.__receive_data(loop, header.filesize)
            if data:
                files_list = data.split(b'\n')

        return list(map(lambda x: x.decode('utf-8'), files_list))

    async def put_file(self, path: str, mode: str, filename: str) -> None:
        loop = asyncio.get_event_loop()
        filesize = os.path.getsize(path)
        await self.__send_header(loop, command='PUT', filename=filename, filesize=filesize, mode=mode)
        header = await self.__get_header(loop)
        if header.status == 'READY':
            buffer_size = 1024
            if filesize > 10_485_760:
                buffer_size = 65536

            try:
                async with aiofiles.open(path, 'rb') as f:
                    while chunk := await f.read(buffer_size):
                        await loop.sock_sendall(self.client_socket, chunk)
            except (IOError, OSError) as e:
                raise ClientError(f"Ошибка чтения файла: {e}")

            header = await self.__get_header(loop)
            if header.status != 'SUCCESS':
                raise ClientError(header.message)
        else:
            raise ClientError(header.message)

    async def __receive_data(self, loop: AbstractEventLoop, filesize: int) -> bytes:
        bytes_received = 0
        data = b''
        while bytes_received < filesize:
            chunk = await loop.sock_recv(self.client_socket, min(1024, filesize - bytes_received))
            if not chunk:
                break
            bytes_received += len(chunk)
            data += chunk
        return data

    async def del_file(self, filename: str) -> None:
        loop = asyncio.get_event_loop()
        await self.__send_header(loop, command='CHECK', filename=filename)
        header = await self.__get_header(loop)
        if header.status == "NOT_EXISTS":
            raise ClientError(f"Файла {filename} нет на сервере")

        await self.__send_header(loop, command='DEL', filename=filename)
        header = await self.__get_header(loop)
        if header.status == 'ERROR':
            raise ClientError(header.message)

    async def save_file(self, filename: str, path: str, mode: str) -> None:
        loop = asyncio.get_event_loop()
        await self.__send_header(loop, command='GET', filename=filename)
        header = await self.__get_header(loop)
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
                        chunk = await loop.sock_recv(self.client_socket,
                                                     min(buffer_size, header.filesize - bytes_received))
                        if not chunk:
                            break
                        await f.write(chunk)
                        bytes_received += len(chunk)
            except (IOError, OSError) as e:
                raise ClientError(f"Ошибка записи файла: {e}")

    async def close_connection(self) -> None:
        if self.client_socket:
            if await self.is_connected():
                loop = asyncio.get_event_loop()
                await self.__send_header(loop, command='QUIT')
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except (ConnectionError, socket.error):
                    pass
            self.client_socket.close()

    async def is_server_file_exists(self, filename: str) -> bool:
        loop = asyncio.get_event_loop()
        await self.__send_header(loop, command='CHECK', filename=filename)
        header = await self.__get_header(loop)
        if header.status == "EXISTS":
            return True
        return False

    def is_local_file_exists(self, path: str) -> bool:
        return os.path.isfile(path)

    def is_local_file_filled(self, path: str) -> bool:
        return os.path.getsize(path) > 0

    async def __get_header(self, loop: asyncio.AbstractEventLoop) -> ResponseHeader | None:
        try:
            data = await asyncio.wait_for(loop.sock_recv(self.client_socket, 512), 5)
            str_data = data.decode('utf-8').strip()
            return ResponseHeader(*str_data.split('\n'))
        except asyncio.TimeoutError:
            return ResponseHeader('Error', 'Time out')

    async def __send_header(self, loop: asyncio.AbstractEventLoop, command: str, filename: str = '',
                            filesize: int = 0, mode: str = 'WRITE') -> None:
        b_data = self.__create_byte_header(command, filename, str(filesize), mode)
        await loop.sock_sendall(self.client_socket, b_data)

    @staticmethod
    def __create_byte_header(*args: str) -> bytes:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')
