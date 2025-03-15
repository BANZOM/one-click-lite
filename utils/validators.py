import re 

def validate_ip(ip_address):
    """Validates an IP address using regular expressions."""
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"  # Basic IPv4 pattern
    if re.match(pattern, ip_address):
        parts = ip_address.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

def validate_username(username):
    """Validates a username using regular expressions."""
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", username))

def validate_pub_key(pub_key):
    """Validates the format of an SSH public key."""
    # Basic SSH public key patterns (ssh-rsa, ssh-dss, ecdsa-sha2-nistp*, ssh-ed25519)
    patterns = [
        r"^ssh-rsa AAAAB3NzaC1yc2E",  
        r"^ssh-dss AAAAB3NzaC1kc3M",  
        r"^ecdsa-sha2-nistp\d{3} AAAAE2VjZHNhLXNoYTItbmlzdHA", 
        r"^ssh-ed25519 AAAAC3NzaC1lZDI1NTE5", 
    ]
    for pattern in patterns:
        if re.match(pattern, pub_key):
            return True
    return False