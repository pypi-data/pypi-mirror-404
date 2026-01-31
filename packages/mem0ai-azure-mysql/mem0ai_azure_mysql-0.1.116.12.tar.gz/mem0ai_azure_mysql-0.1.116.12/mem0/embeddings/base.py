from abc import ABC, abstractmethod
from typing import Literal, Optional

from mem0.configs.embeddings.base import BaseEmbedderConfig


class EmbeddingBase(ABC):
    """Initialized a base embedding class

    :param config: Embedding configuration option class, defaults to None
    :type config: Optional[BaseEmbedderConfig], optional
    """

    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        if config is None:
            self.config = BaseEmbedderConfig()
        else:
            self.config = config

    @abstractmethod
    def embed(self, text, memory_action: Optional[Literal["add", "search", "update"]]) -> list[float]:
        """
        Get the embedding for the given text.

        Args:
            text (str): The text to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: The embedding vector.
        """
        pass

    def embed_in_batch(self, texts, memory_action: Optional[Literal["add", "search", "update"]]) -> list[list[float]]:
        """
        Get the embedding for the given texts.

        Args:
            texts (list[str]): The text list to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: List of the embedding vector.
        """
        return [self.embed(text, memory_action) for text in texts]
