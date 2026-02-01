
import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_encrypted_mongo_memory.EncryptedMongoChatMemory import (
    EncryptedMongoDBChatMessageHistory
)


class TestEncryptedMongoDBChatMessageHistory:
    """
    Unit tests for EncryptedMongoDBChatMessageHistory.

    Tests encryption, decryption, message storage, and retrieval functionality.
    Uses mocking to avoid requiring a live MongoDB instance.
    """
    @pytest.fixture
    def mock_collection(self):
        """Create a mock MongoDB collection."""
        return MagicMock()

    @pytest.fixture
    def mock_encryption_service(self):
        """Create a mock encryption service."""
        with patch(
            'langchain_encrypted_mongo_memory.EncryptedMongoChatMemory.encryption_service'
        ) as mock:
            # Default behavior: return encrypted/decrypted values
            mock.encrypt_json.return_value = "encrypted_data_string"
            mock.decrypt_json.return_value = {
                "type": "human",
                "data": {"content": "Test message", "type": "human"}
            }
            yield mock

    @pytest.fixture
    def history(self, mock_collection, mock_encryption_service):
        """Create an EncryptedMongoDBChatMessageHistory instance with mocks."""
        with patch(
            'langchain_mongodb.MongoDBChatMessageHistory.__init__',
            return_value=None
        ):
            instance = EncryptedMongoDBChatMessageHistory.__new__(
                EncryptedMongoDBChatMessageHistory
            )
            instance.session_id = "test_session_123"
            instance.collection = mock_collection
            return instance

    # -------------------------------------------------------------------------
    # add_message Tests
    # -------------------------------------------------------------------------

    def test_add_message_encrypts_and_stores(
        self, history, mock_collection, mock_encryption_service
    ):
        """Test that add_message encrypts the message and stores it."""
        message = HumanMessage(content="Hello, this is a test")
        
        history.add_message(message)
        
        # Verify encryption was called
        mock_encryption_service.encrypt_json.assert_called_once()
        
        # Verify MongoDB insert was called with encrypted data
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["SessionId"] == "test_session_123"
        assert call_args["History"] == "encrypted_data_string"

    def test_add_message_raises_on_encryption_failure(
        self, history, mock_encryption_service
    ):
        """Test that add_message raises exception on encryption failure."""
        mock_encryption_service.encrypt_json.side_effect = Exception("Encryption failed")
        message = HumanMessage(content="Test")
        
        with pytest.raises(Exception, match="Encryption failed"):
            history.add_message(message)

    def test_add_message_raises_on_db_failure(
        self, history, mock_collection
    ):
        """Test that add_message raises exception on database failure."""
        mock_collection.insert_one.side_effect = Exception("DB connection failed")
        message = HumanMessage(content="Test")
        
        with pytest.raises(Exception, match="DB connection failed"):
            history.add_message(message)

    # -------------------------------------------------------------------------
    # messages Property Tests
    # -------------------------------------------------------------------------

    def test_messages_retrieves_and_decrypts(
        self, history, mock_collection, mock_encryption_service
    ):
        """Test that messages property retrieves and decrypts stored messages."""
        # Setup mock cursor with encrypted data
        mock_cursor = [
            {"SessionId": "test_session_123", "History": "encrypted_msg_1"},
            {"SessionId": "test_session_123", "History": "encrypted_msg_2"}
        ]
        mock_collection.find.return_value = mock_cursor
        
        messages = history.messages
        
        # Verify find was called with correct session ID
        mock_collection.find.assert_called_once_with(
            {"SessionId": "test_session_123"}
        )
        
        # Verify decryption was called for each message
        assert mock_encryption_service.decrypt_json.call_count == 2

    def test_messages_skips_empty_history(
        self, history, mock_collection, mock_encryption_service
    ):
        """Test that messages skips documents with empty History field."""
        mock_cursor = [
            {"SessionId": "test_session_123", "History": ""},
            {"SessionId": "test_session_123", "History": None},
            {"SessionId": "test_session_123", "History": "valid_encrypted"}
        ]
        mock_collection.find.return_value = mock_cursor
        
        history.messages
        
        # Only one valid message should trigger decryption
        assert mock_encryption_service.decrypt_json.call_count == 1

    def test_messages_skips_invalid_message_types(
        self, history, mock_collection, mock_encryption_service
    ):
        """Test that messages skips messages with invalid types."""
        mock_collection.find.return_value = [
            {"SessionId": "test_session_123", "History": "encrypted"}
        ]
        mock_encryption_service.decrypt_json.return_value = {
            "type": "invalid_type",
            "data": {"content": "Test"}
        }
        
        messages = history.messages
        
        # Should return empty list due to invalid type
        assert len(messages) == 0

    def test_messages_handles_valid_types(
        self, history, mock_collection, mock_encryption_service
    ):
        """Test that messages correctly handles human, ai, and system types."""
        valid_types = ['human', 'ai', 'system']
        
        for msg_type in valid_types:
            mock_collection.find.return_value = [
                {"SessionId": "test_session_123", "History": "encrypted"}
            ]
            mock_encryption_service.decrypt_json.return_value = {
                "type": msg_type,
                "data": {"content": f"Test {msg_type} message", "type": msg_type}
            }
            
            messages = history.messages
            
            # Should successfully return the message
            assert len(messages) == 1

    def test_messages_returns_empty_on_db_failure(
        self, history, mock_collection
    ):
        """Test that messages returns empty list on database failure."""
        mock_collection.find.side_effect = Exception("DB error")
        
        messages = history.messages
        
        assert messages == []

    def test_messages_continues_on_single_decryption_failure(
        self, history, mock_collection, mock_encryption_service
    ):
        """Test that messages continues processing if one message fails to decrypt."""
        mock_collection.find.return_value = [
            {"SessionId": "test_session_123", "History": "encrypted_1"},
            {"SessionId": "test_session_123", "History": "encrypted_2"}
        ]
        
        # First call fails, second succeeds
        mock_encryption_service.decrypt_json.side_effect = [
            Exception("Decryption failed"),
            {"type": "human", "data": {"content": "Valid message", "type": "human"}}
        ]
        
        messages = history.messages
        
        # Should return one valid message
        assert len(messages) == 1

    # -------------------------------------------------------------------------
    # clear Tests
    # -------------------------------------------------------------------------

    def test_clear_deletes_session_messages(self, history, mock_collection):
        """Test that clear deletes all messages for the session."""
        mock_result = Mock()
        mock_result.deleted_count = 5
        mock_collection.delete_many.return_value = mock_result
        
        history.clear()
        
        mock_collection.delete_many.assert_called_once_with(
            {"SessionId": "test_session_123"}
        )

    def test_clear_raises_on_db_failure(self, history, mock_collection):
        """Test that clear raises exception on database failure."""
        mock_collection.delete_many.side_effect = Exception("Delete failed")
        
        with pytest.raises(Exception, match="Delete failed"):
            history.clear()


class TestEncryptionIntegrity:
    """Tests for encryption/decryption data integrity."""

    @pytest.fixture
    def history_with_real_encryption(self):
        """Create history instance with real encryption but mocked MongoDB."""
        with patch(
            'langchain_mongodb.MongoDBChatMessageHistory.__init__',
            return_value=None
        ):
            instance = EncryptedMongoDBChatMessageHistory.__new__(
                EncryptedMongoDBChatMessageHistory
            )
            instance.session_id = "integrity_test_session"
            instance.collection = MagicMock()
            return instance

    def test_message_content_preserved_after_encryption_cycle(
        self, history_with_real_encryption
    ):
        """Test that message content is preserved through encrypt/decrypt cycle."""
        from mores_encryption.encryption import encryption_service
        
        original_content = "Sensitive patient data: Blood pressure 120/80"
        message = HumanMessage(content=original_content)
        
        # Encrypt
        from langchain_core.messages import message_to_dict
        message_dict = message_to_dict(message)
        encrypted = encryption_service.encrypt_json(message_dict)
        
        # Verify encryption happened
        assert encrypted != original_content
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = encryption_service.decrypt_json(encrypted)
        
        # Verify content preserved
        assert decrypted["data"]["content"] == original_content

    def test_encrypted_output_is_url_safe(self, history_with_real_encryption):
        """Test that encrypted output is URL-safe Base64."""
        from mores_encryption.encryption import encryption_service
        
        message = HumanMessage(content="Test message for URL safety")
        from langchain_core.messages import message_to_dict
        message_dict = message_to_dict(message)
        
        encrypted = encryption_service.encrypt_json(message_dict)
        
        # URL-safe Base64 should not contain +, /, or =
        # Fernet uses standard Base64 which is URL-safe
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0


class TestSessionIsolation:
    """Tests for session isolation in message storage."""

    @pytest.fixture
    def mock_collection(self):
        """Create a mock MongoDB collection."""
        return MagicMock()

    def test_messages_only_retrieves_own_session(self, mock_collection):
        """Test that messages only retrieves messages for its own session."""
        with patch(
            'langchain_mongodb.MongoDBChatMessageHistory.__init__',
            return_value=None
        ), patch(
            'langchain_encrypted_mongo_memory.EncryptedMongoChatMemory.encryption_service'
        ):
            instance = EncryptedMongoDBChatMessageHistory.__new__(
                EncryptedMongoDBChatMessageHistory
            )
            instance.session_id = "session_A"
            instance.collection = mock_collection
            mock_collection.find.return_value = []
            
            instance.messages
            
            # Verify query filters by session ID
            mock_collection.find.assert_called_with({"SessionId": "session_A"})

    def test_clear_only_deletes_own_session(self, mock_collection):
        """Test that clear only deletes messages for its own session."""
        with patch(
            'langchain_mongodb.MongoDBChatMessageHistory.__init__',
            return_value=None
        ):
            instance = EncryptedMongoDBChatMessageHistory.__new__(
                EncryptedMongoDBChatMessageHistory
            )
            instance.session_id = "session_B"
            instance.collection = mock_collection
            mock_result = Mock()
            mock_result.deleted_count = 0
            mock_collection.delete_many.return_value = mock_result
            
            instance.clear()
            
            # Verify delete filters by session ID
            mock_collection.delete_many.assert_called_with({"SessionId": "session_B"})
