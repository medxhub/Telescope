from flask import Flask, request, jsonify, render_template
import json
import os
## debug output
import sys

app = Flask(__name__)

# Directory to store server data
DATA_DIR = "server_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

server_inventories = {}

def load_server_inventories():
    """ Load server inventories from JSON files in the upload directory based on filenames. """
    server_inventories.clear()  # Clear existing data

    # Search for all .json files in the upload directory
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):  # Assuming the filename format is 'server_name.json'
            server_name = os.path.splitext(filename)[0]  # Get server name from filename
            file_path = os.path.join(DATA_DIR, filename)

            # Load the JSON content from the file
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Store the inventory under the server name
                    #print("server_inventories[server_name] = data['inventory']",file=sys.stdout)
                    server_inventories[server_name] = data['inventory']
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error reading {filename}: {e}")
    #print(server_inventories, file=sys.stdout)

# Home route to display the search interface
@app.route('/')
def index():
    load_server_inventories()
    return render_template('index.html', servers=server_inventories,cnt=len(server_inventories))


# Route to upload server inventory data
@app.route('/upload', methods=['POST'])
def upload_data():
    if request.is_json:
        data = request.get_json()
        server_name = data.get('server_name', 'unknown')

        # Store data as a JSON file
        file_path = os.path.join(DATA_DIR, f'{server_name}.json')
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
    app.run(host='0.0.0.0', port=4343, ssl_context=context,debug=True)
