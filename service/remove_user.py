import logging
from service.csv_service import remove_user_records_from_csv
from service.ssh_service import SSHClient
logger = logging.getLogger(__name__)

def remove_user_from_server(ip, username, action_by_user="System"):
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
        logger.info(f"Attempting removal of user '{username}' from {ip}, requested by '{action_by_user}'")
        success, message = client.connect()
        if not success:
            return success, message

        # Check if the user exists
        stdin, stdout, stderr = client.exec_command(f"id -u {username}")
        user_exists = stdout.channel.recv_exit_status() == 0

        if not user_exists:
            message = f"User '{username}' does not exist on {ip}, skipping removal command."
            logger.info(message + f" (Action by: {action_by_user})")
            # Remove CSV record even if user doesn't exist on server (cleans up potential inconsistencies)
            remove_user_records_from_csv(username, ip, action_by_user)
            # Considered success as the desired state (user gone) is achieved
            return True, message 

        # Attempt user deletion
        logger.info(f"User '{username}' exists on {ip}. Attempting removal (Action by: {action_by_user}).")
        stdin, stdout, stderr = client.exec_command(f"sudo userdel -r {username}") # -r removes home dir
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error_message = stderr.read().decode('utf-8').strip()
            # Check for common non-fatal error: userdel: user X is currently logged in
            if "is currently logged in" in error_message or "process is running" in error_message:
                message = f"Warning: Could not remove user '{username}' from {ip} because they are logged in or have active processes. Manual intervention may be required. Error: {error_message}"
                logger.warning(message + f" (Action by: {action_by_user})")
                # Should we return False here? Maybe. Let's return False as the action wasn't fully completed.
                return False, message
            else:
                message = f"Error removing user '{username}' from {ip}: {error_message}"
                logger.error(message + f" (Action by: {action_by_user})")
                return False, message # Return False on unexpected errors

        # recheck
        stdin_check, stdout_check, stderr_check = client.exec_command(f"id -u {username}")
        if stdout_check.channel.recv_exit_status() == 0:
            # This shouldn't happen if userdel succeeded
            message = f"Error: User '{username}' still exists on {ip} after userdel command."
            logger.error(message + f" (Action by: {action_by_user})")
            return False, message
        else:
            message = f"User '{username}' removed successfully from {ip}."
            logger.info(message + f" (Action by: {action_by_user})")
            # Remove from CSV only after successful confirmation
            remove_user_records_from_csv(username, ip, action_by_user)
            return True, message
    except Exception as e:
        logger.exception(f"General error removing user {username} from {ip} (ActionBy: {action_by_user}): {e}")
        return False, f"General error removing user from {ip}: {e}"
    finally:
        client.close()