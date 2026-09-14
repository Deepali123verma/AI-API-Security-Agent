from abc import ABC, abstractmethod

from app.scanner.models import ScanContext, ScannerFinding


class BaseScanner(ABC):
    name: str

    @abstractmethod
    def scan(self, context: ScanContext) -> list[ScannerFinding]:
        raise NotImplementedError
