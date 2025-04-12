import logging
from service.csv_service import remove_user_records_from_csv
from service.ssh_service import SSHClient
logger = logging.getLogger(__name__)

def remove_user_from_server(ip, username):
    """
    Remove a user from the server at the specified IP address.

    Args:
        ip: The IP address of the server.
        username: The username to remove.

    Returns:
        A tuple: (success, message), where success is a boolean indicating
        success or failure, and message is a string containing output or error.
    """
    client = SSHClient(ip)
    try:
        success, message = client.connect()
        if not success:
            return success, message

        stdin, stdout, stderr = client.exec_command(f"id -u {username}")
        user_exists = stdout.channel.recv_exit_status() == 0

        if not user_exists:
            message = f"User '{username}' does not exist on {ip}"
            logger.info(message)
            remove_user_records_from_csv(username, ip)
            return True, message 

        stdin, stdout, stderr = client.exec_command(f"sudo userdel -r {username}")
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error_message = stderr.read().decode('utf-8').strip()
            message = f"Error removing user '{username}' from {ip}: {error_message}"
            logger.error(message)
            return False, message

        message = f"User '{username}' removed successfully from {ip}"
        logger.info(message)

        # recheck
        stdin, stdout, stderr = client.exec_command(f"id -u {username}")
        user_exists = stdout.channel.recv_exit_status() == 0
        if user_exists:
            message = f"User '{username}' still exists on {ip} after removal"
            logger.error(message)
            return False, message
        message = f"User '{username}' successfully removed from {ip}"
        logger.info(message)
        remove_user_records_from_csv(username, ip)  
        return True, message

    finally:
        client.close()