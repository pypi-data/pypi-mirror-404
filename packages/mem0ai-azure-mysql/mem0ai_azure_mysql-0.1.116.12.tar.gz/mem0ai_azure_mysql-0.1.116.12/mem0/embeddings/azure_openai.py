import os
from typing import Literal, Optional

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from mem0.configs.embeddings.base import BaseEmbedderConfig
from mem0.embeddings.base import EmbeddingBase
from mem0.memory.utils import time_perf


class AzureOpenAIEmbedding(EmbeddingBase):

    cached_embeddings = {}

    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        super().__init__(config)

        api_key = self.config.azure_kwargs.api_key or os.getenv("EMBEDDING_AZURE_API_KEY")
        azure_ad_token = self.config.azure_kwargs.azure_ad_token or os.getenv("EMBEDDING_AZURE_AD_TOKEN")
        azure_deployment = self.config.azure_kwargs.azure_deployment or os.getenv("EMBEDDING_AZURE_DEPLOYMENT")
        azure_endpoint = self.config.azure_kwargs.azure_endpoint or os.getenv("EMBEDDING_AZURE_ENDPOINT")
        api_version = self.config.azure_kwargs.api_version or os.getenv("EMBEDDING_AZURE_API_VERSION")
        default_headers = self.config.azure_kwargs.default_headers

        if azure_endpoint is None:
            raise ValueError("Azure endpoint must be provided either in config or as an environment variable.")

        auth_kwargs = {}
        if api_key:
            auth_kwargs["api_key"] = api_key
        elif azure_ad_token:
            auth_kwargs["azure_ad_token"] = azure_ad_token
        else:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
            auth_kwargs["azure_ad_token_provider"] = token_provider

        self.client = AzureOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            http_client=self.config.http_client,
            default_headers=default_headers,
            **auth_kwargs,
        )

    @time_perf
    def embed(self, text, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        Get the embedding for the given text using OpenAI.

        Args:
            text (str): The text to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: The embedding vector.
        """
        text = text.replace("\n", " ")
        if text not in self.cached_embeddings:
            self.cached_embeddings[text] = self.client.embeddings.create(input=[text], model=self.config.model).data[0].embedding
        return self.cached_embeddings[text]

    @time_perf
    def embed_in_batch(self, texts, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        Get the embedding for the given texts.

        Args:
            texts (list[str]): The text list to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: List of the embedding vector.
        """
        texts = [text.replace("\n", " ") for text in texts]

        # Use cached embeddings if available
        uncached_texts = [text for text in texts if text not in self.cached_embeddings]
        if uncached_texts:
            uncached_embeddings = self.client.embeddings.create(input=uncached_texts, model=self.config.model)
            for text, item in zip(uncached_texts, uncached_embeddings.data):
                self.cached_embeddings[text] = item.embedding

        return [self.cached_embeddings[text] for text in texts]
