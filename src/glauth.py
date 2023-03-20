#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides glauth class to control glauth."""

import logging
import subprocess

from charms.operator_libs_linux.v1 import snap

logger = logging.getLogger(__name__)


class Glauth:
    """Provide glauth charm all functionality needed."""

    def install(self):
        """Install glauth snap."""
        try:
            # Change to stable once stable is released
            self._snap.ensure(snap.SnapState.Latest, channel="edge")
            snap.hold_refresh()
        except snap.SnapError as e:
            logger.error("could not install glauth. Reason: %s", e.message)
            logger.debug(e, exc_info=True)
            raise e

    def refresh(self):
        """Refresh the glauth snap if there is a new revision."""
        # The operation here is exactly the same, so just call the install method
        self.install()

    def remove(self):
        """Remove the glauth snap, preserving config and data."""
        self._snap.ensure(snap.SnapState.Absent)

    @property
    def installed(self):
        """Report if the glauth snap is installed."""
        return self._snap.present

    @property
    def version(self) -> str:
        """Report the version of glauth currently installed."""
        if self.installed:
            # Version separated by newlines includes version, build time and commit hash
            # split by newlines, grab first line, grab second string for version
            full_version = subprocess.run(
                ["glauth", "--version"], stdout=subprocess.PIPE, text=True
            ).stdout.splitlines()[0]
            return full_version.split()[1]
        raise snap.SnapError("glauth snap not installed, cannot fetch version")

    @property
    def _snap(self):
        """Return a representation of the glauth snap."""
        cache = snap.SnapCache()
        return cache["glauth"]
