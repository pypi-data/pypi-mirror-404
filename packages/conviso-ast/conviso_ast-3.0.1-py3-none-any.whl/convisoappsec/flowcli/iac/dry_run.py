import click
import click_log
import json
import traceback
import sys
from convisoappsec.common.box import ContainerWrapper
from convisoappsec.flowcli import help_option
from convisoappsec.flowcli.context import pass_flow_context
from convisoappsec.logger import LOGGER
from convisoappsec.flowcli.common import on_http_error
from convisoappsec.common.cleaner import Cleaner

def execute_dry_run(flow_context, repository_dir, scanner_timeout):
    REQUIRED_CODEBASE_PATH = '/code'
    IAC_IMAGE_NAME = 'iac_scanner_checkov'
    IAC_SCAN_FILENAME = '/{}.json'.format(IAC_IMAGE_NAME)
    containers_map = {
        IAC_IMAGE_NAME: {
            'repository_dir': repository_dir,
            'repository_name': IAC_IMAGE_NAME,
            'tag': 'unstable',
            'command': [
                '-c', REQUIRED_CODEBASE_PATH,
                '-o', IAC_SCAN_FILENAME,
            ],
        },
    }

    conviso_rest_api = flow_context.create_conviso_rest_api_client()
    token = conviso_rest_api.docker_registry.get_sast_token()
    
    LOGGER.info('💬 Preparing Environment...')
    scanners_wrapper = ContainerWrapper(
        token=token,
        containers_map=containers_map,
        logger=LOGGER,
        timeout=scanner_timeout
    )

    LOGGER.info('💬 Starting IaC...')
    scanners_wrapper.run()

    results_list = []
    for r in scanners_wrapper.scanners:
        report_filepath = r.results
        if report_filepath:
             try:
                with open(report_filepath, 'r') as f:
                    results_list.append(json.load(f))
             except Exception as e:
                click.echo(f"Error reading result file {report_filepath}: {e}", file=sys.stderr)

    if len(results_list) == 1:
        return results_list[0]
    return results_list

@click.command(name='dry-run')
@click.option(
    '-r', '--repository-dir', default=".", show_default=True,
    type=click.Path(exists=True, resolve_path=True), required=False,
    help="The source code repository directory."
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
def dry_run(flow_context, repository_dir, scanner_timeout, cleanup):
    """
    Perform a dry-run IAC analysis.
    Checks API Key, runs the scan, and outputs the results in JSON format to stdout.
    Does NOT create assets or deploys on Conviso Platform.
    """
    try:
        results = execute_dry_run(flow_context, repository_dir, scanner_timeout)

        if results:
            print(json.dumps(results, indent=2))
        else:
            print(json.dumps({}, indent=2))

        if cleanup:
            LOGGER.info("🧹 Cleaning up ...")
            cleaner = Cleaner()
            cleaner.cleanup()

    except Exception as e:
        on_http_error(e)
        sys.exit(1)
