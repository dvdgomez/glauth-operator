#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""GLAuth Operator Charm."""

import logging

import glauth
from charms.operator_libs_linux.v1 import snap
from ldapclient_lib import ConfigDataUnavailableEvent, LdapClientProvides, LdapReadyEvent
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus

logger = logging.getLogger(__name__)


class GlauthCharm(CharmBase):
    """Charmed Operator to deploy glauth - a lightweight LDAP server."""

    def __init__(self, *args):
        super().__init__(*args)
        self._ldapclient = LdapClientProvides(self, "ldap-client")
        # Observe common Juju events
        self.framework.observe(self.on.install, self._install)
        self.framework.observe(self.on.remove, self._remove)
        self.framework.observe(self.on.update_status, self._update_status)
        self.framework.observe(self.on.upgrade_charm, self._upgrade_charm)
        # Actions
        self.framework.observe(self.on.set_confidential_action, self._on_set_confidential_action)
        # LDAP Client Lib Integrations
        self.framework.observe(
            self._ldapclient.on.config_data_unavailable,
            self._on_config_data_unavailable,
        )
        self.framework.observe(
            self._ldapclient.on.ldap_ready,
            self._on_ldap_ready,
        )

    def _install(self, _):
        """Install glauth."""
        self.unit.status = MaintenanceStatus("installing glauth")
        try:
            glauth.install()
            self.unit.set_workload_version(glauth.version())
            self.unit.status = ActiveStatus()
        except snap.SnapError as e:
            self.unit.status = BlockedStatus(e.message)

    def _on_config_data_unavailable(self, event: ConfigDataUnavailableEvent) -> None:
        """Handle config-data-unavailable event."""
        # If config data is unavailable, set default config
        glauth.create_default_config(api_port=event.api_port)

    def _on_ldap_ready(self, event: LdapReadyEvent) -> None:
        """Handle ldap-ready event."""
        glauth.start()
        self.unit.status = ActiveStatus()

    def _on_set_confidential_action(self, event):
        """Handle the set-confidential action."""
        if "ca-cert" in event.params:
            cc_content = {"ca-cert": event.params["ca-cert"]}
        else:
            cc_content = {"ca-cert": glauth.load()}
        ldbd_content = {"ldap-default-bind-dn": event.params["ldap-default-bind-dn"]}
        lp_content = {"ldap-password": event.params["ldap-password"]}
        cc_secret = self.app.add_secret(cc_content, label="ca-cert")
        logger.debug("created secret ca-cert")
        ldbd_secret = self.app.add_secret(ldbd_content, label="ldap-default-bind-dn")
        logger.debug("created secret ldap-default-bind-dn")
        lp_secret = self.app.add_secret(lp_content, label="ldap-password")
        logger.debug("created secret ldap-password")
        # Get peer integration to store secrets
        ldap_relation = self.model.get_relation("glauth")
        ldap_relation.data[self.app]["ca-cert"] = cc_secret.id
        ldap_relation.data[self.app]["ldap-default-bind-dn"] = ldbd_secret.id
        ldap_relation.data[self.app]["ldap-password"] = lp_secret.id

    def _remove(self, _):
        """Remove glauth from the machine."""
        self.unit.status = MaintenanceStatus("removing glauth")
        glauth.remove()

    def _update_status(self, _):
        """Update status."""
        snap.hold_refresh()
        self.unit.set_workload_version(glauth.version())

    def _upgrade_charm(self, _):
        """Ensure the snap is refreshed (in channel) if there are new revisions."""
        self.unit.status = MaintenanceStatus("refreshing glauth")
        try:
            glauth.refresh()
        except snap.SnapError as e:
            self.unit.status = BlockedStatus(e.message)


if __name__ == "__main__":  # pragma: nocover
    main(GlauthCharm)
