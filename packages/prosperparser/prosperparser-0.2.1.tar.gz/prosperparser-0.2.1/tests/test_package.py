from __future__ import annotations

import importlib.metadata

import prosperparser as m


def test_version():
    assert importlib.metadata.version("prosperparser") == m.__version__
