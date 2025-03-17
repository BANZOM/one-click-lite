from utils.validators import validate_ip
import logging

logger = logging.getLogger(__name__)

def get_ips_from_group(group, base_path="assets/groups"):
    """
    Retrieves IP addresses from a single group file.

    Args:
        group: The name of the group.
        base_path: The directory where group files are located.

    Returns:
        A list of valid IP addresses found in the specified group file.
        Returns an empty list if the group file is not found or contains no valid IPs.
    """
    filename = f"{base_path}/{group}.txt"
    try:
        logging.info(f"Retrieving IPs from group: {group}")
        with open(filename, 'r') as file:
            ips = [line.strip() for line in file if validate_ip(line.strip())]
            return ips
    except FileNotFoundError:
        logger.warning(f"Group file not found: {filename}")
        return []