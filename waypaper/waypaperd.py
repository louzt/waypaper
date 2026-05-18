"""Small daemon that periodically triggers `waypaper --random`."""

import argparse
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Mapping, Sequence


DEFAULT_INTERVAL_SECONDS = 1800
DEFAULT_SESSION_WAIT_SECONDS = 10
SESSION_WAIT_INTERVAL_SECONDS = 1
LOG = logging.getLogger(__name__)


def positive_interval(value: str) -> int:
    interval = int(value)
    if interval <= 0:
        raise argparse.ArgumentTypeError("interval must be a positive integer")
    return interval


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Randomly changes wallpaper every specified number of seconds."
    )
    parser.add_argument(
        "interval",
        nargs="?",
        default=DEFAULT_INTERVAL_SECONDS,
        type=positive_interval,
        help="Time interval in seconds between random wallpaper changes.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def build_waypaper_command() -> list[str]:
    return [sys.executable, "-m", "waypaper", "--random"]


def get_runtime_dir(environment: Mapping[str, str]) -> Path | None:
    runtime_dir = environment.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir)

    fallback_runtime_dir = Path("/run/user") / str(os.getuid())
    if fallback_runtime_dir.is_dir():
        return fallback_runtime_dir
    return None


def find_wayland_display(runtime_dir: Path | None) -> str | None:
    if runtime_dir is None or not runtime_dir.is_dir():
        return None

    for socket_path in sorted(runtime_dir.glob("wayland-*")):
        if socket_path.is_socket():
            return socket_path.name
    return None


def add_dbus_session_bus(environment: dict[str, str]) -> None:
    if environment.get("DBUS_SESSION_BUS_ADDRESS"):
        return

    runtime_dir = get_runtime_dir(environment)
    if runtime_dir is None:
        return

    bus_path = runtime_dir / "bus"
    if bus_path.is_socket():
        environment["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_path}"


def build_waypaper_environment(
    environment: Mapping[str, str] | None = None,
    wait_seconds: int = DEFAULT_SESSION_WAIT_SECONDS,
    wait_interval: int = SESSION_WAIT_INTERVAL_SECONDS,
    sleep=time.sleep,
) -> dict[str, str]:
    prepared_environment = dict(os.environ if environment is None else environment)
    add_dbus_session_bus(prepared_environment)

    if prepared_environment.get("WAYLAND_DISPLAY"):
        return prepared_environment

    runtime_dir = get_runtime_dir(prepared_environment)
    wayland_display = find_wayland_display(runtime_dir)
    if wayland_display:
        prepared_environment["WAYLAND_DISPLAY"] = wayland_display
        add_dbus_session_bus(prepared_environment)
        LOG.info("Using Wayland display %s from %s.", wayland_display, runtime_dir)
        return prepared_environment

    if prepared_environment.get("DISPLAY"):
        return prepared_environment

    deadline = time.monotonic() + wait_seconds
    while True:
        runtime_dir = get_runtime_dir(prepared_environment)
        wayland_display = find_wayland_display(runtime_dir)
        if wayland_display:
            prepared_environment["WAYLAND_DISPLAY"] = wayland_display
            add_dbus_session_bus(prepared_environment)
            LOG.info("Using Wayland display %s from %s.", wayland_display, runtime_dir)
            return prepared_environment

        if time.monotonic() >= deadline:
            LOG.warning("No Wayland socket found before timeout; launching without display environment.")
            return prepared_environment

        LOG.info("Waiting for Wayland socket in %s.", runtime_dir or "XDG_RUNTIME_DIR")
        sleep(wait_interval)


def trigger_random_wallpaper(
    command: Sequence[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> int:
    run_kwargs = {"check": False}
    if environment is not None:
        run_kwargs["env"] = dict(environment)

    result = subprocess.run(
        list(command) if command is not None else build_waypaper_command(),
        **run_kwargs,
    )
    if result.returncode == 0:
        LOG.info("Random wallpaper command completed successfully.")
    else:
        LOG.warning("Random wallpaper command exited with status %s.", result.returncode)
    return result.returncode


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    command = build_waypaper_command()
    environment = build_waypaper_environment()

    LOG.info("Starting waypaperd with interval=%s seconds.", args.interval)
    try:
        while True:
            trigger_random_wallpaper(command, environment=environment)
            LOG.info("Sleeping for %s seconds.", args.interval)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        LOG.info("waypaperd interrupted, exiting cleanly.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
