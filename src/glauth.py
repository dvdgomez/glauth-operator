#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides glauth class to control glauth."""

import logging
import subprocess

from charms.operator_libs_linux.v1 import snap

logger = logging.getLogger(__name__)


def __getattr__(prop: str):
    if prop == "installed":
        return _snap().present
    elif prop == "version":
        if _snap().present:
            # Version separated by newlines includes version, build time and commit hash
            # split by newlines, grab first line, grab second string for version
            full_version = subprocess.run(
                ["glauth", "--version"], stdout=subprocess.PIPE, text=True
            ).stdout.splitlines()[0]
            return full_version.split()[1]
        raise snap.SnapError("glauth snap not installed, cannot fetch version")
    raise AttributeError(f"Module {__name__!r} has no property {prop!r}")


def _snap():
    cache = snap.SnapCache()
    return cache["glauth"]


def install():
    """Install glauth snap."""
    try:
        # Change to stable once stable is released
        _snap().ensure(snap.SnapState.Latest, channel="edge")
        snap.hold_refresh()
    except snap.SnapError as e:
        logger.error("could not install glauth. Reason: %s", e.message)
        logger.debug(e, exc_info=True)
        raise e


def refresh():
    """Refresh the glauth snap if there is a new revision."""
    # The operation here is exactly the same, so just call the install method
    install()


def remove():
    """Remove the glauth snap, preserving config and data."""
    _snap().ensure(snap.SnapState.Absent)
