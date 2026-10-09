import os

import dotenv
from globus_compute_sdk import Executor as GlobusExecutor


def hello_world() -> str:
    """Hello world function to run on remote system."""
    import platform

    return f"Hello World from {platform.node()}"


def remote_launch(endpoints: dict[str, str]) -> None:
    """Launch hello_world on all configured endpoints."""
    with GlobusExecutor(endpoint_id=endpoints["Tutorial_EP"]) as gc_executor:
        for endpoint, endpoint_id in endpoints.items():
            if not endpoint_id:
                continue

            print(f"Attempting function execution on {endpoint}")
            gc_executor.endpoint_id = endpoint_id
            future = gc_executor.submit(hello_world)
            try:
                result = future.result(timeout=120)
                print(f"Result: {result}")
            except TimeoutError as e:
                print(f"Task execution on {endpoint} failed with: {e}")

        print("Done")


if __name__ == "__main__":
    # Load endpoint IDs from settings.env in the project root
    dotenv.load_dotenv(dotenv.find_dotenv("settings.env"))

    endpoints = {
        "Aurora@ALCF": os.environ.get("AURORA_ENDPOINT_ID"),
        "Perlmutter@NERSC": os.environ.get("PERLMUTTER_ENDPOINT_ID"),
        "Frontier@OLCF": os.environ.get("FRONTIER_ENDPOINT_ID"),
        "Tutorial_EP": os.environ.get("TUTORIAL_ENDPOINT_ID"),
    }

    remote_launch(endpoints)
