=======================
rasenmaeher-k8soperator
=======================

Kubernetes operator for the OpenDefense platform. It owns `platform.opendefence.fi`-group
resources, such as User, Group, Role, and Invite, and keeps their status and references
consistent. Integrations create namespaced UserBinding objects to record that they have
taken a User into account; this operator watches those bindings and reports their
``Synced`` conditions on the User, but does not admit or reconcile UserBinding itself.

Quickstart
----------

Install `mise`_ so the tools in ``mise.toml`` (``helm``, ``kind``, ``kubectl``,
``task``, ``tilt``, ``uv``) are on PATH. On Linux the default container engine
is Docker; start it and confirm ``docker info`` succeeds as your user.

.. _mise: https://mise.jdx.dev/

::

    mise install
    uv sync --locked
    uv run --locked prek install --install-hooks
    task up

``task up`` starts a local registry, the kind cluster (kube context
``kind-rmk8soperator``), and Tilt. Open the Tilt UI (default
http://127.0.0.1:10350/). Health is forwarded to
http://127.0.0.1:18080/readyz.

Apply the sample objects (roles, a group, users ``bob`` and ``charlie``, an
invite, and a UserBinding) from the Tilt UI by triggering the ``demo`` resource
(manual), or with kubectl::

    kubectl apply -f examples/demo.yaml
    kubectl get odrole,odgroup,oduser,odinvite,odub

Everyday commands (``task`` with no arguments lists them):

- ``task down`` — stop Tilt and delete the cluster; the registry stays for the
  next ``task up``
- ``task clean`` — also remove the registry
- ``task tilt:stop`` — stop Tilt only, keep cluster and workloads

Both ``task down`` and ``task clean`` work from a second terminal while
``task up`` is running.

Ways of working
---------------

Develop on the host with uv. prek runs the same checks CI does: Ruff lint and
format, Pyrefly types, conventional commit messages, lockfile freshness, and
the rest of ``.pre-commit-config.yaml``. Do not commit to the default branch
(the ``no-commit-to-branch`` hook blocks it).

::

    uv run --locked prek run --all-files
    uv run --locked pytest -v
    uv run --locked ruff check src tests
    uv run --locked ruff format src tests
    uv run --locked pyrefly check

Tilt live-syncs ``src/`` (and ``pyproject.toml`` / ``uv.lock``) into the
running operator pod and restarts the process. The operator does not
auto-reload like Flask.

Use ``uv add PACKAGE`` for runtime dependencies and ``uv add --dev PACKAGE``
for development tools. Commit ``pyproject.toml`` and ``uv.lock`` together.
Run ``uv lock`` after editing dependencies by hand, and ``uv build`` to produce
wheel and source distributions.

Local cluster
-------------

``task runtime`` prints the selected engine. Linux defaults to Docker. On
macOS, Task uses Docker when Docker Desktop's socket exists at
``$HOME/Library/Containers/com.docker.docker/Data/backend.sock`` and otherwise
defaults to Podman. Override with ``KIND_EXPERIMENTAL_PROVIDER=docker`` or
``podman``; keep the same value for every lifecycle command, including
``task down`` and ``task clean``. This checkout runs one development cluster at
a time. Before switching engines, ``task clean`` with the old provider still
selected.

On macOS with Podman, start the machine first (``podman machine init`` once if
needed)::

    podman machine start  # if the machine is stopped
    podman info
    task up

On macOS with Docker Desktop, start the app and use its Docker CLI context.
Docker Desktop's built-in Kubernetes cluster is not used; these tasks create a
separate kind cluster.

On Windows, run the tools in a WSL2 Linux distribution with the checkout on the
Linux filesystem. Native PowerShell, cmd.exe, and Git Bash are not supported.
``bash``, ``git``, and ``python3`` must be on PATH (Tilt's Helm extension uses
``python3``).

* **Docker Desktop:** Linux containers, WSL2 engine, and integration for your
  distro. Set ``KIND_EXPERIMENTAL_PROVIDER=docker`` and run ``docker info``
  then ``task up``.
* **Podman:** a rootful Podman machine, a Linux ``podman`` binary on PATH (not
  a shell alias), and ``CONTAINER_HOST`` pointing at that machine's root
  socket. Set ``KIND_EXPERIMENTAL_PROVIDER=podman`` and run ``podman info``
  then ``task up``.

The Ubuntu CI job exercises kind and Tilt with Docker. Validation so far also
covers the running macOS Podman stack and Linux Docker lifecycle. Docker
Desktop on macOS and both WSL2 setups still need an end-to-end run on those
hosts.

If port 10350 is already in use, ``task tilt:stop`` then retry ``task up``.
Teardown matches this checkout's Tiltfile and will not stop another project's
Tilt. To run beside another project::

    export TILT_PORT=10351
    task up

Override the health forward with ``OPERATOR_HEALTH_PORT=18081 task up`` if
needed. ``task tilt:down`` stops Tilt and deletes its managed resources while
keeping the kind cluster. Tilt's own ``tilt down`` only deletes resources; it
does not stop a running ``tilt up`` or release its web port.

Cluster and registry aliases: ``task c:up`` / ``task c:d`` and ``task r:up`` /
``task r:d`` (also ``c:u``, ``r:u``). Repeated ``task cluster:up`` reuses the
cluster and repairs its registry connection. The registry container is
``rmk8soperator-registry``. Host pushes use ``localhost:5005``; kind nodes pull
over the ``kind`` network. Tilt builds the development image (Alpine ``tilt``
target, with a restart wrapper) through Docker or Podman depending on the
provider.

Tilt installs cert-manager, issues a local CA and serving certificate into
Secret ``operator-tls``, then applies CRDs, RBAC, the operator Deployment, and
the Group ``ValidatingWebhookConfiguration`` from
``rmk8soperator manifests --image rmk8soperator --ca-file``. The
``webhook-ready`` step then polls the webhook with a server-side dry run;
the ``demo`` resource waits for it, because Service traffic to the fail-closed
Group webhook is refused until the endpoint of the ready pod is programmed.

CLI
---

The installed ``rmk8soperator`` command (and ``python -m rmk8soperator``)
forwards to cloudcoil's ``manifests``, ``install``, and ``run`` entry points::

    # Offline: CRDs and RBAC, no kubeconfig or TLS material required
    rmk8soperator manifests --without-webhooks

    # Full install: CRDs, RBAC, Service, Deployment, and Group admission
    # Create namespace and TLS Secret operator-tls first. The serving
    # certificate must cover opendefence-platform.<namespace>.svc.
    CLOUDCOIL_NAMESPACE=opendefence-system \
      rmk8soperator install --image ghcr.io/example/rmk8soperator:latest --ca-file /path/to/ca.crt

    # Offline manifests including webhook registration (same TLS CA)
    rmk8soperator manifests --image ghcr.io/example/rmk8soperator:latest --ca-file /path/to/ca.crt

    # Run the controllers (kubeconfig locally, ServiceAccount in-cluster)
    CLOUDCOIL_NAMESPACE=opendefence-system rmk8soperator run

``CLOUDCOIL_NAMESPACE`` is the operator's Lease/Deployment namespace. User, Group,
Role, and Invite are cluster-scoped; UserBinding is namespaced. Production
containers with no arguments run
``rmk8soperator run``. Admission serves on every replica, independently of
leader election. Generated webhook configurations fail closed, so the HTTPS
listener and ``operator-tls`` Secret must be ready before Group writes.

Images
------

GitHub Actions builds the ``test`` and ``production`` targets from both
Dockerfile_alpine and Dockerfile_debian on pull requests. Publishing uses the
default Dockerfile (Alpine) for linux/amd64 and linux/arm64. Alpine is the
preferred image; commit ``uv.lock`` because Docker builds use
``uv sync --locked``.

Optional container workflows for isolated checks (Docker or Podman; same
Dockerfiles)::

    # Devel shell
    docker build --target devel_shell -t rmk8soperator:devel_shell .
    docker create --name rmk8soperator_devel -v "$(pwd):/app" -it rmk8soperator:devel_shell
    docker start -i rmk8soperator_devel

    # prek inside that container
    docker exec -i rmk8soperator_devel /bin/bash -c "uv run --locked prek run --all-files"

    # Tox target (CI-style)
    docker build --target tox -t rmk8soperator:tox .
    docker run --rm -it -v "$(pwd):/app" rmk8soperator:tox

    # Production image; tag with the project version
    docker build --target production -t rmk8soperator:0.1.1-260913 .
    docker run -it --name rmk8soperator rmk8soperator:0.1.1-260913

Replace ``docker`` with ``podman`` if that is your engine.

Versioning
----------

Versions follow pvarki's Python convention ``MAJOR.MINOR.PATCH+YYMMDD``.
The ``release`` part records the release date and updates automatically when
bumping major, minor, or patch. Container tags use ``-`` instead of ``+``;
the shared publisher normalizes this, and bump-my-version keeps the README's
local image tags in the same format.

::

    uv run --locked bump-my-version show-bump
    uv run --locked bump-my-version bump patch
    uv lock

Use ``minor`` or ``major`` instead of ``patch`` as needed, or ``release`` to
refresh only the date on a later day. The configuration in
``.bumpversion.toml`` updates the package metadata, module version, version
test, and production image tags in this README. Commit these changes together
with ``uv.lock``; version bumping does not automatically create a commit or
Git tag.
