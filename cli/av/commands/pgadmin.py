import click
import webbrowser
  
@click.group(name='pgadmin')
def group():
    pass

@group.command('open')
def pgadmin_open():
    url = 'http://host.docker.internal:5050/'
    webbrowser.open(url)