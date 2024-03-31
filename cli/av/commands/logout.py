import click
import requests
import json
from ..core.token import Token, TokenType, require_token

@click.command()
@require_token
def logout():    
    
    token = Token.from_type(TokenType.REFRESH)

    keycloak_base_url = 'http://localhost:8080'
    realm_name = 'avalanchecms'

    logout_url = f"{keycloak_base_url}/realms/{realm_name}/protocol/openid-connect/logout"
    payload = {'client_id': 'avalanchecli', 'refresh_token': token.encoded_jwt}
    
    try:
        
        response = requests.post(logout_url, data=payload)
        response.raise_for_status()
        
        cli_response = {"message": "User logged out.", "user_id": token.decoded_jwt.get("sub")}
        
    except requests.RequestException as e:
        error_message = f"Logout failed, {e.response.status_code} - {e.response.text}, cache cleared."
        cli_response = {"error": {"message": error_message}}
    except Exception:
        cli_response = {"error": {"message": "Log out failed, cache cleared."}}
    finally:
        Token.clear()

    click.echo(json.dumps(cli_response, indent=2))