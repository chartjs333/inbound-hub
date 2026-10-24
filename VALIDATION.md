# Validation — 2026-10-24

Production readiness: **BLOCKED**. These are actual local checks, not deployment approval.

## `python -m pytest -q`

Exit 0

```text
...............................                                          [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /workspace/scratch/5b9cf5b7a0f5/inbound-hub/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
31 passed, 1 warning in 4.07s

```

## `python -m ruff check --config pyproject.toml src tests`

Exit 0

```text
All checks passed!

```

## `python -m mypy --cache-dir .mypy-release-final --ignore-missing-imports --check-untyped-defs src`

Exit 0

```text
Success: no issues found in 16 source files

```

## `python -m build --no-isolation`

Exit 0

```text
running egg_info
writing src/inbound_hub.egg-info/PKG-INFO
writing dependency_links to src/inbound_hub.egg-info/dependency_links.txt
writing entry points to src/inbound_hub.egg-info/entry_points.txt
writing requirements to src/inbound_hub.egg-info/requires.txt
writing top-level names to src/inbound_hub.egg-info/top_level.txt
reading manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
running sdist
running egg_info
writing src/inbound_hub.egg-info/PKG-INFO
writing dependency_links to src/inbound_hub.egg-info/dependency_links.txt
writing entry points to src/inbound_hub.egg-info/entry_points.txt
writing requirements to src/inbound_hub.egg-info/requires.txt
writing top-level names to src/inbound_hub.egg-info/top_level.txt
reading manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
running check
creating inbound_hub-0.1.0
creating inbound_hub-0.1.0/src/inbound_hub
creating inbound_hub-0.1.0/src/inbound_hub.egg-info
creating inbound_hub-0.1.0/src/inbound_hub/adapters
creating inbound_hub-0.1.0/src/inbound_hub/domains
creating inbound_hub-0.1.0/src/inbound_hub/integrations
creating inbound_hub-0.1.0/tests
copying files to inbound_hub-0.1.0...
copying README.md -> inbound_hub-0.1.0
copying pyproject.toml -> inbound_hub-0.1.0
copying src/inbound_hub/__init__.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/__main__.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/app.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/coordinator.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/events.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/pipeline.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/service.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/sources.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/tray.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/windows_service.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub.egg-info/PKG-INFO -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub.egg-info/SOURCES.txt -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub.egg-info/dependency_links.txt -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub.egg-info/entry_points.txt -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub.egg-info/requires.txt -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub.egg-info/top_level.txt -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub/adapters/base.py -> inbound_hub-0.1.0/src/inbound_hub/adapters
copying src/inbound_hub/domains/__init__.py -> inbound_hub-0.1.0/src/inbound_hub/domains
copying src/inbound_hub/domains/contracts.py -> inbound_hub-0.1.0/src/inbound_hub/domains
copying src/inbound_hub/domains/musician.py -> inbound_hub-0.1.0/src/inbound_hub/domains
copying src/inbound_hub/domains/registry.py -> inbound_hub-0.1.0/src/inbound_hub/domains
copying src/inbound_hub/integrations/nginx_qa.py -> inbound_hub-0.1.0/src/inbound_hub/integrations
copying tests/test_health.py -> inbound_hub-0.1.0/tests
copying tests/test_musician.py -> inbound_hub-0.1.0/tests
copying tests/test_nginx_actual.py -> inbound_hub-0.1.0/tests
copying tests/test_pipeline.py -> inbound_hub-0.1.0/tests
Writing inbound_hub-0.1.0/setup.cfg
Creating tar archive
removing 'inbound_hub-0.1.0' (and everything under it)
running egg_info
writing src/inbound_hub.egg-info/PKG-INFO
writing dependency_links to src/inbound_hub.egg-info/dependency_links.txt
writing entry points to src/inbound_hub.egg-info/entry_points.txt
writing requirements to src/inbound_hub.egg-info/requires.txt
writing top-level names to src/inbound_hub.egg-info/top_level.txt
reading manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
running bdist_wheel
running build
running build_py
creating build/lib/inbound_hub
copying src/inbound_hub/__main__.py -> build/lib/inbound_hub
copying src/inbound_hub/sources.py -> build/lib/inbound_hub
copying src/inbound_hub/__init__.py -> build/lib/inbound_hub
copying src/inbound_hub/events.py -> build/lib/inbound_hub
copying src/inbound_hub/pipeline.py -> build/lib/inbound_hub
copying src/inbound_hub/app.py -> build/lib/inbound_hub
copying src/inbound_hub/tray.py -> build/lib/inbound_hub
copying src/inbound_hub/windows_service.py -> build/lib/inbound_hub
copying src/inbound_hub/coordinator.py -> build/lib/inbound_hub
copying src/inbound_hub/service.py -> build/lib/inbound_hub
creating build/lib/inbound_hub/adapters
copying src/inbound_hub/adapters/base.py -> build/lib/inbound_hub/adapters
creating build/lib/inbound_hub/domains
copying src/inbound_hub/domains/musician.py -> build/lib/inbound_hub/domains
copying src/inbound_hub/domains/__init__.py -> build/lib/inbound_hub/domains
copying src/inbound_hub/domains/registry.py -> build/lib/inbound_hub/domains
copying src/inbound_hub/domains/contracts.py -> build/lib/inbound_hub/domains
creating build/lib/inbound_hub/integrations
copying src/inbound_hub/integrations/nginx_qa.py -> build/lib/inbound_hub/integrations
running egg_info
writing src/inbound_hub.egg-info/PKG-INFO
writing dependency_links to src/inbound_hub.egg-info/dependency_links.txt
writing entry points to src/inbound_hub.egg-info/entry_points.txt
writing requirements to src/inbound_hub.egg-info/requires.txt
writing top-level names to src/inbound_hub.egg-info/top_level.txt
reading manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
installing to build/bdist.linux-x86_64/wheel
running install
running install_lib
creating build/bdist.linux-x86_64/wheel
creating build/bdist.linux-x86_64/wheel/inbound_hub
copying build/lib/inbound_hub/__main__.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/sources.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/__init__.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/events.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/pipeline.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
creating build/bdist.linux-x86_64/wheel/inbound_hub/adapters
copying build/lib/inbound_hub/adapters/base.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/adapters
copying build/lib/inbound_hub/app.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/tray.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/windows_service.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/coordinator.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
creating build/bdist.linux-x86_64/wheel/inbound_hub/domains
copying build/lib/inbound_hub/domains/musician.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
copying build/lib/inbound_hub/domains/__init__.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
copying build/lib/inbound_hub/domains/registry.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
copying build/lib/inbound_hub/domains/contracts.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
creating build/bdist.linux-x86_64/wheel/inbound_hub/integrations
copying build/lib/inbound_hub/integrations/nginx_qa.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/integrations
copying build/lib/inbound_hub/service.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
running install_egg_info
Copying src/inbound_hub.egg-info to build/bdist.linux-x86_64/wheel/./inbound_hub-0.1.0-py3.12.egg-info
running install_scripts
creating build/bdist.linux-x86_64/wheel/inbound_hub-0.1.0.dist-info/WHEEL
creating '/workspace/scratch/5b9cf5b7a0f5/inbound-hub/dist/.tmp-gjrkov7k/inbound_hub-0.1.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it
adding 'inbound_hub/__init__.py'
adding 'inbound_hub/__main__.py'
adding 'inbound_hub/app.py'
adding 'inbound_hub/coordinator.py'
adding 'inbound_hub/events.py'
adding 'inbound_hub/pipeline.py'
adding 'inbound_hub/service.py'
adding 'inbound_hub/sources.py'
adding 'inbound_hub/tray.py'
adding 'inbound_hub/windows_service.py'
adding 'inbound_hub/adapters/base.py'
adding 'inbound_hub/domains/__init__.py'
adding 'inbound_hub/domains/contracts.py'
adding 'inbound_hub/domains/musician.py'
adding 'inbound_hub/domains/registry.py'
adding 'inbound_hub/integrations/nginx_qa.py'
adding 'inbound_hub-0.1.0.dist-info/METADATA'
adding 'inbound_hub-0.1.0.dist-info/WHEEL'
adding 'inbound_hub-0.1.0.dist-info/entry_points.txt'
adding 'inbound_hub-0.1.0.dist-info/top_level.txt'
adding 'inbound_hub-0.1.0.dist-info/RECORD'
removing build/bdist.linux-x86_64/wheel
Successfully built inbound_hub-0.1.0.tar.gz and inbound_hub-0.1.0-py3-none-any.whl
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Getting build dependencies for wheel...
* Building wheel...

```

## `python -m bandit -r src -f json -o SECURITY_SCAN.json`

Exit 0

```text
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[manager]	WARNING	Test in comment: fixed is not a test name or id, ignoring
[manager]	WARNING	Test in comment: git is not a test name or id, ignoring
[manager]	WARNING	Test in comment: argv is not a test name or id, ignoring
[manager]	WARNING	Test in comment: never is not a test name or id, ignoring
[manager]	WARNING	Test in comment: a is not a test name or id, ignoring
[manager]	WARNING	Test in comment: shell is not a test name or id, ignoring
[manager]	WARNING	Test in comment: fixed is not a test name or id, ignoring
[manager]	WARNING	Test in comment: executable is not a test name or id, ignoring
[manager]	WARNING	Test in comment: argv is not a test name or id, ignoring
[manager]	WARNING	Test in comment: validated is not a test name or id, ignoring
[manager]	WARNING	Test in comment: ref is not a test name or id, ignoring
[manager]	WARNING	Test in comment: no is not a test name or id, ignoring
[manager]	WARNING	Test in comment: shell is not a test name or id, ignoring
[json]	INFO	JSON output written to file: SECURITY_SCAN.json

```

## `python -m pip_audit --disable-pip --no-deps -r requirements-runtime.lock --format json --output DEPENDENCY_AUDIT.json`

Exit 0

```text
WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
No known vulnerabilities found

```

## Actual nginx-qa integration

NGINX_QA_SOURCE points to unchanged commit `627b478e29f5f7254d279363790f46e92c114d8d`. Tests use real ASGI application, JSON schemas, Bearer validation and temporary persistence. Includes Email → booking → six specialist actors → pending submission/deduplication/status; no Play/Start. No staging server was contacted.

## Static security review

Initial Bandit findings B404/B603/B607 in the committed-profile Git reader were reviewed. Git resolves to an absolute executable; leading-option refs are rejected; fixed argv and no shell are used. B404/B603 carry explicit reviewed suppressions. This is not independent penetration testing.

# Architecture independence audit — 2026-10-24

Supersedes the historical source-based integration procedure above. PR #1 audited at
 d518e2f1411da188699da47565f2f564da1fd95b; PR #2 at
 d31f6bd54f70a7e7e2e4295b43424b81dc272155.

Finding: tests/test_nginx_actual.py required NGINX_QA_SOURCE, inserted a foreign checkout
into sys.path, imported its internal main, changed working directory and monkeypatched server
file/state globals. Temporary state was isolated, but test/release independence was violated.
The release script also required that checkout. Replaced the test with consumer HTTP contract
checks and removed the checkout prerequisite. Added an executable-source architecture guard.
No production implementation changes; Bridge requires no independence fix.

Manual inspection of both src trees and their configuration, storage and HTTP clients found no
foreign file reads/writes, shared database/state, foreign working-directory requirements or
nginx-qa internal imports. Hub owns its SQLite state; Bridge owns its SQLite/artifact state.
Operator-configured artist-profile Git repositories are domain input, not nginx-qa internals.
Historical local paths in prior validation logs are evidence, not runtime configuration.

Pending API: POST /api/v1/projects/{id}/pending-sprints and GET /{pending_id}/status,
version 1 proposal envelope, scoped Bearer header and correlation ID. HTTPS required except
explicit loopback HTTP. Redirects are not followed. Response envelopes are JSON dictionaries;
full provider-side schema conformance is not established by mocked consumer tests.
Bridge: typed request schema, HMAC SHA-256 over timestamp + '.' + exact body, constant-time
signature comparison, 60-second freshness and scoped assignment checks. Configured HTTPS
callbacks and fail-closed Bearer introspection only; no filesystem fallback. README documents
these contracts, but nginx-qa callback/introspection support is absent/unqualified. This audit
confirms code independence, not live interoperability or production readiness.

Commands from workspace root (no full regression, builds or live service calls):

- `PYTHONPATH=independence-audit/src inbound-hub/.venv/bin/python -m pytest independence-audit/tests/test_nginx_actual.py independence-audit/tests/test_architecture.py -q`
  Result: 7 passed in 0.23s.
- `PYTHONPATH=channel-bridge/channel_bridge/src inbound-hub/.venv/bin/python -m pytest channel-bridge/channel_bridge/tests/test_gateway.py -q -k 'http_intake or transport_replay or https_callbacks or assignment_introspection or unauthorized_intake'`
  Result: 9 passed, 22 deselected in 0.12s; existing Starlette/httpx deprecation warning.
- `inbound-hub/.venv/bin/python -m ruff check --config independence-audit/pyproject.toml independence-audit/tests/test_nginx_actual.py independence-audit/tests/test_architecture.py --fix`
  Result: one import-format issue fixed, zero remaining.
- `rg -n 'nginx|sys.path|chdir|importlib' inbound-hub/src channel-bridge/channel_bridge/src`
  Result: only Hub-owned integration imports, endpoint configuration and descriptive text;
  no foreign imports/path mutation. Source-based test dependency found separately and removed.
- `git -C channel-bridge diff --exit-code`: exit 0.
- `git -C nginx-qa-reference status --porcelain`: empty; no changes.

New branch targets work/musician-booking-completion for a minimal stacked review. Existing PRs,
main, source branches, services and production data are unchanged. No merge or deployment.
