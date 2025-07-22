# Adapted from https://gist.github.com/honi/81ba1bff622649a4a2ef7ccf695b1fa0

import argparse
import logging
import os
import shlex
import signal
import subprocess
import sys

from django.core.management.base import BaseCommand
from django.utils import autoreload

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command to run an RQ worker with autoreload for development."""

    help = "Run an RQ worker with autoreload (development only)."
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command line arguments for the RQ worker."""
        parser.add_argument(
            "--worker-pid-file",
            action="store",
            dest="worker_pid_file",
            default="/tmp/rqworker.pid",
        )
        parser.add_argument("rqworkerargs", nargs="*")

    def handle(self, *args, **options) -> None:
        """Handle the command to run an RQ worker with autoreload."""
        autoreload.run_with_reloader(
            lambda: run_worker(options["worker_pid_file"], options["rqworkerargs"])
        )


def run_worker(worker_pid_file: str, worker_args: list[str]) -> None:
    """Start an RQ worker, terminating any existing worker with the same PID."""
    if os.path.exists(worker_pid_file):
        with open(worker_pid_file) as f:
            worker_pid = f.read().strip()
        if worker_pid:
            try:
                LOGGER.info("Terminating RQ worker with PID %s", worker_pid)
                os.kill(int(worker_pid), signal.SIGTERM)
            except (ProcessLookupError, ValueError):
                LOGGER.info(
                    "Process with PID %s does not exist or has already exited.", worker_pid
                )

    # Start a new RQ worker process, saving its PID to the provided file
    start_worker_cmd = f"{sys.executable} {get_managepy_path()} rqworker --pid={worker_pid_file} {' '.join(worker_args)}"
    print(f"Starting RQ worker: {start_worker_cmd}")
    subprocess.run(shlex.split(start_worker_cmd))


def get_managepy_path() -> str:
    """Find the path to manage.py in the current project directory or its parents."""
    managepy_path = None
    search_path = os.path.dirname(os.path.abspath(__file__))
    while not managepy_path:
        candidate = os.path.join(search_path, "manage.py")
        if os.path.exists(candidate):
            managepy_path = os.path.abspath(candidate)
        else:
            parent = os.path.dirname(search_path)
            if parent == search_path:
                raise RuntimeError("manage.py not found in parent directories")
            search_path = parent
    return managepy_path
