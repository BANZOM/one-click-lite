from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/create-user', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'username' not in data or 'ips' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    username = data['username']
    ips = [ip.strip() for ip in data['ips'].split(',')]
    #TODO: create SSH connection to the server and add the user with the given IPs
    return jsonify({'message': f'User {username} created with IPs: {ips}'}), 201

if __name__ == '__main__':
    app.run(debug=True)