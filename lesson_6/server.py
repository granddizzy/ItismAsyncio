import asyncio
import uuid

host = '127.0.0.1'
port = 8021


class TaskManager:
    def __init__(self):
        self.parent_tasks = []

    async def parent_task(self, parent_id: str, interval: int):
        child_tasks = []
        try:
            for i in range(10):
                task = asyncio.create_task(self.long_running_task(parent_id, i, interval))
                child_tasks.append(task)
            await asyncio.gather(*child_tasks)
        except asyncio.CancelledError:
            # for task in child_tasks:
            #     task.cancel()
            # await asyncio.gather(*child_tasks, return_exceptions=True)
            print(f"Parent task {parent_id} and its children were cancelled.")

    async def long_running_task(self, parent_id: str, child_id: int, interval: int):
        try:
            while True:
                await asyncio.sleep(interval)
                print(f"Parent task {parent_id}: Child task {child_id} is running.")
        except asyncio.CancelledError:
            print(f"Parent task {parent_id}: Child task {child_id} was cancelled.")

    async def start(self, interval: int):
        parent_id = str(uuid.uuid4())
        parent_task = asyncio.create_task(self.parent_task(parent_id, interval))
        self.parent_tasks.append(parent_task)
        print(f"Started parent task {parent_id}")

    async def stop(self):
        for task in self.parent_tasks:
            task.cancel()
        await asyncio.gather(*self.parent_tasks)
        self.parent_tasks.clear()
        print("All tasks were stopped.")


class Server:
    def __init__(self, host: str, port: int, task_manager: TaskManager):
        self.host = host
        self.port = port
        self.task_manager = task_manager

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")

        while True:
            data = await reader.read(100)
            message = data.decode().strip()
            if message == "START":
                await self.task_manager.start(5)
            elif message == "STOP":
                await self.task_manager.stop()
            elif not message:
                break

        print(f"Disconnected from {addr}")
        writer.close()
        await writer.wait_closed()

    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with server:
            await server.serve_forever()


async def main():
    task_manager = TaskManager()
    server = Server(host, port, task_manager)
    await server.start_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped manually.")
