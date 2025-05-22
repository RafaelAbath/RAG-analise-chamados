from abc import ABC, abstractmethod
from typing import Optional
from core.models import Chamado

class Router(ABC):
    def __init__(self, successor: Optional['Router'] = None):
        self._successor = successor

    def handle(self, chamado: Chamado) -> Optional[str]:
        result = self._route(chamado)
        if result:
            return result
        if self._successor:
            return self._successor.handle(chamado)
        return None

    @abstractmethod
    def _route(self, chamado: Chamado) -> Optional[str]:
        ...