#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test glauth charm."""

import pytest
from pytest_operator.plugin import OpsTest

GLAUTH = "glauth"
SERIES = ["jammy"]


@pytest.mark.abort_on_fail
@pytest.mark.parametrize("series", SERIES)
@pytest.mark.skip_if_deployed
async def test_deploy(ops_test: OpsTest, series: str, glauth_charm):
    """Test glauth charm deployment."""
    # Build and Deploy glauth
    await ops_test.model.deploy(
        str(await glauth_charm),
        application_name=GLAUTH,
        num_units=1,
        series=series,
    )
    # issuing update_status just to trigger an event
    async with ops_test.fast_forward():
        await ops_test.model.wait_for_idle(apps=[GLAUTH], status="active", timeout=1000)
        assert ops_test.model.applications[GLAUTH].units[0].workload_status == "active"
