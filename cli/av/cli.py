import click

from av.commands.login import login as login_command
from av.commands.logout import logout as logout_command
from av.commands.user import group as user_commands
from av.commands.keycloak import group as keycloak_commands
from av.commands.pgadmin import group as pgadmin_commands

@click.group()
def cli():
    """Avalanche CLI"""
    pass

cli.add_command(login_command)
cli.add_command(logout_command)
cli.add_command(user_commands)
cli.add_command(keycloak_commands)
cli.add_command(pgadmin_commands)

if __name__ == '__main__':
    cli()
