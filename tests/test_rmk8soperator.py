"""Package level tests"""

from k8soperator import __version__


def test_version() -> None:
    """Make sure version matches expected"""
    assert __version__ == "0.1.2+260913"
