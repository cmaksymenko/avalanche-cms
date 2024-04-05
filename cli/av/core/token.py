from enum import Enum
import datetime
import jwt
from datetime import timezone
import keyring
import json
import requests
import functools
import sys
import click

class TokenType(Enum):
    ID = "id"
    ACCESS = "access"
    REFRESH = "refresh"

class Token:

    def __init__(self, encoded_jwt, token_type, decoded_jwt=None, expiration=None):
        self.encoded_jwt = encoded_jwt
        self.token_type = token_type
        self.decoded_jwt = decoded_jwt if decoded_jwt else self.decode_jwt(encoded_jwt)
        self.expiration = expiration if expiration else self.get_expiration(self.decoded_jwt)
        
    def is_expired(self):
        return datetime.datetime.now(timezone.utc) > self.expiration
    
    def sec_until_expired(self):
        delta = self.expiration - datetime.datetime.now(timezone.utc)
        return delta.total_seconds()
    
    def save(self):
        
        app_name = "avalanchecli"
        base_key = f"token_{self.token_type.name}"

        keyring.set_password(app_name, f"{base_key}_jwt", self.encoded_jwt)
        
    @staticmethod
    def decode_jwt(encoded_jwt):
        return jwt.decode(encoded_jwt, options={"verify_signature": False})
        
    @staticmethod
    def get_expiration(decoded_jwt):
        return datetime.datetime.fromtimestamp(decoded_jwt.get("exp"), tz=timezone.utc)
    
    def get_expiration_secs(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = self.expiration - now
        return delta.total_seconds()
           
    @classmethod
    def from_jwt(cls, encoded_jwt, token_type: TokenType, save=False):
        
        obj = cls(encoded_jwt, token_type)
        
        if save:
            obj.save()
            
        return obj
        
    @classmethod
    def from_type(cls, token_type: TokenType):
        
        app_name = "avalanchecli"
        base_key = f"token_{token_type.name}"
        
        try:
            
            encoded_jwt = keyring.get_password(app_name, f"{base_key}_jwt")
            
            if encoded_jwt is None:
                raise ValueError(f"Missing token data for {token_type.name} in keyring.")
            
        except ValueError:
            cls.clear()
            raise ValueError(f"Token data for {token_type.name} is missing or corrupt in keyring. Please reauthenticate.")
        
        return cls(encoded_jwt, token_type)
    
    @classmethod
    def from_response(cls, response, save=False):
        
        if not isinstance(response, requests.Response) or response.headers.get('Content-Type') != 'application/json':
            raise ValueError("Response must be from a JSON-based requests.post call")

        response_data = response.json()
        
        identity_token = cls.from_jwt(response_data.get("id_token"), TokenType.ID, save=save)
        access_token = cls.from_jwt(response_data.get("access_token"), TokenType.ACCESS, save=save)
        refresh_token = cls.from_jwt(response_data.get("refresh_token"), TokenType.REFRESH, save=save)

        return identity_token, access_token, refresh_token
    
    @classmethod
    def clear(cls):
        app_name = "avalanchecli"
        for token_type in TokenType:
            try:
                base_key = f"token_{token_type.name}"
                keyring.delete_password(app_name, f"{base_key}_jwt")
            except Exception as e:
                pass

def require_token(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:

            refresh_token = Token.from_type(TokenType.REFRESH)
           
            if refresh_token is None or refresh_token.is_expired() == True:
                raise ValueError("Refresh token is missing or expired.")

        except Exception as e:

            Token.clear()
            
            cli_response = {
                "error": {
                    "message": "Token missing. Please log in with 'av login'.",
                }
            }
            
            click.echo(json.dumps(cli_response, indent=2))
            sys.exit(1)
        
        return func(*args, **kwargs)
    return wrapper