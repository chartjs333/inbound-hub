# Validation — 2026-10-24

Production readiness: **BLOCKED**. These are actual local checks, not deployment approval.

## `python -m pytest -q`

Exit 0

```text
...........................................s                             [100%]
=============================== warnings summary ===============================
../../inbound-hub/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /workspace/scratch/5b9cf5b7a0f5/inbound-hub/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
43 passed, 1 skipped, 1 warning in 1.77s

```

## `python -m ruff check --config pyproject.toml src tests`

Exit 0

```text
All checks passed!

```

## `python -m mypy --cache-dir .mypy-release-final --ignore-missing-imports --check-untyped-defs src`

Exit 0

```text
Success: no issues found in 11 source files

```

## `python -m build --no-isolation`

Exit 0

```text
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing entry points to src/inbound_agent_channel_bridge.egg-info/entry_points.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
running sdist
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing entry points to src/inbound_agent_channel_bridge.egg-info/entry_points.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
running check
creating inbound_agent_channel_bridge-0.1.0
creating inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
creating inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge/static
creating inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
creating inbound_agent_channel_bridge-0.1.0/tests
copying files to inbound_agent_channel_bridge-0.1.0...
copying README.md -> inbound_agent_channel_bridge-0.1.0
copying pyproject.toml -> inbound_agent_channel_bridge-0.1.0
copying src/agent_channel_bridge/__init__.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/__main__.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/adapters.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/api.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/gateway.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/introspection.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/mobile.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/models.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/security.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/simulator.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/transport.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/static/app.js -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge/static
copying src/agent_channel_bridge/static/index.html -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge/static
copying src/agent_channel_bridge/static/manifest.webmanifest -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge/static
copying src/agent_channel_bridge/static/style.css -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge/static
copying src/inbound_agent_channel_bridge.egg-info/PKG-INFO -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/SOURCES.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/dependency_links.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/entry_points.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/requires.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/top_level.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying tests/test_gateway.py -> inbound_agent_channel_bridge-0.1.0/tests
copying tests/test_mobile.py -> inbound_agent_channel_bridge-0.1.0/tests
copying tests/test_mobile_browser.py -> inbound_agent_channel_bridge-0.1.0/tests
Writing inbound_agent_channel_bridge-0.1.0/setup.cfg
Creating tar archive
removing 'inbound_agent_channel_bridge-0.1.0' (and everything under it)
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing entry points to src/inbound_agent_channel_bridge.egg-info/entry_points.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
running bdist_wheel
running build
running build_py
creating build/lib/agent_channel_bridge
copying src/agent_channel_bridge/__main__.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/mobile.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/__init__.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/simulator.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/transport.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/models.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/gateway.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/api.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/adapters.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/introspection.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/security.py -> build/lib/agent_channel_bridge
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing entry points to src/inbound_agent_channel_bridge.egg-info/entry_points.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
creating build/lib/agent_channel_bridge/static
copying src/agent_channel_bridge/static/manifest.webmanifest -> build/lib/agent_channel_bridge/static
copying src/agent_channel_bridge/static/app.js -> build/lib/agent_channel_bridge/static
copying src/agent_channel_bridge/static/index.html -> build/lib/agent_channel_bridge/static
copying src/agent_channel_bridge/static/style.css -> build/lib/agent_channel_bridge/static
installing to build/bdist.linux-x86_64/wheel
running install
running install_lib
creating build/bdist.linux-x86_64/wheel
creating build/bdist.linux-x86_64/wheel/agent_channel_bridge
copying build/lib/agent_channel_bridge/__main__.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/mobile.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/__init__.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/simulator.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/transport.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/models.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/gateway.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/api.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
creating build/bdist.linux-x86_64/wheel/agent_channel_bridge/static
copying build/lib/agent_channel_bridge/static/manifest.webmanifest -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge/static
copying build/lib/agent_channel_bridge/static/app.js -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge/static
copying build/lib/agent_channel_bridge/static/index.html -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge/static
copying build/lib/agent_channel_bridge/static/style.css -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge/static
copying build/lib/agent_channel_bridge/adapters.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/introspection.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/security.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
running install_egg_info
Copying src/inbound_agent_channel_bridge.egg-info to build/bdist.linux-x86_64/wheel/./inbound_agent_channel_bridge-0.1.0-py3.12.egg-info
running install_scripts
creating build/bdist.linux-x86_64/wheel/inbound_agent_channel_bridge-0.1.0.dist-info/WHEEL
creating '/workspace/scratch/5b9cf5b7a0f5/channel-bridge/channel_bridge/dist/.tmp-akgg68t4/inbound_agent_channel_bridge-0.1.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it
adding 'agent_channel_bridge/__init__.py'
adding 'agent_channel_bridge/__main__.py'
adding 'agent_channel_bridge/adapters.py'
adding 'agent_channel_bridge/api.py'
adding 'agent_channel_bridge/gateway.py'
adding 'agent_channel_bridge/introspection.py'
adding 'agent_channel_bridge/mobile.py'
adding 'agent_channel_bridge/models.py'
adding 'agent_channel_bridge/security.py'
adding 'agent_channel_bridge/simulator.py'
adding 'agent_channel_bridge/transport.py'
adding 'agent_channel_bridge/static/app.js'
adding 'agent_channel_bridge/static/index.html'
adding 'agent_channel_bridge/static/manifest.webmanifest'
adding 'agent_channel_bridge/static/style.css'
adding 'inbound_agent_channel_bridge-0.1.0.dist-info/METADATA'
adding 'inbound_agent_channel_bridge-0.1.0.dist-info/WHEEL'
adding 'inbound_agent_channel_bridge-0.1.0.dist-info/entry_points.txt'
adding 'inbound_agent_channel_bridge-0.1.0.dist-info/top_level.txt'
adding 'inbound_agent_channel_bridge-0.1.0.dist-info/RECORD'
removing build/bdist.linux-x86_64/wheel
Successfully built inbound_agent_channel_bridge-0.1.0.tar.gz and inbound_agent_channel_bridge-0.1.0-py3-none-any.whl
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
[json]	INFO	JSON output written to file: SECURITY_SCAN.json

```

## `python -m pip_audit --disable-pip --no-deps -r requirements-runtime.lock --format json --output DEPENDENCY_AUDIT.json`

Exit 0

```text
WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
No known vulnerabilities found

```

## Mandatory browser gate — FAILED / BLOCKED

Attempted `HUB_TEST_CHROMIUM=.../chromium-1161/chrome-linux/chrome TMPDIR=... PYTHONPATH=channel_bridge/src python -m pytest channel_bridge/tests/test_mobile_browser.py -q`. Playwright launched Chromium but it terminated before any page: TargetClosedError. Direct headless Chromium retry with local profile, no-zygote and single-process exited 133 (SIGTRAP). Browser binary reports Chromium 134.0.6998.35. Default suite skips this test when HUB_TEST_CHROMIUM is absent; that skip is NOT a release pass. Browser/visual/platform acceptance remains open.

## Dependency remediation

Initial pip-audit found 37 advisories for Pillow 12.3.0, with fixes reported in 13.0.0. Dependency bounds and runtime lock were updated to Pillow 13.0.0; image/audio validation tests and audit rerun. Runtime lock pins complete installed dependency closure; it does not include wheel hashes.
