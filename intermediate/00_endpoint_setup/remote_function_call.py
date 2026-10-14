import os

import dotenv
from globus_compute_sdk import Executor as GlobusExecutor
from globus_sdk.services.compute.errors import ComputeAPIError


def hello_world() -> str:
    """Hello world function to run on remote system."""
    import platform

    return f"Hello World from {platform.node()}"


def remote_launch(endpoints: dict[str, tuple[str | None, dict | None]]) -> None:
    """Launch hello_world on all configured endpoints."""
    with GlobusExecutor(endpoint_id=endpoints["Tutorial_EP"][0]) as gc_executor:
        for endpoint, (endpoint_id, config) in endpoints.items():
            if not endpoint_id:
                continue

            print(f"Attempting function execution on {endpoint}")
            gc_executor.endpoint_id = endpoint_id
            gc_executor.user_endpoint_config = config
            try:
                future = gc_executor.submit(hello_world)
            except ComputeAPIError as e:
                print(f"Could not submit job to {endpoint}, error:{e}")
                continue

            try:
                # A compute-node task waits for its batch job to start
                result = future.result(timeout=1200)
                print(f"Result: {result}")
            except TimeoutError as e:
                print(f"Task execution on {endpoint} failed with: {e}")

        print("Done")


if __name__ == "__main__":
    # Load endpoint IDs from settings.env in the project root
    dotenv.load_dotenv(dotenv.find_dotenv("settings.env"))

    # Each entry is (endpoint ID, user_endpoint_config). The Aurora and Perlmutter
    # endpoints run the task in a batch job on a compute node, charged to the account.
    endpoints = {
        "Aurora@ALCF": (
            os.environ.get("AURORA_ENDPOINT_ID"),
            {
                "account": os.environ.get("AURORA_ACCOUNT"),
                # hpc-bridge reads the PBS queue from "partition"
                "partition": os.environ.get("AURORA_QUEUE"),
                # Aurora holds jobs that do not name the file systems they use
                "scheduler_options": "#PBS -l filesystems=home:flare",
            },
        ),
        "Perlmutter@NERSC": (
            os.environ.get("PERLMUTTER_ENDPOINT_ID"),
            {
                "account": os.environ.get("PERLMUTTER_ACCOUNT"),
                # Perlmutter rejects jobs that do not select CPU or GPU nodes
                "scheduler_options": "#SBATCH --constraint=cpu",
            },
        ),
        # Frontier remains untested
        "Frontier@OLCF": (os.environ.get("FRONTIER_ENDPOINT_ID"), None),
        "Tutorial_EP": (os.environ.get("TUTORIAL_ENDPOINT_ID"), None),
    }

    remote_launch(endpoints)
