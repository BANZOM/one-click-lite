import csv
import fileinput
import os
from datetime import datetime
import logging
import sys
logger = logging.getLogger(__name__)

DATA_FILE = "logs/user_records.csv"
if not os.path.exists("logs"):
    os.makedirs("logs")
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'IP Address', 'Username']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

def write_to_csv(username, ip):
    """Writes a user record to the CSV file."""
    try:
        file_exists = os.path.exists(DATA_FILE)
        with open(DATA_FILE, mode='a', newline='') as csvfile:
            fieldnames = ['Timestamp', 'IP Address', 'Username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({'Timestamp': datetime.now().isoformat(), 'IP Address': ip, 'Username': username})
        logger.debug(f"Record for user {username} written to {DATA_FILE}")
    except Exception as e:
        logger.error(f"Error writing to CSV file {DATA_FILE}: {e}")

def get_all_servers_for_user(username):
    """Gets a list of all servers a user was created on from the CSV."""
    servers = set()
    try:
        with open(DATA_FILE, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Username'] == username:
                    servers.add(row['IP Address'])
    except FileNotFoundError:
        logger.warning(f"CSV file not found: {DATA_FILE}")
    return list(servers)

def remove_user_records_from_csv(username):
    """Removes all records for a given user from the CSV using fileinput for in-place editing."""
    records_removed = False
    
    try:
        with open(DATA_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            username_index = header.index('Username')
        
        for line in fileinput.input(DATA_FILE, inplace=True):
            if fileinput.isfirstline():
                sys.stdout.write(line)
                continue
                
            row = next(csv.reader([line]))
            
            if row and len(row) > username_index and row[username_index] != username:
                sys.stdout.write(line)
            else:
                records_removed = True
        
        if records_removed:
            logger.info(f"Removed all records for user '{username}' from {DATA_FILE}")
        else:
            logger.warning(f"No records found for user '{username}' in {DATA_FILE}")
    
    except FileNotFoundError:
        logger.error(f"Original CSV file not found: {DATA_FILE}")
    except Exception as e:
        logger.error(f"An error occurred during CSV processing: {e}")

if __name__ == "__main__":
    # Example usage
    write_to_csv("banzo", "127.0.0.13")
    remove_user_records_from_csv("banzo")
    print(get_all_servers_for_user("banzo"))