import json
import os
import re
from dataclasses import dataclass

import requests
from robocorp import log, storage, workitems
from robocorp.tasks import task
from robocorp.vault import SecretContainer, get_secret

from utility.process_utility import create_process
from utility.steps_utility import (
    get_failed_step_id,
    get_step_run_artifacts,
    get_step_worker_info,
)


@dataclass
class ProcessRun:
    id: str
    run_id: str
    workspace_name: str
    organization_name: str


TASK_ID = os.getenv("COLLECTION_TASK_ID", "44039")
TASK_NAME = os.getenv("COLLECTION_TASK_NAME", "Collect Failed Run Data")


@task
def analyze_and_setup():
    item = workitems.inputs.current
    email_body = item.payload["email"]["text"]
    worker_info, failed_step_id = get_failed_run_info(email_body)
    run_artifacts = get_step_run_artifacts(failed_step_id)
    if not run_artifacts:
        worker_name = (
            f"{worker_info.split('@')[1]}-{worker_info.split('@')[0]}"
        )
        worker_id = get_worker_id(worker_name)
        process_id = create_process(
            name="Collect Run Reports",
            task_id=TASK_ID,
            task_name=TASK_NAME,
            worker_id=worker_id,
        )
        start_collector_process(process_id, failed_step_id)


def get_failed_run_info(email_body):
    run_url = get_url_from_email_body(email_body)
    p_run_data = get_process_info_from_url(run_url)
    failed_step_id = get_failed_step_id(p_run_data.run_id)
    worker_info = get_step_worker_info(failed_step_id)
    return worker_info, failed_step_id


def get_worker_id(worker_name: str):
    name_prefix = "Robocorp-"
    worker_list = storage.get_json("workers_list")
    for worker in worker_list:
        if (
            worker["name"].upper()
            == "".join([name_prefix, worker_name]).upper()
        ):
            return worker["id"]


def get_process_info_from_url(url: str) -> str:
    """
    Extracts the process ID from the URL.
    :param url: The URL to extract the process ID from.
    :return: The process ID from the URL.
    """
    process_run = ProcessRun(
        id=url.split("/")[5],
        run_id=url.split("/")[-1],
        workspace_name=url.split("/")[3],
        organization_name=url.split("/")[2],
    )
    return process_run


def get_url_from_email_body(email_body: str) -> str | None:
    """
    Extracts the URL from the email body.
    :param email_body: The body of the email.
    :return: The URL from the email body or None if no URL is found.
    """
    pattern = r"https:\/\/[a-zA-Z0-9\/\.\-_]+"
    match = re.search(pattern, email_body)
    if match:
        url = match.group(0)
        return url
    return None


def start_collector_process(process_id, failed_step_id):
    secrets: SecretContainer = get_secret("ProcessAPI")
    url = f"https://cloud.robocorp.com/api/v1/workspaces/{secrets['workspace_id']}/processes/{process_id}/process-runs"

    payload = json.dumps(
        {
            "type": "with_payloads",
            "payloads": [{"failed_step_id": failed_step_id}],
        }
    )
    headers = {
        "Authorization": f"RC-WSKEY {secrets['apikey']}",
        "Content-Type": "Content-Type': 'application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    response.raise_for_status()
