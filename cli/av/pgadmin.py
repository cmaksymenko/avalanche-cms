import click
import webbrowser
   
@click.group(name='pgadmin')
def pgadmin_group():
    pass

@pgadmin_group.command('open')
def open_pgadmin():
    url = 'http://host.docker.internal:5050/'
    webbrowser.open(url)