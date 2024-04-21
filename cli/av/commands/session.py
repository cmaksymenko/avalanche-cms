import click
import json
from ..core.token import Token, TokenType
import humanize
import datetime
import math
from .feature import Feature, FeatureSet

features = FeatureSet()
 
@click.group(name='session')
def group():
    pass

def adaptive_naturaldelta(seconds):
    
    threshold = 120
    if seconds < threshold:
        return f"{math.floor(seconds)} seconds"
    else:
        return humanize.naturaldelta(datetime.timedelta(seconds=math.floor(seconds)))
   
@group.command('show')
@Token.require(token_type=TokenType.REFRESH, suppress_refresh=True)
def session_show(token: Token = None):
    
    try:
    
        if token is None:
            raise ValueError("Token error. Log in and retry.")
        
        tokens = {
            "access": Token.from_type(TokenType.ACCESS),
            "refresh": token
        }
        
        token_details = {}
        
        for token_type, token in tokens.items():
            
            exp_secs = token.get_expiration_secs()
            
            details = {
                "status": "active" if exp_secs > 0 else "expired",
                "expires_at_utc": token.expiration.isoformat(),
            }
            
            if exp_secs > 0:
                details["time_until_expiration"] = adaptive_naturaldelta(exp_secs)
                if features.is_set(Feature.SHOW_TOKEN):
                    details["token"] = token.encoded_jwt

            token_details[f"{token_type}_token"] = details
            
        session_active = tokens["refresh"].get_expiration_secs() > 0
            
        user_info = {key: tokens["access"].decoded_jwt.get(key) for key in ["sub", "preferred_username", "email", "name"]}
        user_info = {"id": user_info.pop("sub"), "username": user_info.pop("preferred_username"), **user_info}
        
        session_details = {
            "active": session_active,
            "id": tokens["refresh"].decoded_jwt.get("sid"),
            "user": user_info,
            "tokens": token_details
        }
        
        cli_response = {"session": session_details, "message": "Session active."} 
        click.echo(json.dumps(cli_response, indent=2))
        
    except Exception as e:
        Token.handle_error(e, "Session inactive. Log in and retry.")