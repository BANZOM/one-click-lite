import csv
import fileinput
import os
from datetime import datetime
import logging
import sys

logger = logging.getLogger(__name__)
DATA_FILE = "logs/user_records.csv"
FIELDNAMES = ['Timestamp', 'IP Address', 'Username', 'Action By']

if not os.path.exists("logs"):
    os.makedirs("logs")
    logger.info("Created logs directory.")

if not os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
        logger.info(f"Created {DATA_FILE} with headers: {FIELDNAMES}")
    except IOError as e:
         logger.error(f"Failed to create {DATA_FILE}: {e}")
else:
    try:
        with open(DATA_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            try:
                header = next(reader)
                if header != FIELDNAMES:
                    logger.warning(f"CSV file {DATA_FILE} header mismatch. Expected {FIELDNAMES}, found {header}. Manual correction might be needed.")
                    # Consider adding migration logic here in a real app
            except StopIteration: # File is empty
                with open(DATA_FILE, 'w', newline='') as outfile: # Overwrite/create header
                    writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
                    writer.writeheader()
                    logger.info(f"CSV file {DATA_FILE} was empty. Wrote headers: {FIELDNAMES}")
    except IOError as e:
        logger.error(f"Error checking/reading header for {DATA_FILE}: {e}")
    except Exception as e: # Catch broader exceptions during header check
        logger.error(f"Unexpected error during header check for {DATA_FILE}: {e}", exc_info=True)

def write_to_csv(username, ip, action_by):
    """Writes a user record to the CSV file."""
    try:
        file_exists = os.path.exists(DATA_FILE)
        with open(DATA_FILE, mode='a', newline='') as csvfile:
            fieldnames = ['Timestamp', 'IP Address', 'Username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({''
                'Timestamp': datetime.now().isoformat(), 
                'IP Address': ip, 
                'Username': username, 
                'Action By': action_by
            })
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
            if not reader.fieldnames or not all(hrd in reader.fieldnames for hrd in FIELDNAMES):
                logger.error(f"CSV file {DATA_FILE} has incorrect headers. Expected {FIELDNAMES}, got {reader.fieldnames}")
                return []

            for row in reader:
                if row['Username'] == username and row['IP Address']:
                    servers.add(row['IP Address'])
    except FileNotFoundError:
        logger.warning(f"CSV file not found: {DATA_FILE}")
    except Exception as e:
        logger.error(f"Error reading CSV file {DATA_FILE}: {e}")
    return list(servers)

def remove_user_records_from_csv(username: str, ip: str = None, action_by: str = 'System'):
    """Removes user records from the CSV.

    If ip is None, removes ALL records for the user.
    If ip is provided, removes only records matching both username and ip.
    """
    if ip:
        log_message = f"Attempting removal of record for user '{username}' and IP '{ip}' from {DATA_FILE}, requested by '{action_by}'."
    else:
        log_message = f"Attempting removal of ALL records for user '{username}' from {DATA_FILE}, requested by '{action_by}'."
    logger.info(log_message)
    
    temp_file = f"{DATA_FILE}.temp"
    records_removed = False
    
    try:
        # Check if file exists
        if not os.path.exists(DATA_FILE):
            logger.warning(f"CSV file '{DATA_FILE}' is empty or missing.")
            return
            
        # Open original file for reading and temp file for writing
        with open(DATA_FILE, 'r', newline='') as infile, open(temp_file, 'w', newline='') as outfile:
            reader = csv.DictReader(infile)
            
            # Ensure we're using the correct fieldnames from the file
            if not reader.fieldnames:
                logger.error(f"CSV file '{DATA_FILE}' has no headers.")
                return
                
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            
            for row in reader:
                should_keep = True
                
                # Check if this is a row we should remove
                if 'Username' in row and 'IP Address' in row:
                    if ip is None:  # Remove all records for username
                        if row['Username'] == username:
                            should_keep = False
                            records_removed = True
                    else:  # Remove only matching username and IP
                        if row['Username'] == username and row['IP Address'] == ip:
                            should_keep = False
                            records_removed = True
                else:
                    logger.warning(f"Malformed row in CSV missing required fields: {row}")
                    
                if should_keep:
                    writer.writerow(row)
                    
        # Replace original with temp file
        os.replace(temp_file, DATA_FILE)
        
        # Log results
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
        # Clean up temp file if it exists
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

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
            # Check for empty file
            csvfile.seek(0, os.SEEK_END)
            if csvfile.tell() == 0:
                logger.info(f"Log file is empty: {DATA_FILE}")
                return log_data, error_message # Return empty list, no error message needed for empty file
            csvfile.seek(0)

            reader = csv.DictReader(csvfile)

            # Validate headers
            if not reader.fieldnames or not all(hdr in reader.fieldnames for hdr in FIELDNAMES):
                error_message = f"Error: Log data file ({DATA_FILE}) missing required headers ({', '.join(FIELDNAMES)}). Found: {reader.fieldnames}"
                logger.error(error_message)
            else:
                log_data = list(reader)
                logger.info(f"Successfully read {len(log_data)} records from {DATA_FILE}.")

    except FileNotFoundError: # Should be caught above, but handle defensively
        error_message = f"Error: Log data file ({DATA_FILE}) not found."
        logger.warning(error_message)
        log_data = []
    except Exception as e:
        error_message = f"Error: Could not read or parse log data file. Details: {e}"
        logger.exception(f"Error reading log file {DATA_FILE}: {e}")
        log_data = [] # Ensure empty list on error

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

