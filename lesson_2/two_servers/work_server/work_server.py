import multiprocessing
import re
import threading
import time

import select
import socket

host = '127.0.0.1'
port = 8021
token_host = '127.0.0.1'
token_port = 8022


class Server:
    def __init__(self, host: str, port: int, token_host: str, token_port: int):
        self.host = host
        self.port = port
        self.__sockets_list = []
        self.__token_socket = None
        self.tokenserver_host = token_host
        self.tokenserver_port = token_port
        self.__cashed_tokens = {}

    def __disconnect(self, client_socket):
        self.__sockets_list.remove(client_socket)
        if client_socket != self.__token_socket:
            print(f"Disconnected {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
        else:
            print(f"Disconnected token server socket{client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
        client_socket.close()

        # cache clearing
        to_del = []
        for k, v in self.__cashed_tokens.items():
            if v['socket'] == client_socket:
                to_del.append(k)
        for k in to_del:
            self.__cashed_tokens.pop(k)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen()
            print(f"Work server is listening on {host}:{port}")
            self.__sockets_list = [server_socket]
            self.__set_connection_to_tokenserver()
            while True:
                read_sockets, _, error_sockets = select.select(self.__sockets_list, [],
                                                               self.__sockets_list)

                for notified_socket in read_sockets:
                    try:
                        if notified_socket == server_socket:
                            client_socket, _ = server_socket.accept()
                            self.__sockets_list.append(client_socket)
                        elif notified_socket == self.__token_socket:
                            if (response := self.__get_data(notified_socket)) and response.startswith('CHECK'):
                                # _, token, client_id = request.split('\n', 2)
                                _, token, client_id = re.split(r'\s*\n\s*', response)
                                if client_id and (token_cashed_data := self.__cashed_tokens.get(token)):
                                    self.__cashed_tokens[token]['client_id'] = client_id
                                    thread = threading.Thread(target=self.__do_work,
                                                              args=(
                                                                  token_cashed_data['socket'],
                                                                  token_cashed_data['request']))
                                    thread.start()
                                else:
                                    self.__send_data(token_cashed_data['socket'],
                                                     self.__create_byte_header('ERROR', 'Token not valid'))
                        else:
                            if (request := self.__get_data(notified_socket)) and request.startswith('GET'):
                                _, token = request.split('\n', 1)
                                if (
                                        token_cashed_data := self.__cashed_tokens.get(
                                            token)) and token_cashed_data['client_id']:
                                    thread = threading.Thread(target=self.__do_work,
                                                              args=(
                                                                  token_cashed_data['socket'],
                                                                  token_cashed_data['request']))
                                    thread.start()
                                else:
                                    self.__cashed_tokens[token] = {'socket': notified_socket, 'client_id': 0,
                                                                   'request': request}
                                    self.__send_data(self.__token_socket, self.__create_byte_header('CHECK', token))
                            elif request.startswith('TEST'):
                                self.__send_data(notified_socket, self.__create_byte_header('TEST_SUCCESS'))
                    except Exception as e:
                        print(e)
                        self.__disconnect(notified_socket)
                        if notified_socket == self.__token_socket:
                            self.__set_connection_to_tokenserver()

                for notified_socket in error_sockets:
                    print(f"Error socket {notified_socket}")

    def __do_work(self, client_socket: socket.socket, request: str) -> None:
        try:
            time.sleep(1)
            self.__send_data(client_socket, self.__create_byte_header('GET', '42'))
        except:
            self.__disconnect(client_socket)

    def __set_connection_to_tokenserver(self) -> None:
        try:
            self.__token_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.token_socket.settimeout(5)
            self.__token_socket.connect((self.tokenserver_host, self.tokenserver_port))
            self.__sockets_list.append(self.__token_socket)
            print(f"Token server connected to {self.tokenserver_host}:{self.tokenserver_port}")
        except Exception as e:
            print(f"Token server not connected: {e}")

    def __get_data(self, used_socket) -> str | None:
        # return used_socket.recv(512).decode('utf-8').strip()
        return used_socket.recv(512).decode('utf-8').strip()

    def __send_data(self, used_socket, data: bin) -> None:
        used_socket.sendall(data)

    def __create_byte_header(self, *args: str) -> bin:
        return '\n'.join(args).encode('utf-8').ljust(512, b' ')


if __name__ == "__main__":
    server = Server(host, port, token_host, token_port)
    server.start()
