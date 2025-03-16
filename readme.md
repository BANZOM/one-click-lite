# Configuration Sample

Below is a sample JSON configuration object that you can use as a template:

```json
{
    "username": "sample_user",
    "ips": "192.168.1.100",
    "pub_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... your_public_key",
    "add_to_sudoers": true
}
```

## Field Descriptions

- `username`: The system username to be created or configured
- `ips`: IP address(es) for access control
- `pub_key`: Your SSH public key for authentication
- `add_to_sudoers`: Boolean flag to determine if the user should have sudo privileges

Replace the values with your actual configuration data.