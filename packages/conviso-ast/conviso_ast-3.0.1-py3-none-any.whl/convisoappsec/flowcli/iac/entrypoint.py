import click

from convisoappsec.flowcli import help_option
from .run import run
from .dry_run import dry_run


@click.group()
@help_option
def iac():
    pass


iac.add_command(run)
iac.add_command(dry_run)

iac.epilog = '''
  Run flow iac COMMAND --help for more information on a command.
'''
