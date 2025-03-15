import paramiko
import os
import socket  


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

        stdin, stdout, stderr = client.exec_command(f"id -u {username}")
        if stdout.channel.recv_exit_status() == 0:
            return False, f"User '{username}' already exists on {ip}"

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
            stdin, stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_message = stderr.read().decode('utf-8').strip()
                return False, f"Error executing command '{command}' on {ip}: {error_message}"
            print(stdout.read().decode('utf-8'))  # Debugging output

        return True, f"User '{username}' created successfully on {ip}"

    try:
        if admin_password:
            try:
                ssh_client.connect(ip, username=admin_username, password=admin_password)
                success, message = _execute_commands(ssh_client)
                if success:
                    return success, message
                else:
                    print(f'Password Worked but still failed: {message}')
                    # Fallback to key-based auth
            except paramiko.AuthenticationException:
                print(f"Password authentication failed for {ip}. Trying key-based authentication...")
            except socket.error as e: 
                 print(f"Socket error connecting to {ip}: {e}")
                 return False, f"Socket error: {e}"
            except Exception as e:
                print(f"An error occurred during password authentication for {ip}: {e}")
                return False, f"Password authentication error: {e}"

        if pem_file_path and os.path.exists(pem_file_path):
            try:
                ssh_client.connect(ip, username=admin_username, key_filename=pem_file_path)
                return _execute_commands(ssh_client)
            except paramiko.AuthenticationException:
                return False, f"Key-based authentication failed for {ip}."
            except socket.error as e: 
                 print(f"Socket error connecting to {ip}: {e}")
                 return False, f"Socket error: {e}"
            except Exception as e:
                return False, f"An error occurred during key-based authentication: {e}"
        elif pem_file_path:
            return False, f"PEM file not found at specified path {pem_file_path}"
        else:
            return False, f"Neither the admin password nor the PEM file was found"

    except paramiko.SSHException as e:
        print(f"SSH connection error for {ip}: {e}")
        return False, f"SSH connection error: {e}"
    except Exception as e:
        print(f"General error connecting to {ip}: {e}")
        return False, f"General error: {e}"
    finally:
        ssh_client.close()