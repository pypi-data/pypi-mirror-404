"""langchain-encrypted-mongo-memory - Encrypted chat history for LangChain.

A LangChain-compatible MongoDB chat message history with AES-128 encryption.
"""
from .EncryptedMongoChatMemory import EncryptedMongoDBChatMessageHistory

__version__ = "0.1.0"
__all__ = ["EncryptedMongoDBChatMessageHistory"]
