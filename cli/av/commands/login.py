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
from urllib.parse import parse_qs, urlparse
import click
import requests
from ..core.token import Token

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
                    self.wfile.write(b"Login successful. Please close this window.")
                    code_ready_event.set()
                    threading.Thread(target=httpd.shutdown).start()
                    
        def log_message(self, format, *args):
            pass
                    
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
@click.option('-q', '--quiet', is_flag=True, help="Enable quiet mode.")
def login(quiet=False):
    
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
    
    if not quiet:
        click.echo("Opening authorization URL in browser...")
        click.echo(f"If it doesn't open, visit: {authorization_url}")    
        
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
        
        _, access_token, _ = Token.from_response(response, save=True)
        
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

