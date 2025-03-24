import paramiko
import os
import socket  
import logging
from service.crypt_service import decrypt_file
from service.csv_service import write_to_csv

logger = logging.getLogger(__name__)  

def create_user_on_server(ip, username, pub_key, add_to_sudoers=False):
    """Creates a user on a remote server via SSH.

    Attempts password-based authentication first, then falls back to PEM key authentication.

    Args:
        ip: The IP address of the server.
        username: The username to create.
        pub_key: The public key to authorize for the user.

    Returns:
        A tuple: (success, message), where success is a boolean indicating
        success or failure, and message is a string containing output or error.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

    admin_username = os.getenv('ADMIN_USERNAME', "ubuntu")
    admin_password = os.getenv('ADMIN_PASSWORD', None)
    pem_file_path = os.getenv('PEM_FILE_PATH')
    crypt_password = os.getenv('CRYPT_PASSWORD', None)

    def _execute_commands(client):
        """Helper function to execute commands and check for errors."""
        logger.debug(f"Attempting to create user '{username}' on {ip}")

        stdin, stdout, stderr = client.exec_command(f"id -un {username} 2>/dev/null && groups {username}")
        exit_status = stdout.channel.recv_exit_status()
        user_exists = (exit_status == 0)
        groups = ""
        if user_exists:
            output = stdout.read().decode('utf-8').strip()
            parts = output.split(":")
            if len(parts) > 1:
                groups = parts[1].strip()
            logger.info(f"User '{username}' already exists on {ip}")

        commands = []
        if not user_exists:
            commands.extend([
                f"sudo useradd -m -s /bin/bash {username}",
                f"sudo mkdir -p /home/{username}/.ssh",
                f"sudo chown -R {username}:{username} /home/{username}/.ssh",
                f"sudo chmod 700 /home/{username}/.ssh",
            ])
            logger.info(f"Creating user '{username}' on {ip}")
        else:
            logger.info(f"User '{username}' already exists on {ip}, proceeding with other configurations")

        if pub_key:
            stdin, stdout, stderr = client.exec_command(f"test -d /home/{username}/.ssh")
            ssh_dir_exists = stdout.channel.recv_exit_status() == 0
            
            if not ssh_dir_exists:
                commands.extend([
                    f"sudo mkdir -p /home/{username}/.ssh",  # Ensures .ssh exists
                    f"sudo chown {username}:{username} /home/{username}/.ssh",
                    f"sudo chmod 700 /home/{username}/.ssh",
                ])
                logger.info(f"Creating .ssh directory for user '{username}' on {ip}")
            
            stdin, stdout, stderr = client.exec_command(f"test -f /home/{username}/.ssh/authorized_keys")
            auth_keys_exists = stdout.channel.recv_exit_status() == 0
            
            if not auth_keys_exists:
                commands.append(f"sudo touch /home/{username}/.ssh/authorized_keys")
                commands.append(f"sudo chown {username}:{username} /home/{username}/.ssh/authorized_keys")
                commands.append(f"sudo chmod 600 /home/{username}/.ssh/authorized_keys")
                logger.info(f"Creating authorized_keys file for user '{username}' on {ip}")
            
            stdin, stdout, stderr = client.exec_command(f"sudo grep -Fwq '{pub_key}' /home/{username}/.ssh/authorized_keys || echo 'NOT_FOUND'")
            output = stdout.read().decode().strip()
            if output == 'NOT_FOUND':
                # Add the key safely using printf to avoid issues with special characters
                commands.append(f"sudo sh -c 'printf \"%s\\n\" \"{pub_key}\" >> /home/{username}/.ssh/authorized_keys'")
                commands.append(f"sudo chown {username}:{username} /home/{username}/.ssh/authorized_keys")
                commands.append(f"sudo chmod 600 /home/{username}/.ssh/authorized_keys")
                logger.info(f"Adding public key for user '{username}' on {ip}")
            else:
                logger.info(f"Public key for user '{username}' on '{ip}' already exists")

        if add_to_sudoers:
            if f"sudo" not in groups:
                commands.append(f"sudo usermod -aG sudo {username}")
                logger.info(f"Adding user '{username}' to the sudo group on {ip}")
            else:
                logger.info(f"User '{username}' is already in the sudo group on {ip}")
        elif f"sudo" in groups:
            commands.append(f"sudo deluser {username} sudo")
            logger.info(f"Removing user '{username}' from the sudo group on {ip}")

        for command in commands:
            logger.debug(f"Executing command on {ip}: {command}")
            stdin, stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_message = stderr.read().decode('utf-8').strip()
                message = f"Error executing command '{command}' on {ip}: {error_message}"
                logger.error(message)
                return False, message
            logger.debug(stdout.read().decode('utf-8').strip())

        if user_exists:
            message = f"User '{username}' configured successfully on {ip}."
        else:
            message = f"User '{username}' created and configured successfully on {ip}."
        write_to_csv(username, ip) 
        return True, message

    try:
        if admin_password:
            try:
                logger.info(f"Attempting password authentication to {ip} as {admin_username}")
                ssh_client.connect(ip, username=admin_username, password=admin_password, timeout=5)
                success, message = _execute_commands(ssh_client)
                return success, message
            except paramiko.AuthenticationException:
                logger.warning(f"Password authentication failed for {ip}. Trying key-based authentication...")
            except (socket.error, Exception) as e:
                logger.exception(f"Error during password authentication for {ip}: {e}")
                return False, str(e)
            
        if pem_file_path and os.path.exists(pem_file_path):
            try:
                logger.info(f"Attempting key-based authentication to {ip} as {admin_username} using {pem_file_path}")
                private_key_data = decrypt_file(pem_file_path, crypt_password)
                private_key = paramiko.RSAKey(file_obj=private_key_data.decode())
                ssh_client.connect(ip, username=admin_username, pkey=private_key, timeout=5)
                return _execute_commands(ssh_client)
            except paramiko.AuthenticationException:
                message = f"Key-based/Password authentication failed for {ip}."
                logger.error(message)
                return False, message
            except (socket.error, Exception) as e:
                logger.exception(f"Error during key-based authentication for {ip}: {e}")
                return False, str(e)
            
        elif pem_file_path:
            logger.error(f"PEM file not found at specified path {pem_file_path}")
            return False, "PEM file not found"
        else:
            logger.error(f"Neither the admin password nor the PEM file was found")
            return False, "Authentication details not provided"

    except paramiko.SSHException as e:
        logger.exception(f"SSH connection error for {ip}: {e}")
        return False, str(e)
    except Exception as e:
        logger.exception(f"General error connecting to {ip}: {e}")
        return False, str(e)
    finally:
        ssh_client.close()