"""Only explicit synthetic/software tests are collected. Deny outbound sockets."""
import os
import random
from pathlib import Path
import socket
import sys

import numpy as np
import pytest

if os.environ.get('SBX_INSTALLED') != '1':
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'upstream'))


@pytest.fixture(autouse=True)
def deterministic_offline_test(monkeypatch):
    def forbidden(*args, **kwargs):
        raise RuntimeError('network access forbidden in sandbox software tests')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    np.random.seed(20261019)
    random.seed(20261019)


def pytest_sessionfinish(session, exitstatus):
    """A missing scientific backend must fail instead of producing a green skip."""
    reporter = session.config.pluginmanager.getplugin('terminalreporter')
    if reporter and reporter.stats.get('skipped'):
        session.exitstatus = 1
