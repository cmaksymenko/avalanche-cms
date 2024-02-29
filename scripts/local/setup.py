"""
Avalanche CMS Local Setup Script

Manages local development setup for Avalanche CMS. By default, the script is 
interactive, but can be automated using the -a option, generating strong 
random passwords. It handles secrets generation, writes plaintext secrets to 
'/.secrets', and hashes for Keycloak in './secrets/hashes'. It also updates
existing Docker images (opt-out with -ki).

Command Line Options:
- -a, --auto: Automates setup with random strong passwords.
- -p, --password: Sets a specific password.
- -c, --clean: Cleans the environment for a full reset. Additional options:
    - -kv, --keep-volumes: Retains Docker volumes.
    - -ks, --keep-secrets: Retains secrets and hashes in '.secrets'.
- -s, --salt-base: Sets salt base for hashing (debug only).
- -ki, --keep-images: Doesnt pull the latest Docker images.

Use -c for a full cleanup, resetting the runtime setup and losing all data.
Script assumes location in 'scripts/local' for repo root.
"""

import argparse
import base64
import hashlib
import json
import os
import random
import string
import sys
from cleanup import main as cleanup_main
from pull import main as pull_main
from utils.decorators import require_docker_running

def read_credentials():
    
    file_path = './config/credentials.json'
    
    try:
        with open(file_path, 'r') as file:
            
            data = json.load(file)
        
            for item in data:

                if 'name' not in item or 'base_filename' not in item:
                    sys.exit(f"Error: Each item must have 'name' and 'base_filename'. Missing in item: {item}")
                    
                if item.get('in_pgpass_file', False) and 'username' not in item:
                    sys.exit(f"Error: 'username' must be present when 'in_pgpass_file' is true. Missing in item: {item}")
            
            return data
        
    except FileNotFoundError:
        sys.exit(f"File not found: {file_path}")
    except json.JSONDecodeError:
        sys.exit(f"Error decoding JSON from the file: {file_path}")

# Special characters for secure passwords
SECRET_SPECIAL_CHARS = "!@#$%^&*()-_=+[]{};:,.<>/?|"

# Pool of characters for generating secrets: includes letters, digits, and special characters
SECRET_CHAR_POOL = string.ascii_letters + string.digits + SECRET_SPECIAL_CHARS


def find_project_root(current_file):
    
    """
    Determines the project's root directory from the current script's file path.

    Parameters:
        current_file (str): File path of the script.

    Returns:
        str: Root directory path of the project.
    """    
    
    # Assuming the script is in 'scripts/local'
    # Adjust the number of os.path.dirname calls based on actual script location
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


def generate_deterministic_salt(base_string, salt_length=16):
    
    """
    Generates a deterministic salt from a base string using SHA-256 hashing.

    Parameters:
        base_string (str): Non-empty, non-whitespace string for hashing.
        salt_length (int): Length of the salt, between 1 and 32 (default is 16).

    Returns:
        bytes: Salt derived from the SHA-256 hash of 'base_string'.

    Raises:
        ValueError: If 'base_string' is invalid or 'salt_length' is out of range.
    """
    
    if base_string is None:
        raise ValueError("base_string cannot be None")

    # Strip whitespace from the string
    stripped_string = base_string.strip()

    if len(stripped_string) == 0:
        raise ValueError("base_string cannot be empty or only whitespace")

    if not 0 < salt_length <= 32:
        raise ValueError("salt_length must be between 1 and 32 for SHA-256")

    hashed = hashlib.sha256(stripped_string.encode()).digest()
    return hashed[:salt_length]


def hash_secret(secret, salt_length=16, iterations=27500, salt_base=None):

    """
    Hashes a secret using PBKDF2 for Keycloak, defaulting to random salts for security.

    The 'salt_base' parameter is for debugging and should not be set in regular usage.

    Parameters:
        secret (str): The secret to hash.
        salt_length (int, optional): Length of the salt in bytes. Default is 16.
        iterations (int, optional): Number of hashing iterations. Default is 27500.
        salt_base (str, optional): Base for deterministic salt (debugging use only).

    Returns:
        dict: Contains 'algorithm', 'iterations', 'salt', and 'hash'.

    Raises:
        ValueError: If 'secret' is invalid.
        RuntimeError: For errors during hashing.
    """

    if not isinstance(secret, str) or not secret:
        raise ValueError("Invalid secret provided.")

    try:

        salt = os.urandom(salt_length) # generate salt
        
        if salt_base:
            salt = generate_deterministic_salt(salt_base, salt_length)
        else:
            salt = os.urandom(salt_length) # generate salt

        # Hash using PBKDF2
        hashed_secret = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt, iterations)

        # Encode
        encoded_hash = base64.b64encode(hashed_secret).decode()
        encoded_salt = base64.b64encode(salt).decode()

        return {
            "algorithm": "pbkdf2-sha256",
            "iterations": iterations,
            "salt": encoded_salt,
            "hash": encoded_hash
        }

    except Exception as e:
        raise RuntimeError(f"Error during secret hashing: {e}")


def write_pgpass_file(folder, hostname, port=5432, database="*", tuples=None):

    if not all([hostname, tuples]):
        raise ValueError("Hostname and tuples cannot be None or empty.")

    pgpass_file_path = os.path.join(folder, '.pgpass')
    with open(pgpass_file_path, 'w', newline='\n') as file:
        
        for username, password in tuples:
            connection_string = f"{hostname}:{port}:{database}:{username}:{password}\n"
            file.write(connection_string)

    os.chmod(pgpass_file_path, 0o600)
    
    return pgpass_file_path


def generate_random_password(length=22):
    
    """
    Generates a random password.

    Parameters:
        length (int, optional): The length of the password. Defaults to 22.

    Returns:
        str: A randomly generated password string.
    """    
    
    return ''.join(random.choice(SECRET_CHAR_POOL) for i in range(length))


def prompt_for_secret(description, auto=False):
    
    """
    Prompts for a secret or generates one automatically.

    If 'auto' is True, a secret is generated automatically. Otherwise, it prompts the user for input.
    An empty or whitespace-only input will trigger automatic generation.

    Parameters:
        description (str): Description of the secret for prompting.
        auto (bool, optional): Flag to generate secret automatically. Defaults to False.

    Returns:
        str: A user-provided or automatically generated secret.
    """    
    
    if not auto:
        user_input = input(f"Secret for {description} [Enter=random]: ").strip()
        if user_input: # Will be False for empty, whitespace-only strings, or return key
            return user_input

    print(f"Generating secret for {description}.")
    
    return generate_random_password()


def create_secret_file(path, secret):
    
    """
    Creates a file with the given secret if it doesn't exist.

    Parameters:
        path (str): Path to create the secret file.
        secret (str): Secret to write to the file.

    Note:
        Does not overwrite existing files.
    """

    if not os.path.exists(path):
        with open(path, 'w', newline='\n') as file:
            file.write(secret)
        print(f"Secret file created: {path}")
    else:
        print(f"Existing secret file: {path}, skipped")


def create_hash_file(path, secret, salt_base=None):
    
    """
    Creates a hash file for a secret at 'path', if not already present.

    Parameters:
        path (str): File path for the hash file.
        secret (str): Secret to hash.
        salt_base (str, optional): Base for salt derivation, random if not set.

    Note:
        Skips creation if the file already exists.
    """

    if not os.path.exists(path):

        hashed_data = hash_secret(secret=secret, salt_base=salt_base)
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', newline='\n') as file:
            for key, value in hashed_data.items():
                file.write(f"{key.upper()}={value}\n")

        print(f"Hash file created: {path}")
    else:
        print(f"Existing hash file: {path}, skipped")       

def clean_environment(clean=False, keep_volumes=None, keep_secrets=None):
    
    if clean:
        
        print("Cleaning environment.")
        try:
            cleanup_main(keep_volumes, keep_secrets)
        except Exception as e:
            print("Error during cleanup:", e)
            sys.exit(1)    

def create_secrets(keep_secrets=None, auto=False, password=None, salt_base=None):
    
    if password is not None and password.strip():
        print("Common password set.")
    else:
        if password is not None:
            print("Error: Invalid password.")
            sys.exit(1)    
    
    if not keep_secrets:

        project_root = find_project_root(__file__)
        secrets_path = os.path.join(project_root, '.secrets')

        if not os.path.exists(secrets_path):
            os.makedirs(secrets_path)
            
        credentials = read_credentials()
        
        # Process each secret and create corresponding env/hash files
        for entry in credentials:
            
            name = entry.get("name")
            base_filename = entry.get("base_filename")
            username = entry.get("username", None)
            generate_hash = entry.get("generate_hash", False)
            in_pgpass_file = entry.get("in_pgpass_file", False)
            
            # Construct file paths for secret (and hash) files
            secret_file = os.path.join(secrets_path, base_filename + ".env")
            secret_file_hash = os.path.join(secrets_path, "hashes", base_filename + ".hash") if generate_hash else None
            entry["secret_file"] = secret_file
            
            # Choose password: use provided, prompt, or auto-generate
            secret_value = (password.strip() if password and password.strip() else prompt_for_secret(name, auto))
            entry["secret_value"] = secret_value
        
            
            # Create secret (and hash) files on disk
            create_secret_file(secret_file, secret_value)
            if secret_file_hash is not None:
                create_hash_file(path=secret_file_hash, secret=secret_value, salt_base=salt_base)
                entry["secret_file_hash"] = secret_file_hash
        
        # pgAdmin Password File
        
        pgpass_credentials = []
        
        for entry in credentials:         
            if entry.get('in_pgpass_file', False):
                pgpass_credentials.append((entry.get('username'), entry.get('secret_value')))

        if len(pgpass_credentials) > 0:
            pgpass_file_path = write_pgpass_file(secrets_path, "postgres", 5432, "*", pgpass_credentials)           
            print(f"pgAdmin Password File created at {pgpass_file_path}, number of credentials: {len(pgpass_credentials) }")
            
        else:
            print("No secrets apply for pgAdmin Password File, skipping.")
        
    else:
        print("Skipping secret creation, because cleanup was performed with keeping secrets.")     

@require_docker_running
def update_docker_images(keep_images=False):
    
    if not keep_images:
        
        print("Updating Docker images.")
        try:
            pull_main()
        except Exception as e:
            print("Error during Docker image update:", e)
            sys.exit(1)        
    else:
        print("Skipping Docker image update.")

# Main
def main(auto=False, password=None, clean=False, keep_volumes=None, keep_secrets=None, salt_base=None, keep_images=False):
    
    """
    Main Avalanche CMS setup function.
    """    

    if not password:
        print(f"{'Auto' if auto else 'Manual'} mode.")

    clean_environment(clean=clean, keep_volumes=keep_volumes, keep_secrets=keep_secrets)
    create_secrets(keep_secrets=keep_secrets, auto=auto, password=password, salt_base=salt_base)
    update_docker_images(keep_images=keep_images)
        
    print("Avalanche CMS setup complete.")

    # Suggest auto mode if not used and no password provided
    if not auto and not password:
        print("Tip: Use '--auto' for automatic setup.")             

        
def parse_args():

    parser = argparse.ArgumentParser(description="Avalanche CMS Setup: Interactive local development setup. Automatable with -a for strong random passwords. Manages secrets in '/.secrets' and Keycloak hashes in './secrets/hashes'. Use -c for full cleanup, resetting all data. Assumes 'scripts/local' location for repo root.")

    parser.add_argument('-a', '--auto', action='store_true', help='Automates setup with random strong passwords.')
    parser.add_argument('-p', '--password', type=str, help="Sets a specific password. Enclose symbols in single quotes.")
    parser.add_argument('-c', '--clean', action='store_true', help="Cleans the environment for a full reset. Additional options: -kv, --keep-volumes: Retains Docker volumes; -ks, --keep-secrets: Retains secrets and hashes in '.secrets'")
    parser.add_argument('-s', '--salt-base', type=str, help="Sets salt base for hashing (debug only), defaults to random.")
    parser.add_argument('-ki', '--keep-images', action='store_true', help="Doesnt pull the latest Docker images.")

    args, remaining_argv = parser.parse_known_args()
    
    purge_args = None
    if args.clean:
        
        purge_parser = argparse.ArgumentParser()
        purge_parser.add_argument('-kv', '--keep-volumes', action='store_true', help='Doesnt remove Docker volumes')
        purge_parser.add_argument('-ks', '--keep-secrets', action='store_true', help='Doesnt remove secrets and hashes in /.secrets')
        purge_args = purge_parser.parse_args(remaining_argv)
        
    return args, remaining_argv, purge_args


if __name__ == "__main__":
    
    args, remaining_argv, purge_args = parse_args()
    
    keep_volumes = purge_args.keep_volumes if args.clean else None
    keep_secrets = purge_args.keep_secrets if args.clean else None
    
    main(auto=args.auto, password=args.password, clean=args.clean, 
         keep_volumes=keep_volumes, keep_secrets=keep_secrets, 
         salt_base=args.salt_base, keep_images=args.keep_images)