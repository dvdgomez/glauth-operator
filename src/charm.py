#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""GLAuth Operator Charm."""

import logging

import glauth
from charms.operator_libs_linux.v1 import snap
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus

logger = logging.getLogger(__name__)


class GlauthCharm(CharmBase):
    """Charmed Operator to deploy glauth - a lightweight LDAP server."""

    def __init__(self, *args):
        super().__init__(*args)

        # Observe common Juju events
        self.framework.observe(self.on.install, self._install)
        self.framework.observe(self.on.remove, self._remove)
        self.framework.observe(self.on.update_status, self._update_status)
        self.framework.observe(self.on.upgrade_charm, self._upgrade_charm)

        # Integrations
        self.framework.observe(self.on.glauth_relation_changed, self._on_glauth_relation_changed)

    def _install(self, _):
        """Install glauth."""
        self.unit.status = MaintenanceStatus("installing glauth")
        try:
            glauth.install()
            self.unit.set_workload_version(glauth.version)
            self.unit.status = ActiveStatus("glauth ready")
        except snap.SnapError as e:
            self.unit.status = BlockedStatus(e.message)

    def _on_glauth_relation_changed(self, _):
        self.unit.status = MaintenanceStatus("reconfiguring glauth")

    def _remove(self, _):
        """Remove glauth from the machine."""
        self.unit.status = MaintenanceStatus("removing glauth")
        glauth.remove()

    def _update_status(self, _):
        """Update status."""
        snap.hold_refresh()
        self.unit.set_workload_version(glauth.version)

    def _upgrade_charm(self, _):
        """Ensure the snap is refreshed (in channel) if there are new revisions."""
        self.unit.status = MaintenanceStatus("refreshing glauth")
        try:
            glauth.refresh()
        except snap.SnapError as e:
            self.unit.status = BlockedStatus(e.message)


if __name__ == "__main__":  # pragma: nocover
    main(GlauthCharm)
