import click
import webbrowser
  
@click.group(name='keycloak')
def group():
    pass

@group.command('open')
def keycloak_open():
    url = 'http://host.docker.internal:8080/'
    webbrowser.open(url)