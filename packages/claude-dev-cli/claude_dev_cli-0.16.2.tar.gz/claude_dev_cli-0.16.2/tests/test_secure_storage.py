"""Tests for secure storage module."""

import os
from pathlib import Path

import pytest

from claude_dev_cli.secure_storage import SecureStorage


class TestSecureStorage:
    """Tests for SecureStorage class."""
    
    def test_initialization(self, tmp_path: Path) -> None:
        """Test SecureStorage initialization."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        assert storage.config_dir == tmp_path
        assert storage.encrypted_file == tmp_path / "keys.enc"
        assert storage.key_file == tmp_path / ".keyfile"
        assert storage.use_keyring is False  # Forced to encrypted file
    
    def test_force_encrypted_file(self, tmp_path: Path) -> None:
        """Test force_encrypted_file parameter."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        assert storage.use_keyring is False
        assert storage.get_storage_method() == "encrypted_file"
    
    def test_encryption_key_created(self, tmp_path: Path) -> None:
        """Test that encryption key is created."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        assert storage.key_file.exists()
        key = storage.key_file.read_bytes()
        assert len(key) > 0
    
    def test_store_and_retrieve_key(self, tmp_path: Path) -> None:
        """Test storing and retrieving a key."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        storage.store_key("test", "sk-ant-test-key-123")
        retrieved = storage.get_key("test")
        
        assert retrieved == "sk-ant-test-key-123"
    
    def test_get_nonexistent_key(self, tmp_path: Path) -> None:
        """Test retrieving a key that doesn't exist."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        retrieved = storage.get_key("nonexistent")
        assert retrieved is None
    
    def test_delete_key(self, tmp_path: Path) -> None:
        """Test deleting a key."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        storage.store_key("test", "sk-ant-test-key")
        assert storage.get_key("test") == "sk-ant-test-key"
        
        result = storage.delete_key("test")
        assert result is True
        assert storage.get_key("test") is None
    
    def test_delete_nonexistent_key(self, tmp_path: Path) -> None:
        """Test deleting a key that doesn't exist."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        result = storage.delete_key("nonexistent")
        assert result is False
    
    def test_list_keys(self, tmp_path: Path) -> None:
        """Test listing all stored keys."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        storage.store_key("key1", "value1")
        storage.store_key("key2", "value2")
        storage.store_key("key3", "value3")
        
        keys = storage.list_keys()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
    
    def test_list_keys_empty(self, tmp_path: Path) -> None:
        """Test listing keys when none exist."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        keys = storage.list_keys()
        assert keys == []
    
    def test_update_key(self, tmp_path: Path) -> None:
        """Test updating an existing key."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        storage.store_key("test", "old-value")
        assert storage.get_key("test") == "old-value"
        
        storage.store_key("test", "new-value")
        assert storage.get_key("test") == "new-value"
    
    def test_multiple_keys(self, tmp_path: Path) -> None:
        """Test storing multiple keys."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        keys_data = {
            "personal": "sk-ant-personal-key",
            "client": "sk-ant-client-key",
            "work": "sk-ant-work-key"
        }
        
        for name, key in keys_data.items():
            storage.store_key(name, key)
        
        for name, expected_key in keys_data.items():
            assert storage.get_key(name) == expected_key
    
    def test_migrate_from_plaintext(self, tmp_path: Path) -> None:
        """Test migrating plaintext keys."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        plaintext_keys = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        count = storage.migrate_from_plaintext(plaintext_keys)
        assert count == 3
        
        for name, value in plaintext_keys.items():
            assert storage.get_key(name) == value
    
    def test_file_permissions(self, tmp_path: Path) -> None:
        """Test that encrypted file has secure permissions (Unix)."""
        if not hasattr(os, 'chmod'):
            pytest.skip("chmod not available on this platform")
        
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        storage.store_key("test", "value")
        
        # Check key file permissions (should be 0o600)
        key_stat = storage.key_file.stat()
        assert key_stat.st_mode & 0o777 == 0o600
        
        # Check encrypted file permissions
        enc_stat = storage.encrypted_file.stat()
        assert enc_stat.st_mode & 0o777 == 0o600
    
    def test_encrypted_file_persistence(self, tmp_path: Path) -> None:
        """Test that keys persist across storage instances."""
        # Store keys with first instance
        storage1 = SecureStorage(tmp_path, force_encrypted_file=True)
        storage1.store_key("persistent", "test-value")
        
        # Retrieve with second instance
        storage2 = SecureStorage(tmp_path, force_encrypted_file=True)
        retrieved = storage2.get_key("persistent")
        
        assert retrieved == "test-value"
    
    def test_corrupted_encrypted_file(self, tmp_path: Path) -> None:
        """Test handling of corrupted encrypted file."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        storage.store_key("test", "value")
        
        # Corrupt the encrypted file
        storage.encrypted_file.write_text("corrupted data")
        
        # Should handle gracefully and return empty dict
        keys = storage.list_keys()
        assert keys == []
    
    def test_test_environment_detection(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that test environment is properly detected."""
        # Set pytest env var
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_secure_storage.py::test")
        
        storage = SecureStorage(tmp_path, force_encrypted_file=False)
        assert storage.use_keyring is False
    
    def test_testing_env_var(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test TESTING environment variable detection."""
        monkeypatch.setenv("TESTING", "1")
        
        storage = SecureStorage(tmp_path, force_encrypted_file=False)
        assert storage.use_keyring is False
    
    def test_storage_method_reporting(self, tmp_path: Path) -> None:
        """Test get_storage_method returns correct value."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        method = storage.get_storage_method()
        assert method == "encrypted_file"
    
    def test_empty_key_value(self, tmp_path: Path) -> None:
        """Test storing empty string as key value."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        storage.store_key("empty", "")
        retrieved = storage.get_key("empty")
        
        assert retrieved == ""
    
    def test_special_characters_in_key_name(self, tmp_path: Path) -> None:
        """Test key names with special characters."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        special_names = ["key-with-dash", "key_with_underscore", "key.with.dots"]
        
        for name in special_names:
            storage.store_key(name, f"value-for-{name}")
            assert storage.get_key(name) == f"value-for-{name}"
    
    def test_long_key_value(self, tmp_path: Path) -> None:
        """Test storing very long key values."""
        storage = SecureStorage(tmp_path, force_encrypted_file=True)
        
        long_value = "x" * 10000
        storage.store_key("long", long_value)
        
        retrieved = storage.get_key("long")
        assert retrieved == long_value
        assert len(retrieved) == 10000
