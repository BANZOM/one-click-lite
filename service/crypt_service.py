from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import algorithms, modes, Cipher
from cryptography.hazmat.primitives.padding import PKCS7
import secrets
import logging

logger = logging.getLogger(__name__)

SALT_SIZE = 16
KEY_SIZE = 32
IV_SIZE = 16
ITERATIONS = 100_000

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derives a key from a password and salt using PBKDF2.
    PBDKFHMAC stands for "Password-Based Key Derivation Function 2 with Hash Message Authentication Code"
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))

def encrypt_file(input_file_path: str, output_file_path: str, password: str) -> None:
    """Encrypts a file using AES-GCM with a key derived from a password.

    Args:
        input_file_path: Path to the file to encrypt.
        output_file_path: Path to save the encrypted file.
        password: Password to use for key derivation.

    Example:
        encrypt_file('input_file.pem', 'encrypted_file.enc', 'my_password')
    """
    try:
        salt = secrets.token_bytes(SALT_SIZE)
        iv = secrets.token_bytes(IV_SIZE)
        key = derive_key(password, salt)

        with open(input_file_path, "rb") as f:
            plaintext = f.read()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = PKCS7(algorithms.AES.block_size).padder()
        padded_plaintext = padder.update(plaintext) + padder.finalize()

        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        with open(output_file_path, "wb") as f:
            f.write(salt + iv + ciphertext)
    except Exception as e:
        logger.error(f"Error encrypting file: {e}")
        raise

def decrypt_file(input_file_path: str, password: str) -> bytes:
    """Decrypts a file encrypted with encrypt_file() and returns the content.
        This avoids writing the decrypted file to disk.

    Args:
        input_file_path: Path to the encrypted file.
        password: Password used for encryption.

    Returns:
        bytes: The decrypted content of the file.

    Raises:
        ValueError: If the password is incorrect or the file is corrupted.
    """
    try:
        with open(input_file_path, "rb") as f:
            encrypted_data = f.read()

        if len(encrypted_data) < SALT_SIZE + IV_SIZE:
            raise ValueError("Invalid encrypted data format.")
        
        salt = encrypted_data[:SALT_SIZE]
        iv = encrypted_data[SALT_SIZE:SALT_SIZE + IV_SIZE]
        ciphertext = encrypted_data[SALT_SIZE + IV_SIZE:]

        key = derive_key(password, salt)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext
    except ValueError as e:
        logger.error(f"Error with wrong password: {e}")
        raise
    except Exception as e:
        logger.error(f"Error decrypting file: {e}")
        raise


if __name__ == "__main__":
    # encrypt_file("sample.txt", "encrypted.enc", "banzo")
    content = decrypt_file("encrypted.enc", "banzo")
    print(content)

