#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides glauth class to control glauth."""

import logging
import pathlib
import shlex
import subprocess
import zipfile

from charms.operator_libs_linux.v1 import snap
from jinja2 import Template

logger = logging.getLogger(__name__)


def __getattr__(prop: str):
    if prop == "active":
        return bool(_snap().services["daemon"]["active"])
    elif prop == "installed":
        return _snap().present
    elif prop == "version":
        if _snap().present:
            # Version separated by newlines includes version, build time and commit hash
            # split by newlines, grab first line, grab second string for version
            full_version = subprocess.run(
                ["snap", "list", "glauth"], stdout=subprocess.PIPE, text=True
            ).stdout.splitlines()[1]
            return full_version.split()[2]
        raise snap.SnapError("glauth snap not installed, cannot fetch version")
    raise AttributeError(f"Module {__name__!r} has no property {prop!r}")


def _create_default_config(ldap_port: int, api_port: int) -> None:
    """Create default config with no users."""
    with open("templates/glauth.toml.j2", "r") as f:
        template = Template(f.read())

    rendered = template.render(ldap_port=ldap_port, api_port=api_port)
    with open("/var/snap/glauth/common/etc/glauth/glauth.d/glauth.cfg", "w") as f:
        f.write(rendered)


def _get_hostname() -> str:
    """Get GLAuth hostname.

    Returns:
      GLAuth hostname.
    """
    hostname = subprocess.run(
        ["cat", "/etc/hostname"], capture_output=True, text=True
    ).stdout.strip()
    return hostname


def _snap():
    cache = snap.SnapCache()
    return cache["glauth"]


def set_config(config: pathlib.Path, ldap_port: int, api_port: int) -> str:
    """Set GLAuth config resource. Create default if none found.

    Args:
      config: Resource config Path object.
      ldap_port: LDAP port for default config.
      api_port: API port for default config.


    Returns:
      LDAP URI.
    """
    ldap_uri = "ldap"
    # Create default config with no users if resource glauth.cfg not found
    if config is None:
        _create_default_config(ldap_port, api_port)
        ldap_uri = ldap_uri + f"://{_get_hostname()}:{ldap_port}"
    # Zip file of multiple configs
    else:
        with zipfile.ZipFile(config, "r") as zip:
            zip.extractall("/var/snap/glauth/common/etc/glauth/glauth.d/")
        ldap_uri = ldap_uri + f"s://{_get_hostname()}:{ldap_port}"
    return ldap_uri


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


def load() -> str:
    """Load ca-certificate from glauth snap.

    Returns:
      The ca certificate content.
    """
    cert = "/var/snap/glauth/common/etc/glauth/certs.d/glauth.crt"
    key = "/var/snap/glauth/common/etc/glauth/keys.d/glauth.key"
    if not pathlib.Path(cert).exists() and not pathlib.Path(key).exists():
        # If cert and key do not exist, create both
        subprocess.run(
            shlex.split(
                f'openssl req -x509 -newkey rsa:4096 -keyout {key} -out {cert} -days 365 -nodes -subj "/CN={_get_hostname()}"'
            )
        )
    # Start and enable Snap now that config, cert, and key are available
    _snap().start(enable=True)
    content = open(cert, "r").read()
    return content


def refresh() -> None:
    """Refresh the glauth snap if there is a new revision."""
    # The operation here is exactly the same, so just call the install method
    install()


def remove() -> None:
    """Remove the glauth snap, preserving config and data."""
    _snap().ensure(snap.SnapState.Absent)
