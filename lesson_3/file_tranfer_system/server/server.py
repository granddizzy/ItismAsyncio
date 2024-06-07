import asyncio
import os
import re
from pathlib import Path
from asyncio.streams import StreamReader, StreamWriter

host = '127.0.0.1'
port = 8020
files_dir = '../files'


class RequestHeader:
    def __init__(self, command: str, filename: str, filesize: str, mode: str) -> None:
        self.command = command
        self.filename = filename
        self.filesize = int(filesize)
        self.mode = mode


class Server:
    def __init__(self, host: str, port: int, files_dir: str):
        self.host = host
        self.port = port
        self.__files_dir = files_dir
        self.__forbidden_chars = r'[\\/:"*?<>|]'

    async def start(self):
        if self.__check_directory():
            server = await asyncio.start_server(client_connected_cb=self.__handle,
                                                host=self.host,
                                                port=self.port
                                                )
            addr = server.sockets[0].getsockname()
            print(f'Serving on {addr}')

            async with server:
                await server.serve_forever()

    async def __handle(self, reader, writer):
        peername = writer.get_extra_info('peername')
        if peername:
            print(f"Connected {peername[0]}:{peername[1]}")
        while True:
            try:
                header = await self.__get_header(reader)
                if header.command:
                    if header.command == 'GET_LIST':
                        await self.__send_files_list(writer)
                    elif header.command == 'GET':
                        if self.__check_filename(header.filename):
                            await self.__get_file(writer, header.filename)
                        else:
                            await self.__send_header(writer, status='ERROR', message='File not exists')
                    elif header.command == 'CHECK':
                        if self.__check_filename(header.filename):
                            await self.__send_header(writer, status='EXISTS')
                        else:
                            await self.__send_header(writer, status='NOT_EXISTS')
                    elif header.command == 'PUT':
                        if not re.search(self.__forbidden_chars, header.filename):
                            await self.__send_header(writer, status='READY')
                            await self.__put_file(reader, writer, header.filename, header.filesize, header.mode)
                        else:
                            await self.__send_header(writer, status='ERROR', message='Forbidden chars')
                    elif header.command == 'DEL':
                        await self.__del_file(header.filename, writer)
                    elif header.command == 'TEST':
                        await self.__send_header(writer, status='SUCCESS')
                    elif header.command == 'QUIT':
                        await self.__disconnect(writer)
                        break
            except (ConnectionResetError, BrokenPipeError):
                peername = writer.get_extra_info('peername')
                if peername:
                    print(f"Client disconnected unexpectedly {peername[0]}:{peername[1]}")
                writer.close()
                await writer.wait_closed()
                break
            except Exception as e:
                peername = writer.get_extra_info('peername')
                if peername:
                    print(f"Client {peername[0]}:{peername[1]}")
                print(f"Error handling: {e}")
                writer.close()
                await writer.wait_closed()
                break

    def __check_filename(self, filename: str) -> bool:
        return os.path.exists(os.path.join(self.__files_dir, filename))

    @staticmethod
    async def __disconnect(writer: StreamWriter):
        peername = writer.get_extra_info('peername')
        if peername:
            print(f"Disconnected {peername[0]}:{peername[1]}")
        writer.close()
        await writer.wait_closed()

    @staticmethod
    async def __get_header(reader: StreamReader) -> RequestHeader | None:
        data = await reader.read(512)
        str_data = data.decode('utf-8').strip()
        return RequestHeader(*str_data.split('\n'))

    async def __send_header(self, writer: StreamWriter, status: str, message: str = '', filesize: int = 0) -> None:
        b_data = self.__create_byte_header(status, message, str(filesize))
        writer.write(b_data)
        await writer.drain()

    @staticmethod
    def __create_byte_header(*args: str) -> bytes:
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

    async def __send_files_list(self, writer: StreamWriter) -> None:
        data = '\n'.join(self.__get_files_list()).encode('utf-8')
        await self.__send_header(writer, status='LIST', filesize=len(data))
        writer.write(data)
        await writer.drain()

    async def __get_file(self, writer: StreamWriter, filename):
        fullpath = os.path.join(self.__files_dir, filename)
        await self.__send_header(writer, status='READY', filesize=os.path.getsize(fullpath))
        with open(fullpath, 'rb') as f:
            while chunk := f.read(1024):
                writer.write(chunk)
                await writer.drain()

    async def __put_file(self, reader: StreamReader, writer: StreamWriter, filename: str, filesize: int,
                         act: str) -> None:
        mode = 'wb'
        if self.__check_filename(filename) and act == 'ADD':
            mode = 'ab'

        bytes_received = 0
        try:
            with open(os.path.join(self.__files_dir, filename), mode) as f:
                while bytes_received < filesize:
                    chunk = await reader.read(min(1024, filesize - bytes_received))

                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
        except Exception as e:
            await self.__send_header(writer, status='ERROR', message='No data')
            return

        await self.__send_header(writer, status='SUCCESS')

    async def __del_file(self, filename: str, writer: StreamWriter) -> None:
        if self.__check_filename(filename):
            os.remove(os.path.join(files_dir, filename))
            await self.__send_header(writer, status='SUCCESS')
        else:
            await self.__send_header(writer, status='ERROR', message='File not exists')


async def main():
    server = Server(host, port, files_dir)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
