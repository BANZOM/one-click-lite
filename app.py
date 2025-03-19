from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from service.remove_user import remove_user_from_server
from service.csv_service import get_all_servers_for_user
from utils.validators import validate_ip, validate_username, validate_pub_key  
from utils.group_ip_provider import get_ips_from_group
from service.create_user import create_user_on_server
import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'), 
        logging.StreamHandler() 
    ]
)
logger = logging.getLogger(__name__)  

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/create-user', methods=['POST'])
def create_user():
    """API endpoint to create a user on multiple servers."""
    logger.info("Received /create-user request")

    data = request.get_json()
    if not data or 'username' not in data or 'ips' not in data or 'pub_key' not in data:  
        message = 'Invalid username. Use only letters, numbers, underscores, and hyphens'
        logger.warning(message)
        return jsonify({'error': message}), 400

    username = data.get('username')
    group_string = data.get('groups', '')
    manual_ip_string = data.get('ips', '')
    pub_key = data.get('pub_key')
    add_to_sudoers = data.get('add_to_sudoers', False)  

    if not validate_username(username):
        message = 'Invalid username. Use only letters, numbers, underscores, and hyphens'
        logger.warning(message)
        return jsonify({'error': message}), 400

    if not validate_pub_key(pub_key):
        message = 'Invalid public key format'
        logger.warning(message)
        return jsonify({'error': message}), 400
    
    ips = []
    
    if group_string:
        groups = [group.strip() for group in group_string.split(',') if group.strip()]
        for group in groups:
            group_ips = get_ips_from_group(group)
            ips.extend(group_ips)

    if manual_ip_string:
        manual_ips = [ip.strip() for ip in manual_ip_string.split(',') if ip.strip()]
        for ip in manual_ips:
            if validate_ip(ip):
                ips.append(ip)
            else:
                message = f'Invalid IP address: {ip}'
                logger.warning(message)
                return jsonify({'error': message}), 400
            
    ips = list(set(ips))
    if not ips:
        message = 'At least one IP is required'
        logger.warning(message)
        return jsonify({'error': message}), 400

    results = {}
    for ip in ips:
        success, message = create_user_on_server(ip, username, pub_key, add_to_sudoers)
        results[ip] = {'success': success, 'message': message}
        if not success:
            logger.error(f"Failed to create user {username} on {ip}: {message}")


    return jsonify(results), 200

@app.route('/remove-user', methods=['POST'])
def remove_user():
    """API endpoint to remove a user from multiple servers."""
    logger.info("Received /remove-user request")

    data = request.get_json()
    if not data or 'username' not in data:  
        message = 'Invalid request. Username is required'
        logger.warning(message)
        return jsonify({'error': message}), 400

    username = data.get('username')
    ips = data.get('ips', [])  
    remove_from_all = data.get('remove_from_all', False) 

    if not validate_username(username):
        message = 'Invalid username.'
        logger.warning(message)
        return jsonify({'error': message}), 400

    if not ips and not remove_from_all:
        message = "Must specify either 'ips' or 'remove_from_all'"
        logger.warning(message)
        return jsonify({'error': message}), 400
    
    if ips:
        invalid_ips = [ip for ip in ips if not validate_ip(ip)]
        if invalid_ips:
            message = f'Invalid IP addresses: {", ".join(invalid_ips)}'
            logger.warning(message)
            return jsonify({'error': message}), 400
        
    target_ips = []
    if remove_from_all:
        target_ips = get_all_servers_for_user(username)
    elif ips:
        target_ips = ips
    
    results = {}
    for ip in target_ips:
        success, message = remove_user_from_server(ip, username)
        results[ip] = {'success': success, 'message': message}

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('APP_PORT', 5000)))