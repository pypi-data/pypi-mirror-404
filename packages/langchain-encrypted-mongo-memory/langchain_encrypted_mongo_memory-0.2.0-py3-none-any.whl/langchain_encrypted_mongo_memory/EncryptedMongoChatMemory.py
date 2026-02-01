import logging
from typing import List
from langchain_mongodb import MongoDBChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, message_to_dict
from mores_encryption.encryption import encryption_service

logger = logging.getLogger(__name__)


class EncryptedMongoDBChatMessageHistory(MongoDBChatMessageHistory):
    """
    Encrypted MongoDB Chat Message History for Long-Term Memory.
    
    Encrypts messages before storing and decrypts upon retrieval using
    mores-encryption (AES-128 Fernet encryption).
    
    Features:
        - Automatic encryption/decryption of all message content
        - URL-safe Base64 encoded output
        - Secure key management via environment variables
        - Compatible with any LangChain memory integration
    
    Use Case:
        - Store conversation history with end-to-end encryption
        - Secure storage of sensitive chat data (PII, medical, financial)
        - Compliance with data protection requirements (HIPAA, GDPR)
        - Permanent storage (no TTL like Redis)
    
    Usage:
        from langchain_encrypted_mongo_memory import EncryptedMongoDBChatMessageHistory
        
        history = EncryptedMongoDBChatMessageHistory(
            connection_string="mongodb://localhost:27017",
            database_name="myapp",
            collection_name="chat_history",
            session_id="user_123:session_456"
        )
        
        # Add encrypted messages
        history.add_user_message("Sensitive information here")
        
        # Retrieve decrypted messages
        messages = history.messages
    
    Environment Variables:
        ENCRYPTION_KEY: Base64-encoded 32-byte Fernet key (auto-generated if missing)
    """

    def add_message(self, message: BaseMessage) -> None:
        """Encrypt and store message in MongoDB."""
        try:
            # Convert message to dict
            message_dict = message_to_dict(message)
            
            # Encrypt the entire message dictionary
            encrypted_data = encryption_service.encrypt_json(message_dict)
            
            # Store encrypted string in MongoDB
            self.collection.insert_one({
                "SessionId": self.session_id,
                "History": encrypted_data
            })
            
            logger.debug(f"Message stored for session: {self.session_id[:20]}...")
                   
        except Exception as e:
            logger.error(f"Failed to add encrypted message: {e}")
            raise

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve and decrypt messages from MongoDB."""
        try:
            cursor = self.collection.find({"SessionId": self.session_id})
            items = []
            allowed_types = ['human', 'ai', 'system']
            
            for doc in cursor:
                try:
                    encrypted_data = doc.get("History", "")
                    
                    if not encrypted_data:
                        continue
                    
                    # Decrypt
                    decrypted_dict = encryption_service.decrypt_json(encrypted_data)
                    
                    if decrypted_dict and isinstance(decrypted_dict, dict):
                        # Validate message type
                        msg_type = decrypted_dict.get("type", "").lower()
                        if msg_type not in allowed_types:
                            logger.warning(f"Skipping invalid message type: {msg_type}")
                            continue
                        
                        items.append(decrypted_dict)
                    else:
                        logger.warning("Skipping un-decryptable message")
                               
                except Exception as inner_e:
                    logger.warning(f"Error processing history item: {inner_e}")
                    continue
            
            # Convert list of dicts back to BaseMessages
            return messages_from_dict(items)
            
        except Exception as e:
            logger.error(f"Failed to retrieve/decrypt messages: {e}")
            return []

    def clear(self) -> None:
        """Clear all messages for this session from MongoDB."""
        try:
            result = self.collection.delete_many({"SessionId": self.session_id})
            logger.debug(f"Cleared {result.deleted_count} messages for session: {self.session_id[:20]}...")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            raise
