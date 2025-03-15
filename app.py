from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from utils.validators import validate_ip, validate_username, validate_pub_key  
from service.create_user import create_user_on_server

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/create-user', methods=['POST'])
def create_user():
    """API endpoint to create a user on multiple servers."""
    data = request.get_json()
    if not data or 'username' not in data or 'ips' not in data or 'pub_key' not in data:  
        return jsonify({'error': 'Invalid input: username, ips, and pub_key are required'}), 400

    username = data.get('username')
    ip_string = data.get('ips', '')
    pub_key = data.get('pub_key')  

    if not validate_username(username):
        return jsonify({'error': 'Invalid username. Use only letters, numbers, underscores, and hyphens'}), 400

    if not validate_pub_key(pub_key): 
        return jsonify({'error': 'Invalid public key format'}), 400

    ips = [ip.strip() for ip in ip_string.split(',')]
    invalid_ips = [ip for ip in ips if not validate_ip(ip)]
    if invalid_ips:
        return jsonify({'error': f'Invalid IP addresses: {", ".join(invalid_ips)}'}), 400

    if not ips:
        return jsonify({'error': 'At least one IP is required'}), 400

    results = {}
    for ip in ips:
        success, message = create_user_on_server(ip, username, pub_key)  
        results[ip] = {'success': success, 'message': message}

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('APP_PORT', 5000)))