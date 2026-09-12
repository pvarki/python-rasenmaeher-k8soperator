=======================
rasenmaeher-k8soperator
=======================

K8s Operator and CRDs with core RASENMAEHER entities

The operator requires Python 3.14+ (cloudcoil). It owns cluster-scoped
``platform.opendefense.fi/v1alpha1`` resources: User, Group, Role, and Invite.
Integrations watch those objects; this process resolves name references into
status (name + Kubernetes UID) and reports Ready conditions. A validating
admission webhook rejects Group ``parentRef`` values that self-parent, form a
cycle, or name a missing ancestor, and rejects deleting a group that is still
named as ``parentRef`` by another group.

CLI
---

The installed ``rmk8soperator`` command (and ``python -m rmk8soperator``) forwards
to cloudcoil's ``manifests``, ``install``, and ``run`` entry point::

    # Offline: CRDs and RBAC, no kubeconfig or TLS material required
    rmk8soperator manifests --without-webhooks

    # Full install: CRDs, RBAC, Service, Deployment, and Group admission
    # Create namespace and TLS Secret operator-tls first. The serving
    # certificate must cover opendefense-platform.<namespace>.svc.
    CLOUDCOIL_NAMESPACE=opendefence-system \
      rmk8soperator install --image ghcr.io/example/rmk8soperator:latest --ca-file /path/to/ca.crt

    # Offline manifests including webhook registration (same TLS CA)
    rmk8soperator manifests --image ghcr.io/example/rmk8soperator:latest --ca-file /path/to/ca.crt

    # Run the controllers (kubeconfig locally, ServiceAccount in-cluster)
    CLOUDCOIL_NAMESPACE=opendefence-system rmk8soperator run

``CLOUDCOIL_NAMESPACE`` is the operator's Lease/Deployment namespace. The CRDs
themselves are cluster-scoped. Production containers with no arguments run
``rmk8soperator run``. Admission serves on every replica, independently of
leader election. Generated webhook configurations fail closed, so the HTTPS
listener and ``operator-tls`` Secret must be ready before Group writes.

Sample objects (roles, a group, users ``bob`` and ``charlie``, and an invite) live in
``examples/demo.yaml``::

    kubectl apply -f examples/demo.yaml
    kubectl get odrole,odgroup,oduser,odinvite


Docker and Podman
-----------------

For more controlled deployments and to get rid of "works on my computer" -syndrome, we always
make sure our software works under docker.

It's also a quick way to get started with a standard development environment.

Each command block offers Docker and Podman alternatives; run only the block
for your chosen engine. Both engines use the same Dockerfiles.

SSH agent forwarding
^^^^^^^^^^^^^^^^^^^^

Docker builds use buildkit_ (Podman does not need this setting)::

    export DOCKER_BUILDKIT=1

.. _buildkit: https://docs.docker.com/develop/develop-images/build_enhancements/

And also the exact way for forwarding agent to running instance is different on OSX::

    export DOCKER_SSHAGENT="-v /run/host-services/ssh-auth.sock:/run/host-services/ssh-auth.sock -e SSH_AUTH_SOCK=/run/host-services/ssh-auth.sock"

and Linux::

    export DOCKER_SSHAGENT="-v $SSH_AUTH_SOCK:$SSH_AUTH_SOCK -e SSH_AUTH_SOCK"

For Podman on Linux, use an agent socket accessible on the engine host::

    export PODMAN_SSHAGENT="-v $SSH_AUTH_SOCK:$SSH_AUTH_SOCK -e SSH_AUTH_SOCK"

For Podman Machine on macOS or Windows, omit runtime agent forwarding when using
the generated project's public dependencies::

    export PODMAN_SSHAGENT=""

The macOS launchd agent socket cannot be bind-mounted from inside the Linux VM.
If you add private SSH dependencies, configure an agent inside the VM and set
``PODMAN_SSHAGENT`` using its socket path, or run the commands on a Linux host
with an SSH agent. Build-time ``--ssh default`` is separate from runtime mounts.
Docker Desktop's ``/run/host-services/ssh-auth.sock`` path is specific to Docker Desktop.
See the `Podman build options <https://docs.podman.io/en/stable/markdown/podman-build.1.html>`_
for SSH forwarding options.

Creating a development container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build image, create container and start it::

    # Docker
    docker build --ssh default --target devel_shell -t rmk8soperator:devel_shell .
    docker create --name rmk8soperator_devel -v "$(pwd):/app" -it $(echo $DOCKER_SSHAGENT) rmk8soperator:devel_shell
    docker start -i rmk8soperator_devel

    # Podman alternative
    podman build --ssh default --target devel_shell -t rmk8soperator:devel_shell .
    podman create --name rmk8soperator_devel -v "$(pwd):/app" -it $(echo $PODMAN_SSHAGENT) rmk8soperator:devel_shell
    podman start -i rmk8soperator_devel

prek considerations
^^^^^^^^^^^^^^^^^^^^^^^^^

If working in Docker instead of native env you need to run the prek checks in docker too::

    # Docker
    docker exec -i rmk8soperator_devel /bin/bash -c "uv run --locked prek install --install-hooks"
    docker exec -i rmk8soperator_devel /bin/bash -c "uv run --locked prek run --all-files"

    # Podman alternative
    podman exec -i rmk8soperator_devel /bin/bash -c "uv run --locked prek install --install-hooks"
    podman exec -i rmk8soperator_devel /bin/bash -c "uv run --locked prek run --all-files"

You need to have the container running, see above. Or alternatively use the docker run syntax but using
the running container is faster::

    # Docker
    docker run --rm -it -v "$(pwd):/app" rmk8soperator:devel_shell -c "uv run --locked prek run --all-files"

    # Podman alternative
    podman run --rm -it -v "$(pwd):/app" rmk8soperator:devel_shell -c "uv run --locked prek run --all-files"

Test suite
^^^^^^^^^^

You can use the devel shell to run py.test when doing development, for CI use
the "tox" target in the Dockerfile::

    # Docker
    docker build --ssh default --target tox -t rmk8soperator:tox .
    docker run --rm -it -v "$(pwd):/app" $(echo $DOCKER_SSHAGENT) rmk8soperator:tox

    # Podman alternative
    podman build --ssh default --target tox -t rmk8soperator:tox .
    podman run --rm -it -v "$(pwd):/app" $(echo $PODMAN_SSHAGENT) rmk8soperator:tox

Production docker
^^^^^^^^^^^^^^^^^

GitHub Actions builds the test and production targets from both Dockerfile_alpine
and Dockerfile_debian for pull requests. Publishing uses the default Dockerfile
(Alpine) for both linux/amd64 and linux/arm64. See the CI configuration below.

There's a "production" target as well for running the application. Tag the image
with the project version::

    # Docker
    docker build --ssh default --target production -t rmk8soperator:0.1.0-260912 .
    docker run -it --name rmk8soperator rmk8soperator:0.1.0-260912

    # Podman alternative
    podman build --ssh default --target production -t rmk8soperator:0.1.0-260912 .
    podman run -it --name rmk8soperator rmk8soperator:0.1.0-260912

Alpine considerations
^^^^^^^^^^^^^^^^^^^^^

Alpine images are much more lightweight than Debian/Ubuntu ones so they are preferred where possible.
There are a few potential issues however:

  - Compiled extensions not available as wheels are built from source in the builder stage.
  - Compiled extensions not compiling under Alpine. Alpine does not have certain nonstandard extensions to libc
    enabled by default, poorly written extensions will fail to compile because they depend on these extensions
    and do not explicitly request them to be enabled.
  - Commit uv.lock; Docker builds use uv sync --locked to detect stale dependency metadata.

Development
-----------

TLDR:

- Install uv: https://docs.astral.sh/uv/getting-started/installation/
- Install project dependencies and prek hooks (also attempted during generation)::

    uv sync --locked
    uv run --locked prek install --install-hooks

- Run checks and tests::

    uv run --locked prek run --all-files
    uv run --locked pytest -v

Local cluster with Tilt
^^^^^^^^^^^^^^^^^^^^^^^

``mise.toml`` installs ``helm``, ``kind``, ``kubectl``, ``task``, ``tilt``, and
``uv``. On Linux, the local environment defaults to standard Docker Engine.
Start Docker and make sure ``docker info`` succeeds as your user; Docker Desktop
and Podman are not required. Create a kind cluster with a local registry (kube
context ``kind-rmk8soperator``), then run the operator under Tilt::

    mise install
    task up

On macOS, the default is Podman. Start your Podman machine first::

    podman machine start  # if the machine is stopped
    task up

Override either default with ``KIND_EXPERIMENTAL_PROVIDER=docker`` or
``KIND_EXPERIMENTAL_PROVIDER=podman``. Keep the same setting for every lifecycle
command, including ``task down`` and ``task clean``::

    export KIND_EXPERIMENTAL_PROVIDER=docker
    task up

The tasks and Tilt use the same provider selection. Cluster creation uses kind
directly and does not require ctlptl. Repeated ``task cluster:up`` reuses the
cluster and repairs its registry connection.
The registry retains the name ``ctlptl-registry`` to reuse existing image data.
Host pushes use ``localhost:5005``; kind's containerd redirects pulls to the
registry container over the ``kind`` network.

Tilt uses Podman to build and push when the provider is ``podman``. Only the
local registry push disables TLS verification. The development image includes
Tilt's restart wrapper, so source sync and process restarts do not need Docker's
API or a Docker-compatible Podman socket. With ``docker``, Tilt uses Docker's
builder for the same development image.

``task`` with no arguments lists tasks. ``task up`` starts the registry, the
kind cluster, and Tilt. Exit Tilt with Ctrl+C before cleanup. ``task down``
deletes the cluster and its exported CA but leaves the registry running.
``task clean`` also removes the registry. ``task tilt:down`` deletes only the
Tilt-managed resources while keeping the cluster.

Cluster and registry have short aliases: ``task c:up`` / ``task c:d`` and
``task r:up`` / ``task r:d`` (also ``c:u``, ``r:u``).

Tilt installs cert-manager, issues a local CA and serving certificate into
Secret ``operator-tls``, then applies CRDs, RBAC, the operator Deployment, and
the Group ``ValidatingWebhookConfiguration`` from
``rmk8soperator manifests --image rmk8soperator --ca-file``. Changes under
``src/`` are synced into the running pod and the process is restarted (the
operator does not auto-reload like Flask). Apply sample objects from the Tilt
UI by triggering the ``demo`` resource (manual), or with
``kubectl apply -f examples/demo.yaml``. The health listener is forwarded to
``http://127.0.0.1:18080/readyz``. Override the host port with
``OPERATOR_HEALTH_PORT=18081 task up`` if needed.

Ruff handles linting and formatting; Pyrefly checks types. Run them individually with::

    uv run --locked ruff check src tests
    uv run --locked ruff format src tests
    uv run --locked pyrefly check

Use ``uv add PACKAGE`` for runtime dependencies and ``uv add --dev PACKAGE`` for
development tools. Commit both pyproject.toml and uv.lock after dependency changes.
Run ``uv lock`` after manually editing dependencies, and ``uv build`` to produce
wheel and source distributions.

Versions follow pvarki's Python convention ``MAJOR.MINOR.PATCH+YYMMDD``.
The ``release`` part records the release date and updates automatically when
bumping major, minor or patch. Container tags use ``-`` instead of ``+``;
the shared publisher normalizes this, and bump-my-version keeps the README's
local image tags in the same format.

Preview or bump the project version with bump-my-version::

    uv run --locked bump-my-version show-bump
    uv run --locked bump-my-version bump patch
    uv lock

Use ``minor`` or ``major`` instead of ``patch`` as needed, or ``release`` to
refresh only the date on a later day. The configuration in
.bumpversion.toml updates the package metadata, module version, version test,
and production image tags in this README. Commit these changes together with
uv.lock; version bumping does not automatically create a commit or Git tag.

The hook configuration remains in .pre-commit-config.yaml, which prek supports.
System hooks invoke tools through uv so they use the project environment.
