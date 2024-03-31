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
        
        user_info = {"id": id_token.decoded_jwt.get("sub"),
                     "username": id_token.decoded_jwt.get("preferred_username"),
                     "email": id_token.decoded_jwt.get("email"),
                     "name": id_token.decoded_jwt.get("name")}
        
        cli_response = {"user": user_info, "message": "User logged in."}
        
    except Exception as e:
        cli_response = {"error": {"message": "User not logged in."}}

    click.echo(json.dumps(cli_response, indent=2))
