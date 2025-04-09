import logging
import os
logger = logging.getLogger(__name__)

def get_group_list(base_path="assets/groups"):
    """
    Retrieves a list of available groups from the specified directory.

    Args:
        base_path: The directory where group files are located.

    Returns:
        A list of group names (without the .txt extension).
    """
    try:
        logger.info("Retrieving group list")
        groups = [f.split('.')[0] for f in os.listdir(base_path) if f.endswith('.txt')]
        return groups
    except FileNotFoundError:
        logger.warning(f"Group directory not found: {base_path}")
        return []