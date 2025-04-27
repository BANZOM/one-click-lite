import io
import paramiko
import os
from dotenv import load_dotenv
import logging
import socket

# For Debugging, when running the script directly
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.crypt_service import decrypt_file
load_dotenv()

logger = logging.getLogger(__name__)

class SSHClient(paramiko.SSHClient):
    def __init__(self, ip, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_missing_host_key_policy(paramiko.WarningPolicy())
        self._admin_username = os.getenv('ADMIN_USERNAME', "ubuntu")
        self._admin_password = os.getenv('ADMIN_PASSWORD', None)
        self._pem_file_path = os.getenv('PEM_FILE_PATH')
        self._crypt_password = os.getenv('CRYPT_PASSWORD', None)
        self.ip = ip
        self.set_missing_host_key_policy(paramiko.WarningPolicy())

    def connect(self) -> tuple[bool, str]:
        if self._admin_password:
            try:
                logger.info(f"Attempting password authentication to {self.ip} as {self._admin_username}")
                super().connect(self.ip, username=self._admin_username, password=self._admin_password, timeout=5)
                return True, f"Connected to {self.ip} as {self._admin_username}"
            except paramiko.AuthenticationException:
                logger.warning(f"Password authentication failed for {self.ip}. Trying key-based authentication...")
            except TimeoutError as e:
                message = f"Unable to connect to {self.ip}: {e}"
                logger.warning(message)
                return False, message
            except (socket.error, Exception) as e:
                logger.exception(f"Error during password authentication for {self.ip}: {e}")
                return False, str(e)
        
        if self._pem_file_path and os.path.exists(self._pem_file_path):
            try:
                logger.info(f"Attempting key-based authentication to {self.ip} as {self._admin_username} using {self._pem_file_path}")

                private_key_bytes = decrypt_file(self._pem_file_path, self._crypt_password)
                if not private_key_bytes:
                    message = f"Decryption of {self._encrypted_pem_path} returned empty data."
                    logger.error(message)
                    return False, message

                try:
                    decrypted_key_string = private_key_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    logger.error(f"Failed to decode decrypted key from {self._encrypted_pem_path} as UTF-8. Is it a valid PEM key?")
                    return False, f"Decrypted key from {self._encrypted_pem_path} is not valid UTF-8 text."
                
                key_file_obj = io.StringIO(decrypted_key_string)
                private_key = paramiko.RSAKey(file_obj=key_file_obj)

                super().connect(self.ip, username=self._admin_username, pkey=private_key, timeout=5)
                return True, f"Connected to {self.ip} as {self._admin_username}"
            except paramiko.AuthenticationException:
                message = f"Key-based/Password authentication failed for {self.ip}."
                logger.error(message)
                return False, message
            except TimeoutError as e:
                message = f"Unable to connect to {self.ip}: {e}"
                logger.warning(message)
                return False, message
            except (socket.error, Exception) as e:
                logger.exception(f"Error during key-based authentication for {self.ip}: {e}")
                return False, str(e)
            
        elif self._pem_file_path:
            logger.error(f"PEM file not found at specified path {self._pem_file_path}")
            return False, "PEM file not found"
        else:
            logger.error(f"Neither the admin password nor the PEM file was found")
            return False, "Authentication details not provided"


if __name__ == "__main__":
    # Example usage
    ssh_client = SSHClient("127.0.0.1")
    success, message = ssh_client.connect()
    try:
        if success:
            print("Connected successfully")
            # Execute a command
            stdin, stdout, stderr = ssh_client.exec_command("cat /etc/hostname")
            print(stdout.read().decode())
        else:
            print(f"Connection failed: {message}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ssh_client.close()
        print("Connection closed")



    