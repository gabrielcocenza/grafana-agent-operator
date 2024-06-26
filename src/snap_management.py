#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more at: https://juju.is/docs/sdk

"""Snap Installation Module.

Modified from https://github.com/canonical/k8s-operator/blob/main/charms/worker/k8s/src/snap.py
"""


import logging
import platform

import charms.operator_libs_linux.v2.snap as snap_lib

# Log messages can be retrieved using juju debug-log
log = logging.getLogger(__name__)


# Map of the grafana-agent snap revision to install for given architectures and strict mode.
_grafana_agent_snap_name = "grafana-agent"
_grafana_agent_snaps = {
    # (confinement, arch): revision
    ("strict", "amd64"): 16,
    ("strict", "arm64"): 23,
}


class SnapSpecError(Exception):
    """Custom exception type for errors related to the snap spec."""

    pass


def install_ga_snap(classic: bool):
    """Looks up system details and installs the appropriate grafana-agent snap revision."""
    arch = get_system_arch()
    confinement = "classic" if classic else "strict"
    try:
        revision = str(_grafana_agent_snaps[(confinement, arch)])
    except KeyError as e:
        raise SnapSpecError(
            f"Snap spec not found for arch={arch} and confinement={confinement}"
        ) from e
    _install_snap(name=_grafana_agent_snap_name, revision=revision, classic=classic)


def _install_snap(
    name: str,
    revision: str,
    classic: bool = False,
):
    """Install and pin the given snap revision.

    The revision will be held, i.e. it won't be automatically updated any time a new revision is released.
    """
    cache = snap_lib.SnapCache()
    snap = cache[name]
    log.info(
        f"Ensuring {name} snap is installed at revision={revision}"
        f" with classic confinement={classic}"
    )
    snap.ensure(state=snap_lib.SnapState.Present, revision=revision, classic=classic)
    snap.hold()


def get_system_arch() -> str:
    """Returns the architecture of this machine, mapping some values to amd64 or arm64.

    If platform is x86_64 or amd64, it returns amd64.
    If platform is aarch64, arm64, armv8b, or armv8l, it returns arm64.
    """
    arch = platform.processor()
    if arch in ["x86_64", "amd64"]:
        arch = "amd64"
    elif arch in ["aarch64", "arm64", "armv8b", "armv8l"]:
        arch = "arm64"
    # else: keep arch as is
    return arch
