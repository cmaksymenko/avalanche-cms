import base64
import hashlib
import http.server
import json
import queue
import secrets
import socketserver
import threading
import time
import webbrowser
from urllib.parse import urlparse, parse_qs
from uuid import uuid4
import click
import requests
from datetime import datetime
from ..core.token import Token

def display_time_until_expiration(exp_timestamp):
    
    current_timestamp = datetime.now().timestamp()

    remaining_time_seconds = exp_timestamp - current_timestamp
    
    if remaining_time_seconds <= 0:
        return "The token has already expired."
    
    remaining_minutes, remaining_seconds = divmod(remaining_time_seconds, 60)
    formatted_remaining_time = f"{int(remaining_minutes)}min {int(remaining_seconds)}s"
    return formatted_remaining_time

def decode_jwt_payload(token):
    # Split the token into its parts
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT token")

    # Base64 decode the payload part
    payload = parts[1]
    # Add necessary padding
    payload += '=' * (-len(payload) % 4)
    decoded_payload = base64.urlsafe_b64decode(payload)

    # Convert the decoded payload into a dictionary
    payload_dict = json.loads(decoded_payload)
    
    return payload_dict

def generate_code_verifier_and_challenge():
    
    code_verifier = secrets.token_urlsafe(32).encode('utf-8')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier).digest()).rstrip(b'=')
    
    return code_verifier.decode('utf-8'), code_challenge.decode('utf-8')

def start_auth_server(server_port, code_queue, code_ready_event):
    
    class RedirectHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if urlparse(self.path).path.endswith('/callback'):
                query_components = parse_qs(urlparse(self.path).query)
                code = query_components.get("code", None)
                if code:
                    code_queue.put(code[0])
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"Authentication successful. You can close this window.")
                    code_ready_event.set()
                    threading.Thread(target=httpd.shutdown).start()
                    
    httpd = socketserver.TCPServer(("", server_port), RedirectHandler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return httpd, server_thread

def wait_for_code(code_ready_event, code_queue, timeout=300):
    
    start_time = time.time()
    
    while not code_ready_event.is_set() and (time.time() - start_time) < timeout:
        try:
            code_ready_event.wait(timeout=1)
        except KeyboardInterrupt:
            break
        
    if code_ready_event.is_set():
        return code_queue.get()
    
    return None

@click.command()
def login():
    
    client_id = 'avalanchecli'
    realm = 'avalanchecms'
    keycloak_url = 'http://localhost:8080'
    server_port = 49200
    redirect_uri = f"http://localhost:{server_port}/avalanchecli/oidc/pkce/callback"

    code_verifier, code_challenge = generate_code_verifier_and_challenge()
    
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'openid profile email',
        'redirect_uri': redirect_uri,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    
    authorization_endpoint = f'{keycloak_url}/realms/{realm}/protocol/openid-connect/auth'
    token_endpoint = f'{keycloak_url}/realms/{realm}/protocol/openid-connect/token'
    authorization_url = requests.Request('GET', authorization_endpoint, params=params).prepare().url

    code_queue = queue.Queue()
    code_ready_event = threading.Event()
    httpd, server_thread = start_auth_server(server_port, code_queue, code_ready_event)

    webbrowser.open_new(authorization_url)

    authorization_code = wait_for_code(code_ready_event, code_queue)

    if authorization_code:
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'code': authorization_code,
            'code_verifier': code_verifier
        }
        response = requests.post(token_endpoint, data=data)
        
        click.echo(f"URL: {response.url}")
        click.echo(f"Status Code: {response.status_code}")
        click.echo("Response Headers:")
        for key, value in response.headers.items():
            click.echo(f"  {key}: {value}")
        click.echo("Request Headers:")
        for key, value in response.request.headers.items():
            click.echo(f"  {key}: {value}")
        click.echo(f"Response Body:\n{response.text}")    
        
        id_token, access_token, refresh_token = Token.from_response(response, save=True)
        
        click.echo(f"Identity Token valid for {id_token.sec_until_expired()}s: {json.dumps(id_token.decoded_jwt, indent=2)}")
        click.echo(f"Access Token valid for {access_token.sec_until_expired()}s: {json.dumps(access_token.decoded_jwt, indent=2)}")
        click.echo(f"Refresh Token valid for {refresh_token.sec_until_expired()}s: {json.dumps(refresh_token.decoded_jwt, indent=2)}")
        
        user_info = {"id": access_token.decoded_jwt.get("sub"),
                     "username": access_token.decoded_jwt.get("preferred_username"),
                     "email": access_token.decoded_jwt.get("email"),
                     "name": access_token.decoded_jwt.get("name")}
        
        cli_response = {
            "user": user_info,
            "message": "Login successful."
        }
        
    else:
        
        cli_response = {
            "error": {
                "message": "Login failed."
            }
        }
        
    httpd.shutdown()
    server_thread.join()
        
    click.echo(json.dumps(cli_response, indent=2))

'''        
@click.command()
def login():
    
    authorization_code = None  # This will hold the authorization code
    
    code_queue = queue.Queue()
    code_ready_event = threading.Event()  # Event to signal when the code is ready
    
    client_id = 'avalanchecli'
    realm = 'avalanchecms'
    keycloak_url = 'http://localhost:8080'
    authorization_endpoint = f'{keycloak_url}/realms/{realm}/protocol/openid-connect/auth'
    token_endpoint = f'{keycloak_url}/realms/{realm}/protocol/openid-connect/token'
    
    code_verifier = generate_code_verifier()
    click.echo(f"code_verifier: {code_verifier}")
    
    code_challenge = generate_code_challenge(code_verifier)
    click.echo(f"code_challenge: {code_challenge}")
    
    server_port = 49200 # use a high static port for now
    click.echo(f"Server port: {server_port}")
    
    redirect_uri = f"http://localhost:{server_port}/avalanchecli/oidc/pkce/callback"
    click.echo(f"Redirect URI: {redirect_uri}")
    
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'openid profile email',
        'redirect_uri': redirect_uri,
        'code_challenge': code_challenge.decode('utf-8'),
        'code_challenge_method': 'S256',
    }
    click.echo(f"params: {params}")

    authorization_url = requests.Request('GET', authorization_endpoint, params=params).prepare().url
    click.echo(f"authorization_url: {authorization_url}")
    
    class RedirectHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if urlparse(self.path).path == '/avalanchecli/oidc/pkce/callback':
                
                query_components = parse_qs(urlparse(self.path).query)
                code = query_components.get("code", None)

                if code:
                    global authorization_code
                    authorization_code = code[0]  # Extract the authorization code
                    code_queue.put(authorization_code)  # Put the code in the queue
                    click.echo(f"Authorization code: {authorization_code}")
                    # Respond to the browser
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"Authentication successful. You can close this window.")
                    
                    code_ready_event.set()  # Signal that the code is ready
                    
                    # Shutdown the server on a different thread
                    click.echo("Initiating server shutdown...")
                    threading.Thread(target=httpd.shutdown).start()
                   
    # Server setup
    httpd = socketserver.TCPServer(("", server_port), RedirectHandler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    click.echo(f"Server started at http://localhost:{server_port}")
    
    try:
        click.echo("Opening the authorization URL in your browser...")
        click.echo(f"If it doesn't show up, open manually: {authorization_url}")
        webbrowser.open_new(authorization_url)
        
        # Define a timeout for user action (e.g., 3 minutes)
        timeout = 300 # seconds
        start_time = time.time()  # Record the start time        
                       
        # Wait for the authorization code or until timeout
        while not code_ready_event.is_set() and (time.time() - start_time) < timeout:            
            
            try:
                # Wait for a short period to allow interrupt
                code_ready_event.wait(timeout=1)
            except KeyboardInterrupt:
                click.echo("Interrupted by user. Exiting...")
                break  # Exit the loop if CTRL+C is pressed

        if code_ready_event.is_set():
            # Only attempt to get from the queue if the event was set
            authorization_code = code_queue.get()  
            click.echo(f"Received authorization code: {authorization_code}")
        elif (time.time() - start_time) >= timeout:
            # If we reached here because of a timeout
            click.echo("Timed out waiting for authorization. Please try again.")
        else:
            # If the loop exited for any other reason (e.g., user interruption)
            click.echo("Authorization process was not completed.")
        
    except Exception as e:
        # Handle any other exception that may occur
        click.echo(f"An error occurred: {e}") 
        
    finally:
        # Whether interrupted or completed, ensure the server is shut down gracefully
        if 'httpd' in locals() or 'httpd' in globals():
            httpd.shutdown()
            click.echo("Shutting down the server...")

        # Ensure the server thread has ended
        if 'server_thread' in locals() or 'server_thread' in globals():
            server_thread.join()
            click.echo("Server thread has been joined successfully.")
            
    cli_response = None           
    
    if authorization_code != None:

        # Exchange the authorization code for an access token
        data = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'code': authorization_code,
            'code_verifier': code_verifier.decode('utf-8'),
        }
        response = requests.post(token_endpoint, data=data)
        
        click.echo(f"URL: {response.url}")
        click.echo(f"Status Code: {response.status_code}")
        click.echo("Response Headers:")
        for key, value in response.headers.items():
            click.echo(f"  {key}: {value}")
        click.echo("Request Headers:")
        for key, value in response.request.headers.items():
            click.echo(f"  {key}: {value}")
        click.echo(f"Response Body:\n{response.text}")    
        
        id_token, access_token, refresh_token = Token.from_response(response, save=True)
        
        click.echo(f"Identity Token valid for {id_token.sec_until_expired()}s: {json.dumps(id_token.decoded_jwt, indent=2)}")
        click.echo(f"Access Token valid for {access_token.sec_until_expired()}s: {json.dumps(access_token.decoded_jwt, indent=2)}")
        click.echo(f"Refresh Token valid for {refresh_token.sec_until_expired()}s: {json.dumps(refresh_token.decoded_jwt, indent=2)}")
        
        cli_response = {
            "user": {
                "id": id_token.decoded_jwt.get("sub"),
                "username": id_token.decoded_jwt.get("preferred_username"),
                "email": id_token.decoded_jwt.get("email"),
                "name": id_token.decoded_jwt.get("name")
            },
            "message": "Login successful."
        }        
        
    else:
        
        cli_response = {
            "error": {
                "message": "Login failed."
            }
        }
        
    click.echo(json.dumps(cli_response, indent=2))
'''
