import click
import json
from ..core.token import Token, TokenType, require_token

@click.command()
@require_token
def logout():    
    try:
        
        token = Token.from_type(TokenType.REFRESH)
        
        # TODO: logout user
        
        cli_response = {"message": "User logged out.", "user_id": token.decoded_jwt.get("sub")}
        
    except ValueError as e:
        cli_response = {"error": {"message": str(e)}}
    except Exception:
        cli_response = {"error": {"message": "Log out failed, cache cleared."}}
    finally:
        Token.clear()

    click.echo(json.dumps(cli_response, indent=2))
