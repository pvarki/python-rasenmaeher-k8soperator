"""Cloudcoil application for RASENMAEHER platform entities."""

from cloudcoil.application import Application, WebhookServer
from cloudcoil.controller import HealthServer

from rmk8soperator.controllers import ALL_CONTROLLERS

app = Application(
    "opendefense-platform",
    leader_election=True,
    health=HealthServer(host="0.0.0.0", port=8080),  # nosec B104
    webhook=WebhookServer(tls_secret="operator-tls"),  # nosec B106
)
for controller in ALL_CONTROLLERS:
    app.include(controller)

if __name__ == "__main__":
    app.main()
