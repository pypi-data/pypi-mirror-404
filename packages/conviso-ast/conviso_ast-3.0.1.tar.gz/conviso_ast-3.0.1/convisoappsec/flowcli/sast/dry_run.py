import sys
import click
import traceback
import json
from convisoappsec.sast.sastbox import SASTBox
from docker.errors import APIError
import time
from convisoappsec.flow import GitAdapter
from convisoappsec.flowcli import help_option
from convisoappsec.flowcli.context import pass_flow_context
from convisoappsec.logger import LOGGER
from convisoappsec.common.cleaner import Cleaner
from convisoappsec.flowcli.common import on_http_error

class DryRunSASTBox(SASTBox):
    def recovery_technologies_file(self):
        # Skip technology recovery and update for dry-run
        pass

def perform_dry_run_sastbox_scan(
    conviso_rest_api, sastbox_registry, sastbox_repository_name, sastbox_tag, sastbox_skip_login, repository_dir, end_commit, start_commit, logger
):
    max_retries = 5
    retries = 0
    sastbox = DryRunSASTBox(registry=sastbox_registry, repository_name=sastbox_repository_name, tag=sastbox_tag)
    pull_progress_bar = click.progressbar(length=sastbox.size, label="Performing SAST download...")

    while retries < max_retries:
        try:
            if not sastbox_skip_login:
                logger("Checking SASTBox authorization...")
                token = conviso_rest_api.docker_registry.get_sast_token()
                sastbox.login(token)

            with pull_progress_bar as progressbar:
                for downloaded_chunk in sastbox.pull():
                    progressbar.update(downloaded_chunk)
            break
        except APIError as e:
            retries += 1
            logger(f"Retrying {retries}/{max_retries}...")
            time.sleep(1)

            if retries == max_retries:
                logger("Max retries reached. Failed to perform SAST download.")
                raise Exception(f"Max retries reached. Could not complete the SAST download. Error: {str(e)}")

    logger("Starting SAST scan diff...")

    reports = sastbox.run_scan_diff(repository_dir, end_commit, start_commit, log=logger)

    logger("SAST scan diff done.")

    results_filepaths = []
    for r in reports:
        try:
            file_path = str(r)
            results_filepaths.append(file_path)
        except Exception as e:
            click.echo(f"Error decoding file path: {r} with error {e}.", file=sys.stderr)

    return results_filepaths

def log_func(msg, new_line=True):
    click.echo(msg, nl=new_line, err=True)

def execute_dry_run(flow_context, end_commit, start_commit, repository_dir,
                    sastbox_registry, sastbox_repository_name, sastbox_tag, sastbox_skip_login):
    git_adapter = GitAdapter(repository_dir)
    end_commit = end_commit or git_adapter.head_commit
    start_commit = start_commit or git_adapter.empty_repository_tree_commit

    if start_commit == end_commit:
        return {}

    conviso_rest_api = flow_context.create_conviso_rest_api_client()

    results_filepaths = perform_dry_run_sastbox_scan(
        conviso_rest_api, sastbox_registry, sastbox_repository_name, sastbox_tag,
        sastbox_skip_login, repository_dir, end_commit, start_commit, log_func
    )
    
    results_list = []
    for path in results_filepaths:
        try:
            with open(path, 'r') as f:
                results_list.append(json.load(f))
        except Exception as e:
            click.echo(f"Error reading result file {path}: {e}", file=sys.stderr)

    if len(results_list) == 1:
        return results_list[0]
    return results_list

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
    '--cleanup', default=False, is_flag=True, show_default=True,
    help="Clean up system resources."
)
@click.option(
    "-o", "--output", required=False, help="Output the results to a JSON file."
)
@help_option
@pass_flow_context
def dry_run(flow_context, end_commit, start_commit, repository_dir,
            sastbox_registry, sastbox_repository_name, sastbox_tag, sastbox_skip_login, cleanup, output):
    try:
        results = execute_dry_run(
            flow_context, end_commit, start_commit, repository_dir,
            sastbox_registry, sastbox_repository_name, sastbox_tag, sastbox_skip_login
        )

        if output:
            with open(output, "w") as f:
                json.dump(results if results else {}, f, indent=2)
            LOGGER.info(f"Results saved to {output}")
        elif results:
            print(json.dumps(results, indent=2))
        else:
            print(json.dumps({}, indent=2))
            
        if cleanup:
            LOGGER.info("🧹 Cleaning up ...")
            cleaner = Cleaner()
            cleaner.cleanup()

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        on_http_error(e)
        sys.exit(1)
