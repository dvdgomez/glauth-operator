#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test default charm events such as upgrade charm, install, etc."""

import unittest
from unittest.mock import patch

from charm import GlauthCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    """Unit test glauth charm."""

    def setUp(self) -> None:
        """Set up unit test."""
        self.harness = Harness(GlauthCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    @patch("glauth.__getattr__", return_value="v1.0.0")
    @patch("glauth.__getattr__", return_value=True)
    @patch("glauth.install")
    def test_install(self, *_) -> None:
        """Test install behavior."""
        self.harness.charm.on.install.emit()
        self.assertEqual(self.harness.charm.unit.status, ActiveStatus("glauth ready"))
