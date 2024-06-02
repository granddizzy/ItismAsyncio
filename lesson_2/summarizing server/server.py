import multiprocessing
import time


def calculate_sum(start, end, results: multiprocessing.Array, worker_num: int):
    results[worker_num] = sum(range(start, end + 1))


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Время выполнения {end_time - start_time} секунд")
        return result

    return wrapper


@timer
def distribute(total_workers: int, num: int) -> int:
    chunk_size = num // total_workers + (1 if num % total_workers else 0)
    processes = []
    results = multiprocessing.Array('q', total_workers)
    end = 0
    for worker_num in range(total_workers):
        start = end + 1
        end = min(start + chunk_size - 1, num)
        process = multiprocessing.Process(target=calculate_sum, args=(start, end, results, worker_num))
        processes.append(process)
        process.start()
    for process in processes:
        process.join()

    return sum(results)


def start_server():
    # server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_socket.bind(('localhost', 8020))
    # server_socket.listen(5)
    #
    # print('Сервер запущен...')
    #
    # while True:
    #     client_socket, client_address = server_socket.accept()
    #     print(f'Получено подключение от {client_address}')

    # client_thread = threading.Thread(target=handle, args=())
    # client_thread.start()
    workers = multiprocessing.cpu_count()
    result = distribute(workers, 1_000_000_000)

    print(result)


if __name__ == '__main__':
    start_server()
