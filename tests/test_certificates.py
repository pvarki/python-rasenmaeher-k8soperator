"""User mTLS certificate helpers and reconcile branches."""

import pytest

from k8soperator.app import app

TODO = pytest.mark.skip(reason="TODO: implement with k8soperator.controllers._certificates")


def test_manifests_grant_certificate_and_secret_access() -> None:
    """Users controller can manage Certificates and read user cert Secrets."""
    documents = app.manifests(include_webhooks=False)
    cluster_role = next(document for document in documents if document["kind"] == "ClusterRole")
    certificate_rule = next(rule for rule in cluster_role["rules"] if rule.get("resources") == ["certificates"])
    assert "delete" in certificate_rule["verbs"]
    secret_role = next(
        document
        for document in documents
        if document["kind"] == "Role" and document["metadata"]["namespace"] == "opendefence-external-certs"
    )
    assert secret_role["rules"] == [{"apiGroups": [""], "resources": ["secrets"], "verbs": ["get"]}]


@TODO
def test_wants_certificate() -> None:
    """Approved and not revoked -> True; unapproved or revoked -> False."""


@TODO
def test_desired_certificate() -> None:
    """Name, namespace, CN=callsign, RSA 4096, rotationPolicy Never, usages, issuerRef."""


@TODO
def test_public_key_fingerprint_parses_leaf() -> None:
    """Fingerprint comes from the leaf of a chain generated with cryptography."""


@TODO
async def test_reconcile_certificate_waits_until_ready() -> None:
    """Not Ready -> CertificateReady=False reason Issuing, no publicKey."""


@TODO
async def test_reconcile_certificate_records_ready_certificate() -> None:
    """Ready -> reads the Secret and writes publicKey, CertificateReady=True."""


@TODO
async def test_reconcile_certificate_removes_when_not_wanted() -> None:
    """Revoked or unapproved -> deletes the Certificate and clears publicKey."""
