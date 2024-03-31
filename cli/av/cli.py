import click

import av.auth
import av.user
import av.keycloak
import av.pgadmin

@click.group()
def cli():
    """Avalanche CLI"""
    pass

cli.add_command(av.auth.login)
cli.add_command(av.auth.logout)
cli.add_command(av.user.group)
cli.add_command(av.keycloak.group)
cli.add_command(av.pgadmin.group)

if __name__ == '__main__':
    cli()
