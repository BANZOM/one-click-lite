from flask import Flask, request, jsonify
from flask_cors import CORS
import paramiko
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/create-user', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'username' not in data or 'ips' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    username = data.get('username', None)
    ips = [ip.strip() for ip in data['ips'].split(',')]
    pub_key = data.get('pub_key', None)
    # print(f'Creating user {username} on IPs: {ips} and pub_key: {pub_key}')
    #TODO: create SSH connection to the server and add the user with the given IPs

    results = {}
    for ip in ips:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(ip, username=os.getenv('ADMIN_USERNAME'), password=os.getenv('ADMIN_PASSWORD'))
            stdin, stdout, stderr = ssh_client.exec_command("ls -al")
            print(stdout.read().decode('utf-8'))
            # results[ip] = stdout.read().decode('utf-8')
        except Exception as e:
            print(f'Error connecting to {ip}: {e}')
            results[ip] = str(e)
        finally:
            ssh_client.close()

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True)