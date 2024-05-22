import socket
import sys

host = '127.0.0.1'
port = 8020


def start_client():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))

            print('Подключение установлено')

            while True:
                show_main_menu()
                choice = input_choice(4)

                if choice == 0:
                    print("До свидания!!!")
                    sys.exit()
                elif choice == 1:
                    show_file_list(get_file_list(client_socket))
                elif choice == 2:
                    send_file(input_path_file())
                elif choice == 3:
                    del_file(input_filename())
    except Exception as e:
        print(f"An error occurred: {e}")


def show_main_menu() -> None:
    print('Выберите вариант:')
    print('0.Выйти')
    print('1.Получить список файлов')
    print('2.Добавить файл')
    print('3.Удалить файл')


def input_choice(max_choice_num: int) -> int | None:
    while True:
        answer = input("Сделайте выбор:")
        if answer.isdigit() and 0 <= int(answer) <= max_choice_num:
            return int(answer)


def input_path_file() -> str:
    path = input("Введите путь к файлу:")
    return path


def input_filename() -> str:
    filename = input("Введите имя файла:")
    return filename


def get_file_list(client_socket) -> list:
    files_list = []

    data = "0"
    client_socket.send(data.encode('utf-8'))

    data = client_socket.recv(1024).decode('utf-8')
    while data:
        if 'END_OF_LIST' in data:
            # print(data.replace('END_OF_LIST', '').strip())
            break
        files_list.append(data.strip())
        data = client_socket.recv(1024).decode('utf-8')

    return files_list


def show_file_list(files: list) -> None:
    if files:
        print("\n" + "=" * 83)
        for filename in files:
            print(filename)

        print("=" * 83 + "\n")
    else:
        print("Файлов нет")


def send_file(path: str) -> None:
    pass


def del_file(filename: str) -> None:
    pass


if __name__ == "__main__":
    start_client()
