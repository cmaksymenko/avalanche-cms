import click
import webbrowser
   
@click.group(name='keycloak')
def keycloak_group():
    pass

@keycloak_group.command('open')
def open_keycloak():
    url = 'http://host.docker.internal:8080/'
    webbrowser.open(url)
