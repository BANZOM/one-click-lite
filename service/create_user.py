import paramiko
import os
import socket  
import logging
from service.crypt_service import decrypt_file
from service.csv_service import write_to_csv
from service.ssh_service import SSHClient

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
    client = SSHClient(ip)
    try: 
        logger.debug(f"Attempting to create user '{username}' on {ip}")
        success, message = client.connect()
        if not success:
            return success, message

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

    except paramiko.SSHException as e:
        logger.exception(f"SSH connection error for {ip}: {e}")
        return False, str(e)
    except Exception as e:
        logger.exception(f"General error connecting to {ip}: {e}")
        return False, str(e)
    finally:
        client.close()