import base64
import hashlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# 1. The Encrypted Blob you captured earlier
# (From your message: "androidData": "y9a1Dkf...")
ENCRYPTED_BLOB_B64 = "Oi+aOQAVNaz892+3ycK4lYpNvRSAlh675y4SvZ9jnU5uwLzz0y70tFYgDombNOgLGqeLWyS3vHlAwP/0PQ3UU/eR/txiveVzOmXmrBrUfpMyRBM1xI+qtJgVo66Qfc8/HUo4Gxj9pl4RL9JRy0n33S6oQuobvVjCGjkuCrl1zbe1CNeFuCH8jXXocU5X7qIRAuMAZhyiP0Jtcp4d2vS9PQGnB/e+V2nsfaNYpRFgbCOo0ZSeK4nOKKDeLhN37ouST58VZ6EbRjKAwxxGlYcwdUnKp+ZGadTisDRNAOhq+58EAJG6AAiGHCstXcaCr/TD+tKJ+0nwqeH+PUc0d1sYF3lxxlISjYMD1lr3JnCMFVg="

# 2. The UUID Key
# (Try the one you found in Wireshark: f746...)
CANDIDATE_UUID = "f746f80a-160e-4a9b-b074-64a0f8963473"


def decrypt_octoapp_message(uuid_key, blob_b64):
    print(f"--- Decrypting with Key: {uuid_key} ---")

    try:
        # 1. Decode Base64
        data = base64.b64decode(blob_b64)

        # 2. Extract IV and Ciphertext
        # The source code does: base64( iv + ciphertext )
        # AES Block size is 16 bytes
        iv = data[:16]
        ciphertext = data[16:]

        print(f"Total Bytes: {len(data)}")
        print(f"IV: {iv.hex()}")
        print(f"Ciphertext: {len(ciphertext)} bytes")

        # 3. Derive Key (SHA-256)
        # Source: self.key = hashlib.sha256(key.encode()).digest()
        key_bytes = hashlib.sha256(uuid_key.encode("utf-8")).digest()

        # 4. Decrypt (AES-CBC)
        # Source: AES.new(self.key, AES.MODE_CBC, iv)
        cipher = Cipher(
            algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

        # 5. Unpad (PKCS7)
        # The source code uses manual padding, but it follows PKCS7 standards.
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()

        # 6. Decode to Text
        print("\n✅ SUCCESS! Decrypted JSON:")
        print(decrypted_data.decode("utf-8"))
        return True

    except ValueError as e:
        print("\n❌ Decryption Failed: Padding Error.")
        print("This usually means the Password (UUID) is wrong.")
        print(f"Raw decrypted (garbage): {decrypted_padded[:20]}...")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    return False


# Run it
decrypt_octoapp_message(CANDIDATE_UUID, ENCRYPTED_BLOB_B64)
