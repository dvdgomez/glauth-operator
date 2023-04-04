#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""GLAuth Operator Charm."""

import logging

import glauth
from charms.operator_libs_linux.v1 import snap
from ops.charm import CharmBase, RelationJoinedEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, ModelError

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
        self.framework.observe(
            self.on.ldap_client_relation_joined, self._on_ldap_client_relation_joined
        )

    def _install(self, _):
        """Install glauth."""
        self.unit.status = MaintenanceStatus("installing glauth")
        try:
            glauth.install()
            self.unit.set_workload_version(glauth.version)
            self.unit.status = ActiveStatus("glauth ready")
        except snap.SnapError as e:
            self.unit.status = BlockedStatus(e.message)

    def _on_ldap_client_relation_joined(self, event: RelationJoinedEvent):
        """Handle ldap-client relation joined event."""
        self.unit.status = MaintenanceStatus("reconfiguring glauth")
        # Check model for GLAuth config resource
        try:
            resource_path = self.model.resources.fetch("config")
        except ModelError:
            logger.debug("No config resource supplied")
            resource_path = None
        glauth.set_config(resource_path)
        # GLAuth URI to send
        ldap_uri = glauth.get_uri()
        # Get CA Cert from GLAuth Snap
        ca_cert = glauth.load(self.model.config["cert"], self.model.config["key"], ldap_uri)
        cc_content = {"ca-cert": ca_cert}
        ldbd_content = {"ldap-default-bind-dn": self.model.config["ldap-default-bind-dn"]}
        lp_content = {"ldap-password": self.model.config["ldap-password"]}
        # Create Secrets
        cc_secret = self.app.add_secret(cc_content, label="ca-cert")
        logger.debug("created secret %s", cc_secret)
        ldbd_secret = self.app.add_secret(ldbd_content, label="ldap-default-bind-dn")
        logger.debug("created secret %s", ldbd_secret)
        lp_secret = self.app.add_secret(lp_content, label="ldap-password")
        logger.debug("created secret %s", lp_secret)
        cc_secret.grant(event.relation)
        ldbd_secret.grant(event.relation)
        lp_secret.grant(event.relation)
        event.relation.data[self.app]["ca-cert"] = cc_secret.id
        event.relation.data[self.app]["ldap-default-bind-dn"] = ldbd_secret.id
        event.relation.data[self.app]["ldap-password"] = lp_secret.id
        # Configuration data update
        ldap_relation = self.model.get_relation("ldap-client")
        ldap_relation.data[self.app].update(
            {
                "basedn": self.model.config["ldap-search-base"],
                "domain": self.model.config["domain"],
                "ldap-uri": ldap_uri,
            }
        )
        self.unit.status = ActiveStatus("glauth ready")

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
