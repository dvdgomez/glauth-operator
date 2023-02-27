#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test glauth snap functionality."""

import subprocess
import unittest
from pathlib import Path

from glauth import Glauth


class TestGlauth(unittest.TestCase):
    """Test glauth charm functionality."""

    def setUp(self) -> None:
        """Install glauth snap."""
        self.glauth = Glauth()
        if not self.glauth.installed:
            self.glauth.install()

    def test_install(self):
        """Validate snap install."""
        self.assertTrue(Path("/snap/bin/glauth").exists())
        self.assertEqual(subprocess.check_call(["/snap/bin/glauth", "--version"]), 0)
