"""
Repository modules for data access abstraction.

Provides repository implementations for database operations using the repository pattern.
"""

from repositories.base import BaseRepository
from repositories.user_repository import UserRepository
from repositories.document_repository import DocumentRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "DocumentRepository",
]
