import paramiko
import os
import socket  
import logging
from service.csv_service import write_to_csv

logger = logging.getLogger(__name__)  # Use the module name for the logger
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_user_on_server(ip, username, pub_key):
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

    def _execute_commands(client):
        """Helper function to execute commands and check for errors."""
        logger.debug(f"Attempting to create user '{username}' on {ip}")

        stdin, stdout, stderr = client.exec_command(f"id -u {username}")
        if stdout.channel.recv_exit_status() == 0:
            message = f"User '{username}' already exists on {ip}"
            logger.warning(message)
            return False, message

        commands = [
            f"sudo useradd -m -s /bin/bash {username}",
            f"sudo mkdir -p /home/{username}/.ssh",
            f"sudo chown -R {username}:{username} /home/{username}/.ssh",
            f"sudo chmod 700 /home/{username}/.ssh",
        ]
        if pub_key:
            commands.extend([
                f"sudo sh -c 'echo \"{pub_key}\" >> /home/{username}/.ssh/authorized_keys'",
                f"sudo chown {username}:{username} /home/{username}/.ssh/authorized_keys",
                f"sudo chmod 600 /home/{username}/.ssh/authorized_keys",
            ])

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

        message = f"User '{username}' created successfully on {ip}"
        logger.info(message)
        write_to_csv(username, ip) 
        return True, message

    try:
        if admin_password:
            try:
                logger.info(f"Attempting password authentication to {ip} as {admin_username}")
                ssh_client.connect(ip, username=admin_username, password=admin_password)
                success, message = _execute_commands(ssh_client)
                if success:
                    return success, message
                else:
                    logger.warning(f"Password authentication succeeded, but user creation failed: {message}")
                    # Fallback to key-based auth
            except paramiko.AuthenticationException:
                logger.warning(f"Password authentication failed for {ip}. Trying key-based authentication...")
            except socket.error as e: 
                logger.error(f"Socket error connecting to {ip}: {e}")
                return False, str(e)
            except Exception as e:
                logger.exception(f"An error occurred during password authentication for {ip}: {e}")  
                return False, str(e)
            
        if pem_file_path and os.path.exists(pem_file_path):
            try:
                logger.info(f"Attempting key-based authentication to {ip} as {admin_username} using {pem_file_path}")
                ssh_client.connect(ip, username=admin_username, key_filename=pem_file_path)
                return _execute_commands(ssh_client)
            except paramiko.AuthenticationException:
                logger.error(f"Key-based authentication failed for {ip}.")
                return False, "Key-based authentication failed"
            except socket.error as e:
                logger.error(f"Socket error connecting to {ip}: {e}")
                return False, str(e)
            except Exception as e:
                logger.exception(f"An error occurred during key-based authentication: {e}")
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