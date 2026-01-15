from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseProcessor(ABC):
    """Base class for all document processors."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """Parse the document and return structured data."""
        pass
    
    @abstractmethod
    def extract_tables(self) -> List[List[Dict]]:
        """Extract tables from the document."""
        pass
    
    @abstractmethod
    def extract_text(self) -> str:
        """Extract raw text from the document."""
        pass
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get metadata about the document."""
        return {
            "file_path": self.file_path,
            "processor": self.__class__.__name__
        }
