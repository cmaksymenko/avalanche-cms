import click

from av.commands.login import login as login_command
from av.commands.logout import logout as logout_command
from av.commands.session import group as session_commands
from av.commands.keycloak import group as keycloak_commands
from av.commands.pgadmin import group as pgadmin_commands
from av.commands.feature import group as feature_commands

@click.group()
def cli():
    """Avalanche CLI"""
    pass

cli.add_command(login_command)
cli.add_command(logout_command)
cli.add_command(session_commands)
cli.add_command(keycloak_commands)
cli.add_command(pgadmin_commands)
cli.add_command(feature_commands)

if __name__ == '__main__':
    cli()
