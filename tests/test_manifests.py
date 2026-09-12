"""Offline Application manifests."""

from dataclasses import replace

from rmk8soperator.app import app

TEST_CA_PEM = b"-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n"


def test_manifests_include_four_crds_and_leader_election_rbac() -> None:
    """Generated manifests install the four CRDs and lease permissions."""
    documents = app.manifests(include_webhooks=False)
    kinds: dict[str, list[str]] = {}
    for document in documents:
        kinds.setdefault(document["kind"], []).append(document["metadata"]["name"])
    assert set(kinds["CustomResourceDefinition"]) == {
        "users.platform.opendefense.fi",
        "groups.platform.opendefense.fi",
        "roles.platform.opendefense.fi",
        "invites.platform.opendefense.fi",
    }
    assert "opendefense-platform" in kinds["ServiceAccount"]
    assert any(name.endswith(".default") for name in kinds["ClusterRole"])
    role = next(document for document in documents if document["kind"] == "Role")
    resources = [rule.get("resources") for rule in role["rules"]]
    assert any(resource == ["leases"] for resource in resources)
    assert "ValidatingWebhookConfiguration" not in kinds
    assert "Service" not in kinds


def test_manifests_include_group_validating_webhook() -> None:
    """TLS-backed manifests register Group CREATE/UPDATE/DELETE admission."""
    original = app.webhook
    assert original is not None
    app.webhook = replace(original, ca_bundle=TEST_CA_PEM)
    try:
        documents = app.manifests(image="example.invalid/rmk8soperator:test")
    finally:
        app.webhook = original
    kinds = {document["kind"] for document in documents}
    assert "ValidatingWebhookConfiguration" in kinds
    assert "Service" in kinds
    assert "Deployment" in kinds
    webhook = next(document for document in documents if document["kind"] == "ValidatingWebhookConfiguration")
    policy = webhook["webhooks"][0]
    rule = policy["rules"][0]
    assert rule["apiGroups"] == ["platform.opendefense.fi"]
    assert rule["resources"] == ["groups"]
    assert set(rule["operations"]) == {"CREATE", "UPDATE", "DELETE"}
    deployment = next(document for document in documents if document["kind"] == "Deployment")
    pod_spec = deployment["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]
    assert container["volumeMounts"][0]["name"] == "webhook-tls"
    assert pod_spec["volumes"][0]["secret"]["secretName"] == original.tls_secret
