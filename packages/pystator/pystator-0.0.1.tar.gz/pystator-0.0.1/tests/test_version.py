"""Basic tests for pystator."""

from __future__ import annotations

import pystator


def test_version_is_string() -> None:
    assert isinstance(pystator.__version__, str)
    assert len(pystator.__version__) >= 5  # e.g. 0.1.0
