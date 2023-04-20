#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides glauth class to control glauth."""

import logging
import pathlib
import socket
import subprocess

from charms.operator_libs_linux.v1 import snap
from jinja2 import Template

logger = logging.getLogger(__name__)


def _snap():
    cache = snap.SnapCache()
    return cache["glauth"]


def active() -> bool:
    """Return if GLAuth is active or not."""
    return bool(_snap().services["daemon"]["active"])


def create_default_config(api_port: int) -> None:
    """Create default config with no users."""
    template = Template(pathlib.Path("templates/glauth.toml.j2").read_text())

    rendered = template.render(api_port=api_port, ldap_port=363)
    pathlib.Path("/var/snap/glauth/common/etc/glauth/glauth.d/glauth.cfg").write_text(rendered)


def install() -> None:
    """Install glauth snap."""
    try:
        # Change to stable once stable is released
        _snap().ensure(snap.SnapState.Latest, channel="edge")
        snap.hold_refresh()
    except snap.SnapError as e:
        logger.error("could not install glauth. Reason: %s", e.message)
        logger.debug(e, exc_info=True)
        raise e


def installed() -> bool:
    """Return if GLAuth is installed or not."""
    return _snap().present


def load() -> str:
    """Load ca-certificate from glauth snap.

    Returns:
        str: The ca certificate content.
    """
    cert = "/var/snap/glauth/common/etc/glauth/certs.d/glauth.crt"
    key = "/var/snap/glauth/common/etc/glauth/keys.d/glauth.key"
    if not pathlib.Path(cert).exists() and not pathlib.Path(key).exists():
        # If cert and key do not exist, create both
        subprocess.call(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:4096",
                "-keyout",
                f"{key}",
                "-out",
                f"{cert}",
                "-days",
                "365",
                "-nodes",
                "-subj",
                f"/CN={socket.gethostname()}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    content = open(cert, "r").read()
    return content


def refresh() -> None:
    """Refresh the glauth snap if there is a new revision."""
    # The operation here is exactly the same, so just call the install method
    install()


def remove() -> None:
    """Remove the glauth snap, preserving config and data."""
    _snap().ensure(snap.SnapState.Absent)


def start() -> None:
    """Start the glauth snap."""
    _snap().start(enable=True)


def version() -> str:
    """Return GLAuth version."""
    if _snap().present:
        # Version separated by newlines includes version, build time and commit hash
        # split by newlines, grab first line, grab second string for version
        full_version = subprocess.run(
            ["snap", "list", "glauth"], stdout=subprocess.PIPE, text=True
        ).stdout.splitlines()[1]
        return full_version.split()[2]
    raise snap.SnapError("glauth snap not installed, cannot fetch version")
