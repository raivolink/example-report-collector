import re
from typing import Any, Dict

import requests
from robocorp.log import console_message
from robocorp.tasks import task
from robocorp.vault import SecretContainer, get_secret

__all__ = [
    "get_failed_step_id",
    "get_step_worker_info",
    "get_step_run_artifacts",
]

_BASE_URL = "https://cloud.robocorp.com/api/v1"

_secrets: SecretContainer = get_secret("ProcessAPI")
_headers: Dict[str, str] = {"Authorization": f"RC-WSKEY {_secrets['apikey']}"}
_url: str = f"{_BASE_URL}/workspaces/{_secrets['workspace_id']}/step-runs"


def _get_step_run(
    process_run_id: str, run_state: str = None
) -> Dict[str, Any]:
    """Get the step run from the process run id
    :param process_run_id: The process run id
    :param run_state: The run state
    :return: The step run dictionary
    """
    params: Dict[str, str] = {"process_run_id": process_run_id}

    response = requests.request("GET", _url, headers=_headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to get step runs: {response.text}")
    data = response.json()["data"]

    return (
        [d for d in data if d["state"].upper() == run_state.upper()]
        if run_state
        else data
    )


def _get_step_run_console_messages(
    step_run_id: str,
) -> Dict[str, Any]:
    """Get the console messages of a step run
    :param step_run_id: The step run id
    :return: The console messages dictionary
    """

    request_url = f"{_url}/{step_run_id}/console-messages"
    # TODO Add pagination
    response = requests.request("GET", request_url, headers=_headers)
    response.raise_for_status()

    return response.json()["data"]


def get_failed_step_id(process_run_id: str) -> Dict[str, Any] | None:
    """Get the step id from the process run id
    :param process_run_id: The process run id
    :return: The step id or None if no failed step is found
    """
    step_data = _get_step_run(process_run_id, run_state="failed")
    # return first failed step_id
    # COMMENT We only return first failed step as we assume there is only one failed step
    if step_data:
        return step_data[0]["id"]
    else:
        return None


def get_step_worker_info(step_id: str) -> str | None:
    """Get the worker info from the step id
    :param step_id: The step id
    :return: The worker info or None if no worker info is found
    """

    console_messages = _get_step_run_console_messages(step_id)
    for line in console_messages:
        if u_name := _extract_username(line["message"]):
            console_message(
                f"Match found: {line['line_number']} - {line['message']}",
                kind="regular",
            )
            return u_name

    return None


def _extract_username(log_entries: Dict[str, Any]) -> str | None:
    """Extract the username from the console log entries
    :param log_entries: The console log entries
    :return: The username or None if no username is found
    """

    pattern = r'Context:\s*"[^"]+"\s*<[^\\]+\\([^@]+@[^>]+)>'
    match = re.search(pattern, log_entries)
    if match:
        return match.groups()[0]

    return None


def get_step_run_artifacts(step_run_id: str) -> Dict[str, Any]:
    """Get the artifacts of a step run
    :param step_run_id: The step run id
    :return: The artifacts dictionary
    """
    request_url = f"{_url}/{step_run_id}/artifacts"
    response = requests.request("GET", request_url, headers=_headers)
    response.raise_for_status()

    if response.json()["data"]:
        return response.json()["data"]
    else:
        return None
