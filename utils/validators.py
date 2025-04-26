import re
from typing import List

def validate_ip(ip_address: str) -> bool:
    """
    Validates if a string represents a valid IPv4 address.

    Checks both the format (four dot-separated numbers) and the range
    of each number (0-255).

    Args:
        ip_address: The string to validate as an IP address.

    Returns:
        True if the string is a valid IPv4 address, False otherwise.
    """
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, ip_address):
        return False 
    parts = ip_address.split('.')
    return all(0 <= int(part) <= 255 for part in parts)

def validate_username(username: str) -> bool:
    """
    Validates if a username contains only allowed characters.

    Allowed characters are:
    - Uppercase letters (A-Z)
    - Lowercase letters (a-z)
    - Digits (0-9)
    - Underscore (_)
    - Period (.)
    - Hyphen (-)

    Args:
        username: The username string to validate.

    Returns:
        True if the username contains only allowed characters, False otherwise.
    """
    return bool(re.match(r"^[a-zA-Z0-9_.-]+$", username))

def validate_pub_key(pub_key: str) -> bool:
    """
    Performs a basic validation of an SSH public key format by checking its starting prefix.

    This check is *not* exhaustive. It only verifies if the key string begins
    with a known identifier for common key types (RSA, DSS, ECDSA, Ed25519).
    It does not validate the Base64 encoding or the key's cryptographic integrity.

    Args:
        pub_key: The SSH public key string to validate.

    Returns:
        True if the key starts with a recognized SSH key type prefix, False otherwise.
    """
    SUPPORTED_KEY_PREFIXES: List[str] = [
        r"^ssh-rsa AAAAB3NzaC1yc2E",      # RSA key prefix
        r"^ssh-dss AAAAB3NzaC1kc3M",      # DSS key prefix (less common now)
        r"^ecdsa-sha2-nistp\d{3} AAAAE2VjZHNhLXNoYTItbmlzdHA", # ECDSA key prefixes (nistp256, 384, 521)
        r"^ssh-ed25519 AAAAC3NzaC1lZDI1NTE5", # Ed25519 key prefix
    ]

    return any(re.match(pattern, pub_key) for pattern in SUPPORTED_KEY_PREFIXES)
