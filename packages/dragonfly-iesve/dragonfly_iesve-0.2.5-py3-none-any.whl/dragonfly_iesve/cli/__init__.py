"""dragonfly-iesve commands which will be added to dragonfly command line interface."""
import click
from dragonfly.cli import main

from .translate import translate


# command group for all iesve extension commands.
@click.group(help='dragonfly iesve commands.')
@click.version_option()
def iesve():
    pass


iesve.add_command(translate)

# add ies sub-commands to honeybee CLI
main.add_command(iesve)
