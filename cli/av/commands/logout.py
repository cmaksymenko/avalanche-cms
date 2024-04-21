import click
import requests
import json
from ..core.token import Token, TokenType
from .feature import Feature, FeatureSet

features = FeatureSet()

@click.command()
@Token.require(token_type=TokenType.REFRESH, alt_str="Not logged in.")
def logout(token: Token = None):
    
    try:
    
        if token is None or not hasattr(token, 'encoded_jwt'):
            raise ValueError("Token error. Log in and retry.")
        
        keycloak_base_url = 'http://localhost:8080'
        realm_name = 'avalanchecms'

        logout_url = f"{keycloak_base_url}/realms/{realm_name}/protocol/openid-connect/logout"
        payload = {'client_id': 'avalanchecli', 'refresh_token': token.encoded_jwt}
        
        try:
            
            response = requests.post(logout_url, data=payload)
            response.raise_for_status()
            
            cli_response = {"message": "User logged out.", "user_id": token.decoded_jwt.get("sub")}
            
        except requests.RequestException as e:
            
            if not features.is_set(Feature.VERBOSE_ERRORS):
                error_message = "Logout failed, cache cleared."
            else:
                error_message = f"Logout failed: {e.response.status_code} - {e.response.text}. Cache cleared."
            
            cli_response = {"error": {"message": error_message}}
        except Exception:
            cli_response = {"error": {"message": "Logout failed, cache cleared."}}
        finally:
            Token.clear()

        click.echo(json.dumps(cli_response, indent=2))
        
    except Exception as e:
        Token.handle_error(e)