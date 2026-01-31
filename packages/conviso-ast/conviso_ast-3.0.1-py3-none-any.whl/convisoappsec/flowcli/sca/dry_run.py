import click
import click_log
import traceback
import json
import sys
from convisoappsec.common.box import ContainerWrapper
from convisoappsec.flowcli import help_option
from convisoappsec.flowcli.context import pass_flow_context
from convisoappsec.logger import LOGGER
from convisoappsec.flowcli.common import on_http_error
from convisoappsec.common.cleaner import Cleaner

def log_func(msg, new_line=True):
    click.echo(msg, nl=new_line, err=True)

def execute_dry_run(flow_context, repository_dir, custom_sca_tags, scanner_timeout):
    REQUIRED_CODEBASE_PATH = '/code'
    OSV_SCANNER_IMAGE_NAME = 'osv_scanner'

    scanners = {
        OSV_SCANNER_IMAGE_NAME: {
            'repository_name': OSV_SCANNER_IMAGE_NAME,
            'tag': 'latest',
            'command': [
                '-c', REQUIRED_CODEBASE_PATH,
                '-f', 'json',
                '-o', '/{}.json'.format(OSV_SCANNER_IMAGE_NAME)
            ],
            'repository_dir': repository_dir
        },
    }

    if custom_sca_tags:
        for custom_tag in custom_sca_tags:
            scan_name, tag = custom_tag
            if scan_name in scanners.keys():
                scanners[scan_name]['tag'] = tag

    conviso_rest_api = flow_context.create_conviso_rest_api_client()
    token = conviso_rest_api.docker_registry.get_sast_token()
    
    LOGGER.info('💬 Preparing Environment...')
    scabox = ContainerWrapper(
        token=token,
        containers_map=scanners,
        logger=LOGGER,
        timeout=scanner_timeout
    )
    LOGGER.info('💬 Starting SCA...')
    scabox.run()

    results_list = []
    for unit in scabox.scanners:
        file_path = unit.results
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    results_list.append(json.load(f))
            except Exception as e:
                click.echo(f"Error reading result file {file_path}: {e}", file=sys.stderr)

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
def dry_run(flow_context, repository_dir, custom_sca_tags, scanner_timeout, cleanup):
    """
    Perform a dry-run SCA analysis.
    Checks API Key, runs the scan, and outputs the results in JSON format to stdout.
    Does NOT create assets or deploys on Conviso Platform.
    """
    try:
        results = execute_dry_run(flow_context, repository_dir, custom_sca_tags, scanner_timeout)

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
