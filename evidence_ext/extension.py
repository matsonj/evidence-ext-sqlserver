"""Meltano Evidence extension."""
from __future__ import annotations

import os
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import structlog
from meltano.edk import models
from meltano.edk.extension import ExtensionBase
from meltano.edk.process import Invoker, log_subprocess_error

log = structlog.get_logger()


class Evidence(ExtensionBase):
    """Extension implementing the ExtensionBase interface."""

    _invokers = {}

    def __init__(self) -> None:
        """Initialize the extension."""
        self.app_name = "evidence_extension"
        self.evidence_home = os.environ.get("EVIDENCE_HOME") or os.environ.get(
            f"{self.app_name}_EVIDENCE_HOME"
        )
        if not self.evidence_home:
            log.debug("env dump", env=os.environ)
            log.error(
                "EVIDENCE_HOME not found in environment, unable to function without it"
            )
            sys.exit(1)

    def get_invoker(self, command_name):
        assert command_name in ("npm", "npx"), f"Command {command_name} not supported."
        if command_name not in self._invokers:
            self._invokers[command_name] = Invoker(command_name)
        return self._invokers[command_name]

    def initialize(self, force: bool):
        """Initialize a new project."""
        npx = self.get_invoker("npx")
        try:
            npx.run_and_log(*["degit", "evidence-dev/template", self.evidence_home])
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
            self.get_invoker("npm").run_and_log(*command_args)
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
        npm = self.get_invoker("npm")
        npm.run_and_log(*["install", "--prefix", self.evidence_home])
        npm.run_and_log(*["run", "build", "--prefix", self.evidence_home])

    def dev(self):
        npm = self.get_invoker("npm")
        npm.run_and_log(*["install", "--prefix", self.evidence_home])
        npm.run_and_log(*["run", "dev", "--prefix", self.evidence_home])
