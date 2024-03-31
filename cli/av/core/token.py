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

    def __init__(self, encoded_jwt, token_type, decoded_jwt, expiration):
        self.encoded_jwt = encoded_jwt
        self.token_type = token_type
        self.decoded_jwt = decoded_jwt
        self.expiration = expiration
        
    def is_expired(self):
        return datetime.datetime.now(timezone.utc) > self.expiration
    
    def sec_until_expired(self):
        delta = self.expiration - datetime.datetime.now(timezone.utc)
        return delta.total_seconds()
    
    def save(self):

        app_name = "avalanchecli"
        base_key = f"token_{self.token_type.name}"

        keyring.set_password(app_name, f"{base_key}_jwt", self.encoded_jwt)
        keyring.set_password(app_name, f"{base_key}_jwt_decoded", json.dumps(self.decoded_jwt))
        keyring.set_password(app_name, f"{base_key}_exp", self.expiration.isoformat())
        
    @classmethod
    def from_jwt(cls, encoded_jwt, token_type: TokenType, save=False):
        
        decoded_jwt = jwt.decode(encoded_jwt, options={"verify_signature": False})
        expiration = datetime.datetime.fromtimestamp(decoded_jwt.get("exp"), tz=timezone.utc)
        
        obj = cls(encoded_jwt, token_type, decoded_jwt, expiration)
        
        if save:
            obj.save()
        
        return obj
        
    @classmethod
    def from_type(cls, token_type: TokenType):

        app_name = "avalanchecli"
        base_key = f"Token_{token_type.name}"

        encoded_jwt = keyring.get_password(app_name, f"{base_key}_jwt")

        if encoded_jwt is None:
            raise ValueError(f"Missing token data for {token_type.name} in keyring.")
        
        decoded_jwt = jwt.decode(encoded_jwt, options={"verify_signature": False})
        expiration = datetime.datetime.fromtimestamp(decoded_jwt.get("exp"), tz=timezone.utc)
       
        return cls(encoded_jwt, token_type, decoded_jwt, expiration)
    
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
                keyring.delete_password(app_name, f"{base_key}_jwt_decoded")
                keyring.delete_password(app_name, f"{base_key}_exp")
            except Exception as e:
                pass

def require_token(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:

            refresh_token = Token.from_type(TokenType.REFRESH)

            if not refresh_token or refresh_token.is_expired():
                raise ValueError("Refresh token is missing or expired.")

        except Exception as e:

            Token.clear()
            
            click.echo("Please log in via 'av login'", err=True)
            sys.exit(1)
        
        return func(*args, **kwargs)
    return wrapper