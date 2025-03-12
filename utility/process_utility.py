import json
from typing import Dict
from uuid import UUID

import requests
from robocorp.log import critical, info, suppress
from robocorp.vault import SecretContainer, get_secret, set_secret


@suppress(variables=True)
def create_process(name: str, task_id: str, task_name: str, worker_id: str):
    BASE_URL = "https://cloud.robocorp.com/api/v1"
    secrets: SecretContainer = get_secret("ProcessAPI")
    url = f"{BASE_URL}/workspaces/{secrets['workspace_id']}/processes"

    headers: Dict[str, str] = {
        "Authorization": f"RC-WSKEY {secrets['apikey']}",
        "Content-Type": "application/json",
    }
    # try:
    #     len(secrets["collector_process_id"]) > 0
    #     info("Process id already set for collector")
    #     return
    # except KeyError:
    #     info("New collector_process_id will be created")
    #     pass
    payload = json.dumps(
        {
            "name": name,
            "steps": [
                {
                    "name": "Retrive Failed Run Reports",
                    "task_package": {
                        "id": f"{task_id}",
                        "task": {
                            "name": f"{task_name}",
                        },
                    },
                    "worker": {
                        "type": "self_hosted",
                        "id": f"{worker_id}",
                    },
                }
            ],
        }
    )
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()

    try:
        UUID(response.json()["id"])
        secrets["collector_process_id"] = response.json()["id"]
        set_secret(secrets)
        info(f"Process {response.json()['id']} created")
    except ValueError:
        critical("Invalid process id")

    return secrets["collector_process_id"]


# @task
# def create_process_task():
#     create_process(
#         name="Test Process",
#         task_id="44039",
#         task_name="Collect Failed Run Reports",
#         worker_id="41cf7064-63d4-4625-a709-06b403f76769",
#     )
