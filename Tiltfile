# -*- mode: Python -*-
# Local operator loop: kind cluster + local registry + live_update image.
#
# Start with `task up` (registry + kind-rmk8soperator + Tilt). The lifecycle
# commands are in tilt/Taskfile.*.yml. Image name must match
# `rmk8soperator manifests --image`. live_update follows
# https://docs.tilt.dev/example_python.html ; the tilt image includes a restart
# wrapper because this process does not auto-reload like Flask.
#
# cert-manager issues the local CA; export-webhook-ca writes tilt/.certs/ca.crt
# for `rmk8soperator manifests --image --ca-file` (Service, Deployment, admission).

load("ext://podman", "podman_build")
load("ext://namespace", "namespace_create")
load("ext://helm_resource", "helm_resource", "helm_repo")

OPERATOR_NS = "opendefence-system"
OPERATOR_IMAGE = "rmk8soperator"
KIND_CONTEXT = "kind-rmk8soperator"
CA_FILE = "tilt/.certs/ca.crt"
CERT_MANAGER_VERSION = "v1.21.1"
watch_file("Taskfile.yml")
RUNTIME = str(local(["task", "--silent", "runtime"], quiet=True)).strip()
if RUNTIME == "podman":
    docker_prune_settings(disable=True)
# Host bytecode must neither trigger restarts nor be synced into the container.
watch_settings(ignore=["**/__pycache__/**", "**/*.py[cod]"])

allow_k8s_contexts(KIND_CONTEXT)
if k8s_context() != KIND_CONTEXT:
    fail("Use task tilt:up or tilt up --context %s" % KIND_CONTEXT)
# The cert-manager chart install needs more than the 30s default.
update_settings(k8s_upsert_timeout_secs=180)
namespace_create(OPERATOR_NS)
k8s_resource(
    new_name="operator-ns",
    objects=["%s:Namespace:default" % OPERATOR_NS],
)

helm_repo("jetstack", "https://charts.jetstack.io")
helm_resource(
    "cert-manager",
    "jetstack/cert-manager",
    namespace="cert-manager",
    flags=[
        "--create-namespace",
        "--version",
        CERT_MANAGER_VERSION,
        "--set",
        "crds.enabled=true",
    ],
    resource_deps=["jetstack"],
)

k8s_yaml("tilt/webhook-certs.yaml")
k8s_resource(
    new_name="operator-certs",
    objects=[
        "operator-selfsigned:issuer:%s" % OPERATOR_NS,
        "operator-ca:certificate:%s" % OPERATOR_NS,
        "operator-ca:issuer:%s" % OPERATOR_NS,
        "operator-tls:certificate:%s" % OPERATOR_NS,
    ],
    resource_deps=["cert-manager", "operator-ns"],
)

local_resource(
    "export-webhook-ca",
    "./tilt/export-ca.sh",
    deps=["tilt/export-ca.sh"],
    resource_deps=["operator-certs"],
    env={
        "CLOUDCOIL_NAMESPACE": OPERATOR_NS,
        "KIND_CONTEXT": KIND_CONTEXT,
    },
)

watch_file(CA_FILE)
# On a fresh cluster, let cert-manager and export-webhook-ca run first.
# Writing the watched CA file reloads this Tiltfile to add the operator.
if not os.path.exists(CA_FILE):
    exit("Waiting for cert-manager to issue the local webhook CA")

watch_file("src/rmk8soperator/models")
k8s_yaml(
    local(
        "uv run --locked rmk8soperator manifests --image %s --ca-file %s"
        % (OPERATOR_IMAGE, CA_FILE),
        env={"CLOUDCOIL_NAMESPACE": OPERATOR_NS},
        quiet=True,
    )
)

k8s_resource(
    new_name="operator-crds-rbac",
    objects=[
        "groups.platform.opendefence.fi:CustomResourceDefinition:default",
        "invites.platform.opendefence.fi:CustomResourceDefinition:default",
        "roles.platform.opendefence.fi:CustomResourceDefinition:default",
        "users.platform.opendefence.fi:CustomResourceDefinition:default",
        "opendefence-platform:serviceaccount:%s" % OPERATOR_NS,
        "opendefence-platform.%s:clusterrole:default" % OPERATOR_NS,
        "opendefence-platform.%s:clusterrolebinding:default" % OPERATOR_NS,
        "opendefence-platform.%s:role:%s" % (OPERATOR_NS, OPERATOR_NS),
        "opendefence-platform.%s:rolebinding:%s" % (OPERATOR_NS, OPERATOR_NS),
    ],
    resource_deps=["operator-ns"],
)

live_update_steps = [
    sync("./src", "/app/src"),
    sync("./pyproject.toml", "/app/pyproject.toml"),
    sync("./uv.lock", "/app/uv.lock"),
    run(
        "uv sync --locked --no-dev",
        trigger=["./pyproject.toml", "./uv.lock"],
    ),
    run("date > /tmp/.restart-proc"),
]

image_deps = ["src", "pyproject.toml", "uv.lock", "README.rst", "docker"]
# Both builders use the restart wrapper included in the development image.
if RUNTIME == "podman":
    podman_build(
        OPERATOR_IMAGE,
        ".",
        extra_flags=["--file", "Dockerfile_alpine", "--target", "tilt"],
        push_extra_flags=["--tls-verify=false"],
        deps=image_deps + ["Dockerfile_alpine", ".dockerignore"],
        live_update=live_update_steps,
    )
else:
    docker_build(
        OPERATOR_IMAGE,
        ".",
        dockerfile="Dockerfile_alpine",
        target="tilt",
        only=image_deps,
        live_update=live_update_steps,
    )

k8s_resource(
    "opendefence-platform",
    objects=[
        "opendefence-platform.%s.cloudcoil.io:ValidatingWebhookConfiguration:default"
        % OPERATOR_NS,
    ],
    port_forwards="%s:8080" % os.getenv("OPERATOR_HEALTH_PORT", "18080"),
    resource_deps=["operator-crds-rbac", "export-webhook-ca"],
)

local_resource(
    "webhook-ready",
    "./tilt/wait-webhook.sh",
    deps=["tilt/wait-webhook.sh"],
    resource_deps=["opendefence-platform"],
    env={"KIND_CONTEXT": KIND_CONTEXT},
)

k8s_yaml("examples/demo.yaml")
k8s_resource(
    new_name="demo",
    objects=[
        "superadmin:Role:default",
        "group-admin:Role:default",
        "role-admin:Role:default",
        "group-admin:Group:default",
        "bob:User:default",
        "charlie:User:default",
        "onboarding:Invite:default",
    ],
    resource_deps=["webhook-ready"],
    trigger_mode=TRIGGER_MODE_MANUAL,
    auto_init=False,
)
