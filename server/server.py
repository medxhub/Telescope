from flask import Flask, request, jsonify, render_template
import json
import os

app = Flask(__name__)

# Directory to store server data
DATA_DIR = "server_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# A global variable to store server inventories
server_inventories = {}

def load_server_inventories():
    """ Load server inventories from the upload directory. """
    global server_inventories
    server_inventories.clear()  # Clear existing data
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):  # Assuming inventory files are in JSON format
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                data = json.load(f)
                server_name = data.get('server_name')
                if server_name:
                    server_inventories[server_name] = data['inventory']


# Home route to display the search interface
@app.route('/')
def index():
    return render_template('index.html', servers=server_inventories)


# Route to upload server inventory data
@app.route('/upload', methods=['POST'])
def upload_data():
    if request.is_json:
        data = request.get_json()
        server_name = data.get('server_name', 'unknown')

        # Store data as a JSON file
        file_path = os.path.join(DATA_DIR, f'{server_name}_data.json')
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        return jsonify({"message": f"Data received for {server_name}"}), 200
    else:
        return jsonify({"error": "Invalid JSON"}), 400

# Route to handle search requests
@app.route('/search', methods=['GET'])
def search_inventory():
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', 'user')  # Default to user search

    results = []
    
    # Loop through stored server data
    for file_name in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, file_name)
        with open(file_path, 'r') as f:
            data = json.load(f)
            
            if search_type == 'user':
                # Search in the user list
                for user in data.get('users', []):
                    if query.lower() in user.lower():
                        results.append({'server': data['server_name'], 'user': user})
            
            elif search_type == 'package':
                # Search in the installed packages list
                for package in data['inventory'].get('installed_packages', []):
                    if query.lower() in package.lower():
                        results.append({'server': data['server_name'], 'package': package})

            elif search_type == 'binary':
                # Search in the binaries list
                for binary, version in data['inventory'].get('binaries', {}).items():
                    if query.lower() in binary.lower() or query.lower() in version.lower():
                        results.append({'server': data['server_name'], 'binary': binary, 'version': version})

    return jsonify(results)

if __name__ == '__main__':
    # Use self-signed certificates for HTTPS
    context = ('certs/server.crt', 'certs/server.key')
    app.run(host='0.0.0.0', port=4343, ssl_context=context)

