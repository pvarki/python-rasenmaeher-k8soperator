"""Cloudcoil application for RASENMAEHER platform entities."""

from cloudcoil.application import Application, RBACRule, WebhookServer
from cloudcoil.controller import HealthServer
from cloudcoil.models.cert_manager.v1 import Certificate
from cloudcoil.models.kubernetes.core.v1 import Secret

from k8soperator.controllers import ALL_CONTROLLERS
from k8soperator.controllers._certificates import EXTERNAL_CERT_NAMESPACE
from k8soperator.models.v1alpha1 import UserBinding

app = Application(
    "opendefence-platform",
    leader_election=True,
    health=HealthServer(host="0.0.0.0", port=8080),  # nosec B104
    webhook=WebhookServer(tls_secret="operator-tls"),  # nosec B106
    resources=(UserBinding,),
    rules=(
        RBACRule(Certificate, verbs=("delete",), plural="certificates", scope="Namespaced", all_namespaces=True),
        RBACRule(Secret, verbs=("get",), plural="secrets", scope="Namespaced", namespace=EXTERNAL_CERT_NAMESPACE),
    ),
)
for controller in ALL_CONTROLLERS:
    app.include(controller)

if __name__ == "__main__":
    app.main()
