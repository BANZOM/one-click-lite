# Configuration Sample

## Create User Configuration
Below is a sample JSON configuration object that you can use as a template:

```json
{
    "username": "sample_user",
    "groups": "sre,devops",
    "ips": "192.168.1.100",
    "pub_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... your_public_key",
    "add_to_sudoers": true
}
```
### Field Descriptions

- `username`: The system username to be created or configured
- `groups`: The Groups for IP/Server Access
- `ips`: IP address(es) for access control
- `pub_key`: Your SSH public key for authentication
- `add_to_sudoers`: Boolean flag to determine if the user should have sudo privileges

Replace the values with your actual configuration data.

## Remove User Configuration
Below is a sample JSON configuration object for removing a user:

```json
{
    "username": "sample_user",
    "ips": [
        "192.168.1.100",
        ...
    ],
    "remove_from_all": true, // if true, remove from all users, then no need to specify ips
}
```

### Field Descriptions
- `username`: The system username to be removed
- `ips`: IP address(es) for access control
- `remove_from_all`: Boolean flag to determine if the user should be removed from all users. If set to true, the `ips` field is ignored.


