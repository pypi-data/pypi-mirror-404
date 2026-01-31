# Mem0 - Azure Enhanced Fork

This repository is an enhanced fork of [mem0ai/mem0](https://github.com/mem0ai/mem0.git) that provides enterprise-grade improvements for Azure environments and production deployments.

## 🚀 Key Enhancements

### 1. Azure Entra ID Authentication
- **Azure AI Search**: Support for Azure Entra ID (Azure AD) authentication using [`DefaultAzureCredential`](mem0/vector_stores/azure_ai_search.py:114)
- **Azure OpenAI**: Seamless Entra ID integration for both LLM and embedding services using [`DefaultAzureCredential`](mem0/llms/azure_openai.py:37)
- **Simplified Authentication**: No need to manage API keys when using managed identities or service principals

### 2. MySQL Database Support
- **Production-Ready**: Replace SQLite3 with enterprise-grade [`MySQL`](mem0/dbs/mysql.py:18) for scalable memory history storage
- **Connection Pooling**: Built-in connection pooling and SSL support for secure connections
- **Migration Support**: Automatic schema migration from existing SQLite databases
- **Thread-Safe**: Thread-safe operations with proper connection management

## 📦 Installation

Install the enhanced package with Azure and MySQL dependencies:

```bash
pip install mem0ai-azure-mysql
```
