"""Meltano Evidence extension."""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

import structlog
from meltano.edk import models
from meltano.edk.extension import ExtensionBase
from meltano.edk.process import Invoker, log_subprocess_error

log = structlog.get_logger()


class Evidence(ExtensionBase):
    """Extension implementing the ExtensionBase interface."""

    def __init__(self) -> None:
        """Initialize the extension."""
        self.app_name = "evidence_extension"
        self.evidence_home = os.environ.get("EVIDENCE_HOME") or os.environ.get(
            "EVIDENCE_HOME_DIR"
        )
        if not self.evidence_home:
            log.debug("env dump", env=os.environ)
            log.error(
                "EVIDENCE_HOME not found in environment, unable to function without it"
            )
            sys.exit(1)
        self.npm = Invoker("npm")
        self.npx = Invoker("npx")

    def initialize(self, force: bool):
        """Initialize a new project."""
        try:
            self.npx.run_and_log(
                *["degit", "evidence-dev/template", self.evidence_home]
            )
        except subprocess.CalledProcessError as err:
            log_subprocess_error("npx degit", err, "npx degit failed")
            sys.exit(err.returncode)

    def invoke(self, command_name: str | None, *command_args: Any) -> None:
        """Invoke the underlying cli, that is being wrapped by this extension.

        Args:
            command_name: The name of the command to invoke.
            command_args: The arguments to pass to the command.
        """
        try:
            self.npm.run_and_log(*command_args)
        except subprocess.CalledProcessError as err:
            log_subprocess_error(f"npm {command_name}", err, "npm invocation failed")
            sys.exit(err.returncode)

    def describe(self) -> models.Describe:
        """Describe the extension.

        Returns:
            The extension description
        """
        return models.Describe(
            commands=[
                models.ExtensionCommand(
                    name="evidence_extension", description="extension commands"
                )
            ]
        )

    def build(self):
        """Run 'npm run build' in the Evidence home dir."""
        self.npm.run_and_log(*["install", "--prefix", self.evidence_home])
        self.npm.run_and_log(*["run", "build", "--prefix", self.evidence_home])

    def dev(self):
        """Run 'npm run dev' in the Evidence home dir."""
        self.npm.run_and_log(*["install", "--prefix", self.evidence_home])
        self.npm.run_and_log(*["run", "dev", "--prefix", self.evidence_home])
