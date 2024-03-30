import click
from av.auth import login
from av.keycloak import keycloak_group
from av.pgadmin import pgadmin_group

@click.group()
def cli():
    """Avalanche CLI"""
    pass

cli.add_command(login)
cli.add_command(keycloak_group)
cli.add_command(pgadmin_group)

if __name__ == '__main__':
    cli()
