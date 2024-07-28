import asyncio


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def send_command(self, command: str):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        print(f'Send: {command}')
        writer.write(command.upper().encode())
        await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def start(self):
        while True:
            command = input()
            if command == "QUIT":
                break
            await self.send_command(command)


if __name__ == "__main__":
    host = '127.0.0.1'
    port = 8021
    client = Client(host, port)

    asyncio.run(client.start())
