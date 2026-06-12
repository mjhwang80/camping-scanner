#app/platforms/base.py
from abc import ABC, abstractmethod

class CampingMonitor(ABC):
    
    def __init__(self):
        self.params = {}

    @abstractmethod
    async def check_availability(self, params: dict) -> bool:
        pass

    @abstractmethod
    async def close_client(self):
        """네트워크 리소스를 정리하는 공통 인터페이스"""
        pass