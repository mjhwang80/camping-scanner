from abc import ABC, abstractmethod

class CampingMonitor(ABC):
    @abstractmethod
    async def check_availability(self, params: dict) -> bool:
        """
        params: Java의 Map 구조로, 
        {'camp_id': '123', 'date': '2024-05-20', 'site_codes': ['A1', 'A2']} 형태
        """
        pass