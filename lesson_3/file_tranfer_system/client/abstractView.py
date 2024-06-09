import re
from configparser import NoOptionError
from datetime import datetime
import aioconsole

from lesson_3.file_tranfer_system.client.model import ClientError
import abc
from abc import ABC, abstractmethod

forbidden_chars = r'[\\/:"*?<>|]'


class View:
    @abstractmethod
    async def show_main_menu(self) -> int:
        pass

    @abstractmethod
    async def show_fileexists_menu(self) -> int:
        pass

    @abstractmethod
    async def input_choice(self, max_choice_num: int) -> int | None:
        pass

    @abstractmethod
    async def input_local_path_file(self) -> str:
        pass

    @abstractmethod
    async def input_filename(self) -> str:
        pass

    @abstractmethod
    def show_file_list(self, files: list) -> None:
        pass

    @abstractmethod
    def show_error(self, error: ClientError) -> None:
        pass

    @abstractmethod
    def show_message(self, msg) -> None:
        pass

    @abstractmethod
    async def input_mode_fileexists(self) -> str:
        pass
