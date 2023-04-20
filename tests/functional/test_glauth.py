#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test glauth snap functionality."""

import unittest

import glauth


class TestGlauth(unittest.TestCase):
    """Test glauth charm functionality."""

    def setUp(self) -> None:
        """Install glauth snap."""
        self.glauth = glauth
        if not self.glauth.installed():
            self.glauth.install()

    def test_install(self):
        """Validate snap install."""
        self.assertTrue(glauth.installed())
        self.assertTrue(type(glauth.version()), str)
