from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mem0.configs.dbs.base import BaseDBConfig


class DBBase(ABC):
    """Initialized a base database class

    :param config: Database configuration option class, defaults to None
    :type config: Optional[BaseDBConfig], optional
    """

    def __init__(self, config: Optional[BaseDBConfig] = None):
        if config is None:
            self.config = BaseDBConfig()
        else:
            self.config = config

    @abstractmethod
    def add_history(
        self,
        memory_id: str,
        old_memory: Optional[str],
        new_memory: Optional[str],
        event: str,
        *,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        is_deleted: int = 0,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        """Add a history record to the database.
        
        :param memory_id: The ID of the memory being tracked
        :param old_memory: The previous memory content
        :param new_memory: The new memory content
        :param event: The type of event that occurred
        :param created_at: When the record was created
        :param updated_at: When the record was last updated
        :param is_deleted: Whether the record is deleted (0 or 1)
        :param actor_id: ID of the actor who made the change
        :param role: Role of the actor
        """
        pass

    @abstractmethod
    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Retrieve history records for a given memory ID.
        
        :param memory_id: The ID of the memory to get history for
        :return: List of history records as dictionaries
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset/clear all data in the database."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection and clean up resources."""
        pass

    def __del__(self):
        self.close()
