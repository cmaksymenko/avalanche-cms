"""
Cleans the Avalanche CMS local dev environment.

Shuts down and cleans the local Avalanche CMS dev environment. Supports
optional retention of volumes and secrets.

Options:
- -kv, --keep-volumes: Retain Docker volumes.
- -ks, --keep-secrets: Retain '.secrets'.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from utils.decorators import require_docker_running
from utils.output import print

@require_docker_running
def get_docker_volumes():

    """
    Fetches Docker volume names.

    Returns list of names or empty list on failure.
    """

    result = subprocess.run(["docker", "volume", "ls", "-q"], capture_output=True, text=True)

    if result.returncode != 0:
        print("Error listing Docker volumes")
        return []  # return empty on failure

    # return list of volume names
    return result.stdout.splitlines()

@require_docker_running
def remove_volumes(volumes):
    
    """
    Removes specified Docker volumes.

    Args:
        volumes (list): Volumes to remove.
    """

    for volume in volumes:
        
        print(f"Removing volume {volume}...")
        
        # remove volume
        subprocess.run(["docker", "volume", "rm", "-f", volume], check=True)
        
        print(f"Removed volume {volume}")

def purge_avalanchecms_volumes():
    
    """
    Purges all Avalanche CMS Docker volumes.
    """
    
    print("Removing Docker volumes.")

    volumes = get_docker_volumes() # Get all Docker volumes
    pattern = re.compile('avalanchecms_.*') # regex

    # filter volumes matching the regex
    filtered_volumes = [volume for volume in volumes if pattern.match(volume)]

    if not filtered_volumes:
        print("No volumes match the pattern: avalanchecms_.*")
        return

    remove_volumes(filtered_volumes)
    
    print("Docker volumes removed.")

@require_docker_running
def purge_docker_environment(keep_volumes=False):
    
    """
    Stops/removes containers and purges volumes unless keep_volumes is True.

    Args:
        keep_volumes (bool): Skip volume purge if True.
    """
    
    try:
        
        print("Stopping/removing Docker containers and networks.")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_dir = os.path.join(script_dir, '../../environments/local')
        original_dir = os.getcwd()

        os.chdir(env_dir) # change to docker compose dir

        # stop/remove containers and networks
        subprocess.run(["docker", "compose", "down"], check=True)
        
        print("Docker containers and networks stopped/removed.")

        if keep_volumes:
            print("Volume purge skipped.")
        else:
            purge_avalanchecms_volumes()  # purge volumes by default

    except subprocess.CalledProcessError as e:
        print(f"Failed to purge Docker environment: {e}")
        sys.exit(1)

    finally:
        os.chdir(original_dir) # return to original dir

def remove_secret_folder():
    
    """
    Removes the '.secrets' directory if it exists.
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    secrets_dir = os.path.join(script_dir, '../../.secrets')
   
    try:
        shutil.rmtree(secrets_dir) # remove the .secrets dir
        print("/.secrets folder removed successfully.")
    except FileNotFoundError:
        # .secrets dir does not exist
        print("/.secrets folder does not exist or has already been removed.")

def purge_secrets(keep_secrets=False):
    
    """
    Purges secrets unless keep_secrets is True.

    Args:
        keep_secrets (bool): Skip purge if True.
    """

    if keep_secrets:
        print("Secret removal skipped.")
    else:
        print("Removing secrets.")
        remove_secret_folder()  # remove .secrets directory
        print("Secrets removed.")


def main(keep_volumes=False, keep_secrets=False):
    
    """
    Main cleanup function, optionally keeping volumes and secrets.

    Args:
        keep_volumes (bool): Skip volume purge if True.
        keep_secrets (bool): Skip secret purge if True.
    """
    
    print("Cleaning up local development environment.")

    purge_docker_environment(keep_volumes)
    purge_secrets(keep_secrets)

    print("Local development environment cleanup is complete.")


def parse_args():
    parser = argparse.ArgumentParser(description="Avalanche CMS Cleanup.")
    parser.add_argument('-kv', '--keep-volumes', action='store_true', help='Keeps Docker volumes')
    parser.add_argument('-ks', '--keep-secrets', action='store_true', help='Keeps secrets in /.secrets')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    main(keep_volumes=args.keep_volumes, keep_secrets=args.keep_secrets)