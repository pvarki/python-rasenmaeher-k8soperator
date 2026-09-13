"""Package level tests"""

from rmk8soperator import __version__


def test_version() -> None:
    """Make sure version matches expected"""
    assert __version__ == "0.1.1+260913"
