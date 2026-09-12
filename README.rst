=======================
rasenmaeher-k8soperator
=======================

K8s Operator and CRDs with core RASENMAEHER entities


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
for SSH forwarding and host gateway configuration.

Creating a development container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build image, create container and start it::

    # Docker
    docker build --add-host=host.docker.internal:host-gateway --ssh default --target devel_shell -t rmk8soperator:devel_shell .
    docker create --add-host=host.docker.internal:host-gateway --name rmk8soperator_devel -v "$(pwd):/app" -it $(echo $DOCKER_SSHAGENT) rmk8soperator:devel_shell
    docker start -i rmk8soperator_devel

    # Podman alternative
    podman build --add-host=host.docker.internal:host-gateway --ssh default --target devel_shell -t rmk8soperator:devel_shell .
    podman create --add-host=host.docker.internal:host-gateway --name rmk8soperator_devel -v "$(pwd):/app" -it $(echo $PODMAN_SSHAGENT) rmk8soperator:devel_shell
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
    docker run --add-host=host.docker.internal:host-gateway --rm -it -v "$(pwd):/app" rmk8soperator:devel_shell -c "uv run --locked prek run --all-files"

    # Podman alternative
    podman run --add-host=host.docker.internal:host-gateway --rm -it -v "$(pwd):/app" rmk8soperator:devel_shell -c "uv run --locked prek run --all-files"

Test suite
^^^^^^^^^^

You can use the devel shell to run py.test when doing development, for CI use
the "tox" target in the Dockerfile::

    # Docker
    docker build --add-host=host.docker.internal:host-gateway --ssh default --target tox -t rmk8soperator:tox .
    docker run --add-host=host.docker.internal:host-gateway --rm -it -v "$(pwd):/app" $(echo $DOCKER_SSHAGENT) rmk8soperator:tox

    # Podman alternative
    podman build --add-host=host.docker.internal:host-gateway --ssh default --target tox -t rmk8soperator:tox .
    podman run --add-host=host.docker.internal:host-gateway --rm -it -v "$(pwd):/app" $(echo $PODMAN_SSHAGENT) rmk8soperator:tox

Production docker
^^^^^^^^^^^^^^^^^

GitHub Actions builds the test and production targets from both Dockerfile_alpine
and Dockerfile_debian for pull requests. Publishing uses the default Dockerfile
(Alpine) for both linux/amd64 and linux/arm64. See the CI configuration below.

There's a "production" target as well for running the application. Tag the image
with the project version::

    # Docker
    docker build --add-host=host.docker.internal:host-gateway --ssh default --target production -t rmk8soperator:0.1.0-260912 .
    docker run --add-host=host.docker.internal:host-gateway -it --name rmk8soperator rmk8soperator:0.1.0-260912

    # Podman alternative
    podman build --add-host=host.docker.internal:host-gateway --ssh default --target production -t rmk8soperator:0.1.0-260912 .
    podman run --add-host=host.docker.internal:host-gateway -it --name rmk8soperator rmk8soperator:0.1.0-260912

Alpine considerations
^^^^^^^^^^^^^^^^^^^^^

Alpine images are much more lightweight than Debian/Ubuntu ones so they are preferred where possible.
There are a few potential issues however:

  - Compiled extensions not available as wheels. This is mostly mitigated by our own wheel builder.
  - Compiled extensions not compiling under Alpine. Alpine does not have certain nonstandard extensions to libc
    enabled by default, poorly written extensions will fail to compile because they depend on these extensions
    and do not explicitly request them to be enabled.
  - Commit uv.lock; Docker builds use uv sync --locked to detect stale dependency metadata.


Continuous integration
----------------------

The workflows in .github/workflows use shared actions from
`pvarki/config-ci-library <https://github.com/pvarki/config-ci-library>`_, following
`python-mediamtx-rmmtxauthz <https://github.com/pvarki/python-mediamtx-rmmtxauthz/tree/main/.github/workflows>`_.

Pull requests validate the version bump and project metadata, run prek, test
Python 3.12, 3.13 and 3.14, build Python distributions, and build both container
variants. JUnit results are saved as artifacts. Snyk checks dependencies using
the ``deployapp-products`` organization. The version must differ from the PR's
base branch; use the version bump commands below and commit uv.lock with it.

After the version, setup, prek, test and Docker checks pass, same-repository PRs
publish preview images. Pushes to main publish release images and run Snyk
monitoring. As in the example, Snyk runs independently of publishing. Fork PRs
run checks without publishing, Snyk credentials or writing JUnit check reports.
Manual runs of the PR workflow run checks without requiring a version bump or
publishing; manual publishing through the main workflow is limited to main.

The image name is ``pvarki/rasenmaeher-worker`` (product ``rasenmaeher``, component
``worker``). The shared publisher derives version and PR tags from
.bumpversion.toml and publishes to GHCR, Docker Hub and ACR. Configure these
repository or organization settings before running the workflows:

- Variables: ``DOCKERHUB_USERNAME``, ``ACR_REPO`` (registry hostname), ``ACR_USERNAME``.
- Secrets: ``DOCKERHUB_TOKEN``, ``ACR_TOKEN``, ``SNYK_TOKEN``.
- GitHub supplies ``GITHUB_TOKEN``; publishing jobs request ``packages: write``.

All referenced registry credentials must be populated. To disable Docker Hub
or ACR, remove all inputs for that registry from both publishing jobs; passing
empty values makes the shared action fail. Shared pvarki actions track ``main``
to receive common CI updates.


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
