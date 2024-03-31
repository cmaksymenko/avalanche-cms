import click
import json
from ..core.token import Token, TokenType, require_token
 
@click.group(name='user')
def group():
    pass

@group.command('show')
@require_token
def show_user():
    
    try:

        id_token = Token.from_type(TokenType.ID)
        if not id_token:
            raise ValueError("No ID token found.")
        
        cli_response = {
            "user": {
                "id": id_token.decoded_jwt.get("sub"),
                "username": id_token.decoded_jwt.get("preferred_username"),
                "email": id_token.decoded_jwt.get("email"),
                "name": id_token.decoded_jwt.get("name")
            },
            "message": "User is logged in."
        }
        
    except Exception as e:
        
        cli_response = {
            "error": {
                "message": "No user is logged in.",
            }
        }

    click.echo(json.dumps(cli_response, indent=2)) 

def init_user_commands(cli):
    cli.add_command(show_user)