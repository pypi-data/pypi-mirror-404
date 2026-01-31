"""Secure storage for API keys using system keyring.

Supports:
- macOS: Keychain
- Linux: Secret Service API (GNOME Keyring, KWallet)
- Windows: Windows Credential Locker

Falls back to encrypted file storage if keyring is unavailable.
"""

import json
import os
from pathlib import Path
from typing import Optional

try:
    import keyring
    from keyring.errors import KeyringError
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from cryptography.fernet import Fernet


class SecureStorage:
    """Secure storage for API keys with cross-platform support."""
    
    SERVICE_NAME = "claude-dev-cli"
    
    def __init__(self, config_dir: Path, force_encrypted_file: bool = False):
        """Initialize secure storage.
        
        Args:
            config_dir: Directory to store encrypted fallback files
            force_encrypted_file: Force use of encrypted file storage (for testing)
        """
        self.config_dir = config_dir
        self.encrypted_file = config_dir / "keys.enc"
        self.key_file = config_dir / ".keyfile"
        
        # Check if we should use keyring (disabled in test environments)
        # Detect test environment by checking for pytest or TESTING env var
        in_test = (
            force_encrypted_file or
            'pytest' in os.environ.get('_', '') or
            os.environ.get('PYTEST_CURRENT_TEST') is not None or
            os.environ.get('TESTING') == '1'
        )
        
        if in_test:
            # Always use encrypted file in tests to avoid Keychain prompts
            self.use_keyring = False
        else:
            # Check if keyring backend is available in production
            self.use_keyring = KEYRING_AVAILABLE and self._test_keyring()
        
        if not self.use_keyring:
            # Initialize fallback encryption
            self._ensure_encryption_key()
    
    def _test_keyring(self) -> bool:
        """Test if keyring backend is working.
        
        Returns:
            True if keyring is functional, False otherwise
        """
        try:
            # Try to get/set a test value
            test_key = f"{self.SERVICE_NAME}_test"
            keyring.set_password(self.SERVICE_NAME, test_key, "test")
            result = keyring.get_password(self.SERVICE_NAME, test_key)
            keyring.delete_password(self.SERVICE_NAME, test_key)
            return result == "test"
        except (KeyringError, Exception):
            return False
    
    def _ensure_encryption_key(self) -> None:
        """Ensure encryption key exists for fallback storage."""
        # Check if key_file path is a directory
        if self.key_file.exists() and self.key_file.is_dir():
            raise RuntimeError(
                f"Encryption key path {self.key_file} is a directory. "
                f"Please remove this directory."
            )
        
        if not self.key_file.exists():
            # Generate a new encryption key
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Secure the key file (Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(self.key_file, 0o600)
    
    def _get_cipher(self) -> Fernet:
        """Get Fernet cipher for fallback encryption."""
        if self.key_file.is_dir():
            raise RuntimeError(
                f"Encryption key path {self.key_file} is a directory. "
                f"Please remove this directory."
            )
        key = self.key_file.read_bytes()
        return Fernet(key)
    
    def _load_encrypted_keys(self) -> dict:
        """Load keys from encrypted fallback file."""
        if not self.encrypted_file.exists():
            return {}
        
        # Check if encrypted_file is a directory
        if self.encrypted_file.is_dir():
            raise RuntimeError(
                f"Encrypted keys file {self.encrypted_file} is a directory. "
                f"Please remove this directory."
            )
        
        try:
            cipher = self._get_cipher()
            encrypted_data = self.encrypted_file.read_bytes()
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception:
            # If decryption fails, return empty dict
            return {}
    
    def _save_encrypted_keys(self, keys: dict) -> None:
        """Save keys to encrypted fallback file."""
        # Check if encrypted_file is a directory
        if self.encrypted_file.exists() and self.encrypted_file.is_dir():
            raise RuntimeError(
                f"Encrypted keys file {self.encrypted_file} is a directory. "
                f"Please remove this directory."
            )
        
        cipher = self._get_cipher()
        data = json.dumps(keys).encode()
        encrypted_data = cipher.encrypt(data)
        self.encrypted_file.write_bytes(encrypted_data)
        
        # Secure the encrypted file
        if hasattr(os, 'chmod'):
            os.chmod(self.encrypted_file, 0o600)
    
    def store_key(self, name: str, api_key: str) -> None:
        """Store an API key securely.
        
        Args:
            name: Name/identifier for the API key
            api_key: The API key to store
        """
        if self.use_keyring:
            try:
                keyring.set_password(self.SERVICE_NAME, name, api_key)
                return
            except KeyringError:
                # Fall back to encrypted file if keyring fails
                pass
        
        # Use encrypted file storage
        keys = self._load_encrypted_keys()
        keys[name] = api_key
        self._save_encrypted_keys(keys)
    
    def get_key(self, name: str) -> Optional[str]:
        """Retrieve an API key.
        
        Args:
            name: Name/identifier for the API key
            
        Returns:
            The API key or None if not found
        """
        if self.use_keyring:
            try:
                return keyring.get_password(self.SERVICE_NAME, name)
            except KeyringError:
                # Fall back to encrypted file
                pass
        
        # Use encrypted file storage
        keys = self._load_encrypted_keys()
        return keys.get(name)
    
    def delete_key(self, name: str) -> bool:
        """Delete an API key.
        
        Args:
            name: Name/identifier for the API key
            
        Returns:
            True if deleted, False if not found
        """
        if self.use_keyring:
            try:
                keyring.delete_password(self.SERVICE_NAME, name)
                return True
            except KeyringError:
                # Fall back to encrypted file
                pass
        
        # Use encrypted file storage
        keys = self._load_encrypted_keys()
        if name in keys:
            del keys[name]
            self._save_encrypted_keys(keys)
            return True
        return False
    
    def list_keys(self) -> list[str]:
        """List all stored key names.
        
        Returns:
            List of key names
        """
        if self.use_keyring:
            # Keyring doesn't provide a list operation
            # We need to maintain a separate index
            # For now, fall through to encrypted file
            pass
        
        keys = self._load_encrypted_keys()
        return list(keys.keys())
    
    def get_storage_method(self) -> str:
        """Get the current storage method being used.
        
        Returns:
            'keyring' or 'encrypted_file'
        """
        return "keyring" if self.use_keyring else "encrypted_file"
    
    def migrate_from_plaintext(self, plaintext_keys: dict[str, str]) -> int:
        """Migrate keys from plaintext config to secure storage.
        
        Args:
            plaintext_keys: Dictionary of name -> api_key
            
        Returns:
            Number of keys migrated
        """
        count = 0
        for name, api_key in plaintext_keys.items():
            self.store_key(name, api_key)
            count += 1
        return count
