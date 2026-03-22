from abc import ABC, abstractmethod
from typing import Any

from aisuite import Client

from config import settings


class Agent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.model = settings.model
        self.client = Client()

    @abstractmethod
    def run(self, task: str, history=None) -> Any:
        pass
