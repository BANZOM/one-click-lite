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
    """"Gets a UNIQUE list of all servers a user was created on from the CSV."""
    logger.info(f"Fetching all servers for user {username}")
    servers = set()
    try:
        with open(DATA_FILE, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Username'] == username:
                    servers.add(row['IP Address'])
    except FileNotFoundError:
        logger.warning(f"CSV file not found: {DATA_FILE}")
    except Exception as e:
        logger.error(f"Error reading CSV file {DATA_FILE}: {e}")
    return list(servers)

def remove_user_records_from_csv(username: str, ip: str =None):
    """Removes user records from the CSV.

    If ip is None, removes ALL records for the user.
    If ip is provided, removes only records matching both username and ip.
    """
    logger.info(f"Removing records for user {username} from {DATA_FILE}")
    records_removed = False
    try:
        try:
            with open(DATA_FILE, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                username_index = header.index('Username')
                ip_index = header.index('IP Address')  
        except (FileNotFoundError, StopIteration):
            logger.warning(f"CSV file '{DATA_FILE}' is empty or missing.")
            return
        except ValueError as e:
            logger.error(f"CSV file '{DATA_FILE}' is missing required columns: {e}")
            return

        for line in fileinput.input(DATA_FILE, inplace=True):
            if fileinput.isfirstline():
                sys.stdout.write(line) 
                continue

            row = next(csv.reader([line]))

            if row and len(row) > max(username_index, ip_index):
                if ip is None: 
                    if row[username_index] != username:
                        sys.stdout.write(line)
                    else:
                        records_removed = True
                else: 
                    if row[username_index] != username or row[ip_index] != ip:
                        sys.stdout.write(line)
                    else:
                        records_removed = True
            else:
                logger.warning(f"Malformed row in CSV: {line.strip()}")

        if records_removed:
            if ip is None:
                logger.info(f"Removed all records for user '{username}' from {DATA_FILE}")
            else:
                logger.info(f"Removed record(s) for user '{username}' and IP '{ip}' from {DATA_FILE}")
        else:
            if ip is None:
                logger.warning(f"No records found for user '{username}' in {DATA_FILE}")
            else:
                logger.warning(f"No records found for user '{username}' and IP '{ip}' in {DATA_FILE}")

    except Exception as e:
        logger.exception(f"An error occurred during CSV processing: {e}")

def get_all_log_records():
    """
    Reads all records from the user_records.csv file.

    Returns:
        tuple: A tuple containing:
            - list: A list of dictionaries representing the log records.
            - str or None: An error message string if an error occurred, otherwise None.
    """
    log_data = []
    error_message = None
    if not os.path.exists(DATA_FILE):
        error_message = f"Error: Log data file ({DATA_FILE}) not found."
        logger.warning(error_message)
        return log_data, error_message

    try:
        with open(DATA_FILE, mode='r', newline='', encoding='utf-8') as csvfile:
            csvfile.seek(0, os.SEEK_END) 
            file_size = csvfile.tell()  
            if file_size == 0:
                logger.info(f"Log file is empty: {DATA_FILE}")
                return log_data, error_message 

            csvfile.seek(0) 

            reader = csv.DictReader(csvfile)
            required_headers = ['Timestamp', 'IP Address', 'Username']
            if not reader.fieldnames or not all(hdr in reader.fieldnames for hdr in required_headers):
                error_message = f"Error: Log data file ({DATA_FILE}) missing required headers ({', '.join(required_headers)})."
                logger.error(error_message)
            else:
                 log_data = list(reader)
                 logger.info(f"Successfully read {len(log_data)} records from {DATA_FILE}.")

    except FileNotFoundError: 
         error_message = f"Error: Log data file ({DATA_FILE}) not found."
         logger.warning(error_message)
         log_data = []
    except Exception as e:
        error_message = f"Error: Could not read or parse log data file. Details: {e}"
        logger.exception(f"Error reading log file {DATA_FILE}: {e}")
        log_data = []

    return log_data, error_message

if __name__ == "__main__":
    # Example usage
    # write_to_csv("banzo", "127.0.0.13")
    # write_to_csv("banzo", "127.0.0.14")
    # write_to_csv("banzo", "127.0.0.15")
    # write_to_csv("testuser", "192.168.1.100")
    # write_to_csv("testuser", "192.168.1.101")
    # write_to_csv("anotheruser", "10.0.0.5")
    # write_to_csv("anotheruser", "10.0.0.6")
    # write_to_csv("yetanother", "172.16.0.10")
    # write_to_csv("yetanother", "172.16.0.11")
    # write_to_csv("lastuser", "192.168.0.50")

    # Test removing records
    # remove_user_records_from_csv("banzo")
    # remove_user_records_from_csv("testuser", "192.168.1.100")
    # print(get_all_servers_for_user("dev"))
    # print(get_all_log_records())
    pass
    
    