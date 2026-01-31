import click

from convisoappsec.flowcli import help_option
from .run import run
from .dry_run import dry_run


@click.group()
@help_option
def sast():
    pass


sast.add_command(run)
sast.add_command(dry_run)

sast.epilog = '''
  Run flow sast COMMAND --help for more information on a command.
'''
