# Collecting logs from failed runs

## How to run

### Prerequisites

- API key with accesses as [on this image](C:\Users\Raivo\Documents\GitHub\robot-examples\example-report-collector\doc\images\api_access.png)
- Vault secret `ProcessAPI` with the following keys:
  - apikey
  - workspace_id
  - collector_process_id (Optional)
- Json asset named `workers-list`.

```json
[
{
  "id": "e2c2ee2a-c4d6-41d4-6e4b-fba63fd392a1",
  "name": "Robocorp-machine1-EXAMP2"
},
{
  "id": "6e8807d1-46fd-4545-b456a-0001ea6a7084",
  "name": "Robocorp-machine1-EXAMP2"
}
]
  ```


Automation has two task that can be used to collect logs from failed runs:

1. `Get Failed Run Info`
2. `Collect Failed Run Data`

### Get Failed Run Info

This task is used to get the failed run info from the email body. It uses api calls to gather steps information and worker information.

If failed run did not have artifacts available, process will be created to collect artifacts. After creation process process will be started.
Pocess needs enviroment variable with task package id and step name.

### Collect Failed Run Data

Uses step id to compress run logs and worker logs into zip files.