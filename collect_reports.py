import os
import zipfile
from pathlib import Path
from time import time

from dotenv import load_dotenv
from robocorp import log, workitems
from robocorp.tasks import get_output_dir, task

load_dotenv()
# Get the path to the LOCALAPPDATA directory
local_appdata = Path(os.getenv("LOCALAPPDATA"))
# Create the path to the run logs
run_logs = local_appdata / "robocorp" / "workforce-agent-core-service" / "runs"
# Create the path to the worker logs
worker_logs = local_appdata / "robocorp" / "workforce-agent" / "logs"
# Create the path to the reports folder
reports_folder = Path(os.getenv("REPORTS_FOLDER", default=get_output_dir()))


@task
def collect_failed_run_reports():
    for item in workitems.inputs:
        try:
            failed_step_id = item.payload["failed_step_id"]
            create_zip_of_folder(
                run_logs / failed_step_id,
                reports_folder / f"run_{failed_step_id}.zip",
            )
            create_zip_of_folder(
                worker_logs,
                reports_folder / f"worker_logs_{failed_step_id}.zip",
            )
        except TypeError:
            log.critical(f"No step id in payload: {item.payload}")


def create_zip_of_folder(folder_path: Path, zip_path: Path) -> None:
    """
    Creates a ZIP archive of a folder, skipping any existing ZIP files.

    :param folder_path: Path to the folder to be zipped.
    :param zip_path: Path to the output ZIP file.
    """
    folder_path = Path(folder_path)
    zip_path = Path(zip_path)
    current_time = time()
    if folder_path.exists():
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in folder_path.rglob("*"):
                if (
                    file_path.is_file() and file_path.suffix != ".zip"
                ):  # Skip directories and ZIP files
                    if 1735689600.8706732 < os.path.getatime(folder_path):
                        os.utime(file_path, (current_time, current_time))
                    arcname = file_path.relative_to(folder_path)
                    zipf.write(file_path, arcname)
        log.info(f"ZIP archive created at: {zip_path}")
    else:
        log.critical(f"Folder does not exist: {folder_path}")
        raise Exception(f"Folder does not exist: {folder_path}")
