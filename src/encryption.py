from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from typing import Any, Final

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class EncryptionHandler:
    _instance: EncryptionHandler | None = None

    def __init__(self):
        EncryptionHandler._instance = self
        self.key: Final[str] = str(uuid.uuid4())

    @classmethod
    def get_instance(cls) -> EncryptionHandler:
        """
        Returns the singleton instance of EncryptionHandler.
        """

        if cls._instance is None:
            cls._instance = EncryptionHandler()

        return cls._instance

    def get_key(self) -> str:
        """
        Returns the encryption key.
        """

        return self.key

    def encrypt_notification(self, payload: dict[str, Any]) -> str:
        """
        Encrypts the notification payload using AES encryption with a randomly generated IV.

        Args:
            payload (dict[str, Any]): The notification payload to encrypt.

        Returns:
            str: The encrypted notification payload as a Base64-encoded string.
        """

        # 1. Derive the Key (SHA-256)
        key_bytes = hashlib.sha256(self.key.encode("utf-8")).digest()

        # 2. Serialize JSON
        raw_json = json.dumps(payload)

        # 3. Apply Padding (PKCS7)
        # AES blocks are 16 bytes (128 bits)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(raw_json.encode("utf-8")) + padder.finalize()

        # 4. Generate Random IV (16 bytes)
        iv = os.urandom(16)

        # 5. Encrypt (AES-CBC)
        cipher = Cipher(
            algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # 6. Combine & Base64 Encode
        # Format: Base64( IV + Ciphertext )
        final_blob = iv + ciphertext
        return base64.b64encode(final_blob).decode("utf-8")
