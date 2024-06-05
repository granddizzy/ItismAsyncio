import asyncio
import os
import re
from pathlib import Path
from asyncio.streams import StreamReader, StreamWriter

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
            server = await asyncio.start_server(client_connected_cb=self.__handle,
                                                host=self.host,
                                                port=self.port
                                                )
            addr = server.sockets[0].getsockname()
            print(f'Serving on {addr}')

            async with server:
                await server.serve_forever()

    async def __handle(self, reader, writer):
        while True:
            try:
                if request := await self.__get_request(reader):
                    if request.startswith('LIST'):
                        await self.__send_files_list(writer)
                    elif request.startswith('GET'):
                        _, filename = request.split('\n', 1)
                        if self.__check_filename(filename):
                            await self.__get_file(writer, filename)
                        else:
                            await self.__send_response(writer,
                                                       self.__create_byte_data('ERROR', 'File not exists'))
                    elif request.startswith('CHECK'):
                        _, filename = request.split('\n', 1)
                        if self.__check_filename(filename):
                            await self.__send_response(writer, self.__create_byte_data('EXISTS'))
                        else:
                            await self.__send_response(writer, self.__create_byte_data('NOT_EXISTS'))
                    elif request.startswith('PUT'):
                        _, filename, filesize, act = request.split('\n', 3)
                        if not re.search(self.__forbidden_chars, filename):
                            await self.__put_file(reader, writer, filename, int(filesize), act)
                        else:
                            await self.__send_response(writer,
                                                       self.__create_byte_data('ERROR', 'Forbidden chars'))
                    elif request.startswith('DEL'):
                        _, filename = request.split('\n', 1)
                        await self.__del_file(filename, writer)
                    elif request.startswith('QUIT'):
                        await self.__disconnect(writer)
                        break
            except (ConnectionResetError, BrokenPipeError):
                print("Client disconnected unexpectedly")
                writer.close()
                await writer.wait_closed()
                break
            except Exception as e:
                print(f"Error handling client: {e}")
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
    async def __get_request(reader: StreamReader) -> str | None:
        data = await reader.read(512)
        return data.decode('utf-8').strip()

    @staticmethod
    async def __send_response(writer: StreamWriter, data: bytes) -> None:
        writer.write(data)
        await writer.drain()

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

    async def __send_files_list(self, writer: StreamWriter) -> None:
        data = '\n'.join(self.__get_files_list()).encode('utf-8')
        await self.__send_response(writer, self.__create_byte_data('LIST', str(len(data))))
        await self.__send_response(writer, data)

    async def __get_file(self, writer: StreamWriter, filename):
        fullpath = os.path.join(self.__files_dir, filename)
        await self.__send_response(writer, self.__create_byte_data('GET', str(os.path.getsize(fullpath))))
        with open(fullpath, 'rb') as f:
            while chunk := f.read(1024):
                await self.__send_response(writer, chunk)

    async def __put_file(self, reader: StreamReader, writer: StreamWriter, filename: str, filesize: int,
                         act: str) -> None:
        mode = 'wb'
        if self.__check_filename(filename) and act == 'ADD':
            mode = 'ab'

        bytes_received = 0
        try:
            with open(os.path.join(self.__files_dir, f"{filename}"), mode) as f:
                while bytes_received < filesize:
                    chunk = await reader.read(min(1024, filesize - bytes_received))

                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
        except Exception as e:
            await self.__send_response(writer, self.__create_byte_data('ERROR', 'No data'))
            return

        await self.__send_response(writer, self.__create_byte_data('SUCCESS'))

    async def __del_file(self, filename: str, writer: StreamWriter) -> None:
        if self.__check_filename(filename):
            os.remove(os.path.join(files_dir, filename))
            await self.__send_response(writer, self.__create_byte_data('SUCCESS'))
        else:
            await self.__send_response(writer, self.__create_byte_data('ERROR', 'File not exists'))


async def main():
    server = Server(host, port, files_dir)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
