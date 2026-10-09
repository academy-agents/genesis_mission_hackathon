# Module 0: Globus Compute endpoint setup

A Globus Compute endpoint runs your Python functions on a remote system, for example Aurora, Perlmutter, or Frontier.

The `globus-compute-endpoint` package is installed when you install this repo with `uv sync`. Refer to the [top-level README](../../README.md). Do the steps below on the system where the endpoint must run, for example a login node.

## 1. Configure the endpoint

```bash
uv run globus-compute-endpoint configure gm_endpoint
```

This command creates the endpoint configuration in `~/.globus_compute/gm_endpoint/`.

## 2. Start the endpoint

```bash
uv run globus-compute-endpoint start gm_endpoint
```

The first time, the command shows a Globus login link. Open the link and log in.

When the endpoint starts, it shows its endpoint UUID. To show the UUID again, use:

```bash
uv run globus-compute-endpoint list
```

## 3. Add the endpoint UUID to settings.env

Copy the endpoint UUID into `settings.env` in the project root. Use the variable for your system:

```
AURORA_ENDPOINT_ID=<your-endpoint-uuid>
PERLMUTTER_ENDPOINT_ID=<your-endpoint-uuid>
FRONTIER_ENDPOINT_ID=<your-endpoint-uuid>
```

## 4. Test the endpoint

```bash
uv run python intermediate/00_endpoint_setup/remote_function_call.py
```

The script runs `hello_world` on each endpoint in `settings.env` and shows the result.
