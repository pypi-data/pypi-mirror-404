import click
import json
import traceback
import sys
from convisoappsec.flowcli import help_option
from convisoappsec.flowcli.context import pass_flow_context
from convisoappsec.logger import LOGGER
from convisoappsec.flowcli.common import on_http_error
from convisoappsec.common.cleaner import Cleaner
from convisoappsec.sast.sastbox import SASTBox
from convisoappsec.flowcli.sast.dry_run import execute_dry_run as execute_sast_dry_run
from convisoappsec.flowcli.sca.dry_run import execute_dry_run as execute_sca_dry_run
from convisoappsec.flowcli.iac.dry_run import execute_dry_run as execute_iac_dry_run

@click.command(name='dry-run')
@click.option(
    "-s", "--start-commit", required=False,
    help="If no value is set so the empty tree hash commit is used."
)
@click.option(
    "-e", "--end-commit", required=False,
    help="If no value is set so the HEAD commit from the current branch is used"
)
@click.option(
    "-r", "--repository-dir", default=".", show_default=True,
    type=click.Path(exists=True, resolve_path=True), required=False,
    help="The source code repository directory."
)
@click.option(
    "--sastbox-registry", default="", required=False, hidden=True,
    envvar=("CONVISO_SASTBOX_REGISTRY", "FLOW_SASTBOX_REGISTRY"),
)
@click.option(
    "--sastbox-repository-name", default="", required=False, hidden=True,
    envvar=("CONVISO_SASTBOX_REPOSITORY_NAME", "FLOW_SASTBOX_REPOSITORY_NAME"),
)
@click.option(
    "--sastbox-tag", default=SASTBox.DEFAULT_TAG, required=False, hidden=True,
    envvar=("CONVISO_SASTBOX_TAG", "FLOW_SASTBOX_TAG"),
)
@click.option(
    "--sastbox-skip-login/--sastbox-no-skip-login", default=False, required=False, hidden=True,
    envvar=("CONVISO_SASTBOX_SKIP_LOGIN", "FLOW_SASTBOX_SKIP_LOGIN"),
)
@click.option(
    "--custom-sca-tags", hidden=True, required=False, multiple=True, type=(str, str),
    help="It should be passed as <repository_name> <image_tag>."
)
@click.option(
    "--scanner-timeout", hidden=True, required=False, default=7200, type=int,
    help="Set timeout for each scanner"
)
@click.option(
    '--cleanup', default=False, is_flag=True, show_default=True,
    help="Clean up system resources."
)
@help_option
@pass_flow_context
def dry_run(flow_context, end_commit, start_commit, repository_dir,
            sastbox_registry, sastbox_repository_name, sastbox_tag, sastbox_skip_login,
            custom_sca_tags, scanner_timeout, cleanup):
    """
    Perform a dry-run AST analysis (SAST, SCA, IaC).
    Checks API Key, runs the scans, and outputs the results in JSON format to stdout.
    Does NOT create assets or deploys on Conviso Platform.
    """
    try:
        results = {}

        # Run SAST
        sast_results = execute_sast_dry_run(
            flow_context, end_commit, start_commit, repository_dir,
            sastbox_registry, sastbox_repository_name, sastbox_tag, sastbox_skip_login
        )
        results['sast'] = sast_results

        # Run SCA
        sca_results = execute_sca_dry_run(
            flow_context, repository_dir, custom_sca_tags, scanner_timeout
        )
        results['sca'] = sca_results

        # Run IaC
        iac_results = execute_iac_dry_run(
            flow_context, repository_dir, scanner_timeout
        )
        results['iac'] = iac_results

        print(json.dumps(results, indent=2))

        if cleanup:
            LOGGER.info("🧹 Cleaning up ...")
            cleaner = Cleaner()
            cleaner.cleanup()

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        on_http_error(e)
        sys.exit(1)
