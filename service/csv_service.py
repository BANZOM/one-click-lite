import csv
import os
from datetime import datetime


def write_to_csv(username, ip, filename="logs/user_records.csv"):
    """Writes a user record to the CSV file."""
    file_exists = os.path.exists(filename)
    with open(filename, mode='a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'IP Address', 'Username']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'Timestamp': datetime.now().isoformat(), 'IP Address': ip, 'Username': username})