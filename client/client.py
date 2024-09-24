import requests
import platform
import os
import json
import pwd
import subprocess

# List of known binaries to check
KNOWN_BINARIES = ['java', 'python3', 'nginx', 'docker', 'git', 'node', 'perl', 'ruby', 'go', 'mysql', 'postgresql']

def get_server_inventory():
    """ Get basic server information along with installed packages and known binaries. """
    inventory = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'installed_packages': get_installed_packages(),
        'known_binaries': get_known_binaries_versions()
    }
    return inventory

def get_installed_packages():
    """ Get a list of installed packages on the system """
    packages = []

    # Debian-based systems (Ubuntu, Debian)
    try:
        result = subprocess.run(['dpkg-query', '-W', '-f=${binary:Package} ${Version}\n'], stdout=subprocess.PIPE, text=True)
        packages = result.stdout.splitlines()
    except FileNotFoundError:
        # Not a Debian-based system, fallback to RPM-based (CentOS, RHEL)
        try:
            result = subprocess.run(['rpm', '-qa', '--queryformat', '%{NAME} %{VERSION}\n'], stdout=subprocess.PIPE, text=True)
            packages = result.stdout.splitlines()
        except FileNotFoundError:
            # Add support for other systems if needed
            packages.append("Package manager not found.")

    return packages

def get_known_binaries_versions():
    """ Get the versions of known binaries """
    binaries_info = {}
    
    # For each known binary, try to get the version
    for binary in KNOWN_BINARIES:
        version = get_binary_version(binary)
        binaries_info[binary] = version if version else "Version not available"
    
    return binaries_info

def get_binary_version(binary_name):
    """ Try to extract version information for a given binary """
    version_flags = ['--version', '-v', '-V']
    
    for flag in version_flags:
        try:
            result = subprocess.run([binary_name, flag], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if result.returncode == 0:
                # Extract the first line which usually contains the version info
                first_line = result.stdout.splitlines()[0]
                return first_line
        except Exception as e:
            continue
    
    # If no version flag works, return None
    return None

def get_user_list():
    """ Get a list of users on the system """
    users = [user.pw_name for user in pwd.getpwall() if user.pw_uid >= 1000]  # filter system accounts
    return users

def send_data_to_server(url, server_name):
    """ Send the server inventory and user list to the server """
    data = {
        'server_name': server_name,
        'inventory': get_server_inventory(),
        'users': get_user_list()
    }

    try:
        #response = requests.post(url, json=data, verify='certs/ca.crt')
        response = requests.post(url, json=data, verify=False)
        if response.status_code == 200:
            print(f"Success: {response.json()['message']}")
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    server_name = platform.node()  # Use hostname as server name
    server_url = 'https://10.0.2.6:4343/upload'
    
    send_data_to_server(server_url, server_name)

