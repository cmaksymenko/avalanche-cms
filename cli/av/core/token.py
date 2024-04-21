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
    
    def is_about_to_expire(self, threshold_secs=20):
        delta = self.expiration - datetime.datetime.now(timezone.utc)
        return delta < datetime.timedelta(seconds=threshold_secs), int(delta.total_seconds())
    
    def sec_until_expired(self):
        delta = self.expiration - datetime.datetime.now(timezone.utc)
        return delta.total_seconds()
    
    def save(self):
        app_name = "avalanchecli"
        base_key = f"token_{self.token_type.name}"
        keyring.set_password(app_name, f"{base_key}_jwt", self.encoded_jwt)
        
    def get_expiration_secs(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = self.expiration - now
        return delta.total_seconds()
        
    @staticmethod
    def decode_jwt(encoded_jwt):
        return jwt.decode(encoded_jwt, options={"verify_signature": False})
        
    @staticmethod
    def get_expiration(decoded_jwt):
        return datetime.datetime.fromtimestamp(decoded_jwt.get("exp"), tz=timezone.utc)
             
    @classmethod
    def from_jwt(cls, encoded_jwt, token_type: TokenType, save=False):
        
        obj = cls(encoded_jwt, token_type)
        
        if save:
            obj.save()
            
        return obj
        
    @classmethod
    def from_type(cls, token_type: TokenType, alt_str=None):
        
        app_name = "avalanchecli"
        base_key = f"token_{token_type.name}"
        
        try:
            
            encoded_jwt = keyring.get_password(app_name, f"{base_key}_jwt")
            
            if encoded_jwt is None:
                raise ValueError("Token data is missing.")
            
        except ValueError:
            cls.clear()
            raise ValueError(alt_str if alt_str is not None else "Token data incorrect. Log in and retry.")
        
        return cls(encoded_jwt, token_type)
    
    @classmethod
    def from_response(cls, response, save=False):
        
        if not isinstance(response, requests.Response) or response.headers.get('Content-Type') != 'application/json':
            raise ValueError("Response should be from a JSON 'requests.post'.")

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
            
    @classmethod
    def refresh(cls):
        
        refresh_token = Token.from_type(TokenType.REFRESH)
        
        client_id = 'avalanchecli'
        realm_name = 'avalanchecms'
        keycloak_url = 'http://localhost:8080'

        token_endpoint = f"{keycloak_url}/realms/{realm_name}/protocol/openid-connect/token"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        payload = {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.encoded_jwt
        }

        response = requests.post(token_endpoint, headers=headers, data=payload)
        if response.status_code == 200:
            
            _, access_token, _ = Token.from_response(response, save=True)
            return (access_token is not None)

        else:
            raise ValueError("Token refresh failed.")

    @staticmethod
    def require(token_type=TokenType.ACCESS, suppress_refresh=False, pass_type=None, alt_str=None):
        def decorator(func):
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):

                try:
                    
                    token = Token.from_type(token_type=token_type, alt_str=alt_str)
                    
                    if token is None and token_type != TokenType.REFRESH:
                        refresh_token = Token.from_type(TokenType.REFRESH)
                        if refresh_token and not refresh_token.is_expired() and not suppress_refresh:
                            Token.refresh()
                            token = Token.from_type(token_type)
                   
                    if token and token.is_about_to_expire() and not suppress_refresh:
                        Token.refresh()
                        token = Token.from_type(token_type)
                            
                    if token is None or token.is_expired():
                        raise ValueError(alt_str if alt_str is not None else "Token invalid. Log in and retry.")
                    
                except Exception as e:
                    Token.handle_error(e)
                   
                if pass_type and pass_type != token_type:
                    token = Token.from_type(pass_type)
                    
                kwargs['token'] = token
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def handle_error(exception, alt_str=None):
        
        Token.clear()
        
        if isinstance(exception, ValueError):
            error_message = str(exception)
        else:
            error_message = alt_str if alt_str is not None else "Error occurred. Log in and retry."
        
        cli_response = {"error": {"message": error_message}}
        click.echo(json.dumps(cli_response, indent=2))
        
        sys.exit(1)