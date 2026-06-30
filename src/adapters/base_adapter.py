from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseAdapter(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Reads the input file and parses it into a list of generic key-value dictionaries.
        """
        pass