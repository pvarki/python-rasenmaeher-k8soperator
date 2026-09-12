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

On macOS, both Podman and Docker Desktop can provide the engine. Podman is the
default. Start your Podman machine first (run ``podman machine init`` once if
you do not have a machine)::

    podman machine start  # if the machine is stopped
    podman info
    task up

For Docker Desktop on macOS, start the application and select its Docker CLI
context. If you previously configured ``DOCKER_HOST`` for Podman, clear it
before checking that ``docker info`` reports the Docker Desktop engine::

    export KIND_EXPERIMENTAL_PROVIDER=docker
    docker info
    task up

Docker Desktop's built-in Kubernetes cluster is not needed: these tasks create
a separate kind cluster. The registry uses a published localhost port, and
kind nodes reach it over their container network; neither path requires direct
access to the VM's container IP addresses.

On Windows, run the development tools in a WSL2 Linux distribution, with the
checkout in its Linux filesystem (for example, ``~/devel/``). Install ``mise``
and run ``mise install`` there; ``bash``, ``git``, and ``python3`` must also be on
PATH (the Helm Tilt extension uses ``python3``). Run ``task``, ``tilt``,
``kubectl``, and ``uv`` inside that same distribution.

* **Docker Desktop:** use Linux containers and enable the WSL2 engine and
  integration for your development distribution in Docker Desktop settings.
  Follow `Docker's WSL2 setup
  <https://docs.docker.com/desktop/features/wsl/>`_. In the WSL terminal::

      export KIND_EXPERIMENTAL_PROVIDER=docker
      docker info
      task up

* **Podman:** start a Podman machine with root privileges enabled, as required
  by `kind on Windows
  <https://podman-desktop.io/docs/kind/configuring-podman-for-kind-on-windows>`_.
  Follow `Podman's WSL connection setup
  <https://podman-desktop.io/docs/podman/accessing-podman-from-another-wsl-instance>`_
  to give your development distribution access to the machine's rootful
  socket. Install a Linux Podman client executable named ``podman`` on PATH;
  an interactive shell alias is not enough for kind and Tilt subprocesses.
  For the default machine, run in the WSL terminal::

      export CONTAINER_HOST=unix:///mnt/wsl/podman-sockets/podman-machine-default/podman-root.sock
      export KIND_EXPERIMENTAL_PROVIDER=podman
      podman info
      task up

  ``CONTAINER_HOST`` selects remote mode even with a full Linux Podman client.
  Adjust the socket path for a custom machine, and retain this setting for
  subsequent lifecycle commands. ``podman info`` must succeed with socket
  access as your WSL user before starting the tasks.

WSL2 uses the Linux provider default (Docker). The Windows path above uses
Linux clients throughout; native PowerShell, cmd.exe, and Git Bash execution
are not currently supported by this development setup. The scripts need a
Unix shell, and Tilt's Podman extension emits POSIX shell commands. Native
support would also need to handle Git Bash container-path conversion and
Windows Python launcher setup for the Helm extension.

Validation so far covers the running macOS Podman stack and Linux Docker
build/push/pull and lifecycle checks. The Ubuntu CI job exercises kind and
Tilt with Docker. Docker Desktop on macOS and both WSL2 configurations still
need an end-to-end run on those hosts.

Override a platform default with ``KIND_EXPERIMENTAL_PROVIDER=docker`` or
``KIND_EXPERIMENTAL_PROVIDER=podman``; unset it to restore the default.
Keep the same setting for every lifecycle command, including ``task down``
and ``task clean``. Before changing engines, run ``task clean`` with the old
provider still selected. This
deletes the old development cluster and registry, releases port 5005, and
removes the exported CA. Then select the new provider and run ``task up``.
Both providers use the same kube context and CA path, so this checkout runs
one development cluster at a time.

``Taskfile.yml`` selects the provider with Task's native ``OS`` function and
exports it to kind. ``task runtime`` prints the selected provider; Tilt uses
the same task. Repeated ``task cluster:up`` reuses the cluster and repairs its
registry connection.
``tilt/Taskfile.cluster.yml`` calls kind's create, export, and delete commands
directly, using its default single-node cluster and ``--wait`` for startup
readiness. Task's ``status`` checks skip creation when the cluster or registry
already exists.
``tilt/connect-registry.sh`` contains only the network connection and per-node
registry configuration required by `kind's local registry setup
<https://kind.sigs.k8s.io/docs/user/local-registry/>`_. The containerd settings
are in ``tilt/registry-hosts.toml`` and Tilt's registry discovery metadata is in
``tilt/registry.yaml``.
The development registry is named ``rmk8soperator-registry``.
Host pushes use ``localhost:5005``; kind's containerd redirects pulls to the
registry container over the ``kind`` network.

Tilt uses Podman to build and push when the provider is ``podman``. Only the
local registry push disables TLS verification. The development image includes
Tilt's restart wrapper, so source sync and process restarts do not need Docker's
API or a Docker-compatible Podman socket. With ``docker``, Tilt uses Docker's
builder for the same development image.

``task`` with no arguments lists tasks. ``task up`` starts the registry, the
kind cluster, and Tilt. ``task down`` sends a stop signal to this checkout's
Tilt process and immediately deletes the cluster and its exported CA. The
registry remains running. ``task clean`` also removes the registry. Both
commands work from a second terminal while ``task up`` is running.

``task tilt:stop`` stops only Tilt, keeping the cluster and workloads.
``task tilt:down`` stops Tilt and deletes its managed resources while keeping
the cluster. Tilt's own ``tilt down`` command only deletes resources; it does
not stop a running ``tilt up`` process or release its web port.

If startup reports that port 10350 is already in use, run ``task tilt:stop``
before retrying ``task up``. Teardown checks the session's Tiltfile path and
refuses to stop a different checkout's Tilt. To run beside another project,
set ``TILT_PORT`` to a free port and retain that setting for up and down::

    export TILT_PORT=10351
    task up

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
