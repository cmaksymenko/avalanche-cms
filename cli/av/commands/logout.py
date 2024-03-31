import click
from ..core.token import require_token

@click.command()
@require_token
def logout():
    click.echo("logout mock")
    pass