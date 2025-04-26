import getpass
from werkzeug.security import generate_password_hash
import csv
import os
from dotenv import load_dotenv
load_dotenv()

USERS_FILE = os.getenv("OWNER_IDS_RECORD")

def add_user():
    """Prompts for username and password, hashes password, and adds/updates users.csv."""
    username = input("Enter username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    password = getpass.getpass("Enter password: ")
    if not password:
        print("Password cannot be empty.")
        return

    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Passwords do not match.")
        return

    hashed_password = generate_password_hash(password)

    users = []
    user_found = False
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                # Check for required headers right away
                if not reader.fieldnames or 'username' not in reader.fieldnames or 'password_hash' not in reader.fieldnames:
                     print(f"Error: {USERS_FILE} is missing 'username' or 'password_hash' columns.")
                     # Recreate header if file is empty or malformed? Risky. Better to instruct manual fix.
                     # If file is completely empty, we handle it below.
                     if os.path.getsize(USERS_FILE) == 0:
                         print("File is empty, will create header.")
                     else:
                         return # Exit if headers are wrong and file is not empty

                for row in reader:
                    if row['username'] == username:
                        print(f"Updating password for user '{username}'.")
                        row['password_hash'] = hashed_password
                        user_found = True
                    users.append(row)
        except Exception as e:
            print(f"Error reading {USERS_FILE}: {e}")
            return # Exit on read error

    if not user_found:
        print(f"Adding new user '{username}'.")
        users.append({'username': username, 'password_hash': hashed_password})

    try:
        with open(USERS_FILE, 'w', newline='') as f:
            fieldnames = ['username', 'password_hash']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)
        print(f"Successfully updated {USERS_FILE}.")
    except Exception as e:
        print(f"Error writing to {USERS_FILE}: {e}")


if __name__ == "__main__":
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
         # Create file with header if it doesn't exist or is empty
         try:
             with open(USERS_FILE, 'w', newline='') as f:
                 writer = csv.writer(f)
                 writer.writerow(['username', 'password_hash'])
             print(f"Created {USERS_FILE} with headers.")
         except Exception as e:
              print(f"Error creating {USERS_FILE}: {e}")

    add_user()