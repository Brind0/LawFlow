from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
import sqlite3

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection
        # Ensure row factory is set to Row if not already
        if self.conn.row_factory != sqlite3.Row:
            self.conn.row_factory = sqlite3.Row
    
    @abstractmethod
    def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        pass
