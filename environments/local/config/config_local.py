import os
import urllib.parse

SERVER_MODE = True

AUTHENTICATION_SOURCES = ['oauth2']

# Enable internal auth if PGADMIN_ENABLE_INTERNAL_AUTH is set
if os.getenv('PGADMIN_ENABLE_INTERNAL_AUTH', '').lower() in ['true', '1', 'on', 'yes', 'y', 'enabled']:
    AUTHENTICATION_SOURCES.append('internal')
    
MFA_ENABLED = False
OAUTH2_AUTO_CREATE_USER = True
MASTER_PASSWORD_REQUIRED = False
MAX_LOGIN_ATTEMPTS = 0
AUTO_DISCOVER_SERVERS = False

USER_INACTIVITY_TIMEOUT = 900
OVERRIDE_USER_INACTIVITY_TIMEOUT = True

OAUTH2_CONFIG = [{
    
    'OAUTH2_NAME': 'Keycloak',
    'OAUTH2_DISPLAY_NAME': 'Keycloak',
    'OAUTH2_CLIENT_ID': 'pgadmin',
    
    'OAUTH2_TOKEN_URL': 'http://host.docker.internal:8080/realms/avalanchecms/protocol/openid-connect/token',
    'OAUTH2_AUTHORIZATION_URL': 'http://host.docker.internal:8080/realms/avalanchecms/protocol/openid-connect/auth',
    'OAUTH2_SERVER_METADATA_URL': 'http://host.docker.internal:8080/realms/avalanchecms/.well-known/openid-configuration',
    'OAUTH2_USERINFO_ENDPOINT': 'http://host.docker.internal:8080/realms/avalanchecms/protocol/openid-connect/userinfo',
    'OAUTH2_API_BASE_URL': 'http://host.docker.internal:8080/realms/avalanchecms',
    
    'OAUTH2_SCOPE': 'openid email profile',
    'OAUTH2_AUTO_CREATE_USER': False,
    'OAUTH2_SSL_CERT_VERIFICATION': False,
    
    'OAUTH2_ADDITIONAL_CLAIMS': { # Checked for mapping in the ID token
        'roles': [ "admin" ]
    }    
}]

# Add OAUTH2_CLIENT_SECRET only if PGADMIN_OAUTH2_CLIENT_SECRET is set
if 'PGADMIN_OAUTH2_CLIENT_SECRET' in os.environ:
    OAUTH2_CONFIG[0]['OAUTH2_CLIENT_SECRET'] = urllib.parse.quote(os.environ['PGADMIN_OAUTH2_CLIENT_SECRET'].strip())

#import logging
#FILE_LOG_LEVEL = logging.DEBUG
#CONSOLE_LOG_LEVEL = logging.DEBUG
#DEBUG = True
