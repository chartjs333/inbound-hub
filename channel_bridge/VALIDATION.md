# Validation evidence

Executed 2026-10-24 with Python 3.12.14.

## `python -m pytest -q`

Exit: 0

```text
........................                                                 [100%]
=============================== warnings summary ===============================
../../inbound-hub/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /workspace/scratch/5b9cf5b7a0f5/inbound-hub/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
24 passed, 1 warning in 0.83s

```

## `python -m ruff check --config pyproject.toml src tests`

Exit: 0

```text
All checks passed!

```

## `python -m mypy --ignore-missing-imports --check-untyped-defs src`

Exit: 0

```text
Success: no issues found in 6 source files

```

## `python -m build --no-isolation`

Exit: 0

```text
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
running sdist
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
running check
creating inbound_agent_channel_bridge-0.1.0
creating inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
creating inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
creating inbound_agent_channel_bridge-0.1.0/tests
copying files to inbound_agent_channel_bridge-0.1.0...
copying README.md -> inbound_agent_channel_bridge-0.1.0
copying pyproject.toml -> inbound_agent_channel_bridge-0.1.0
copying src/agent_channel_bridge/__init__.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/api.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/gateway.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/models.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/simulator.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/agent_channel_bridge/transport.py -> inbound_agent_channel_bridge-0.1.0/src/agent_channel_bridge
copying src/inbound_agent_channel_bridge.egg-info/PKG-INFO -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/SOURCES.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/dependency_links.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/requires.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying src/inbound_agent_channel_bridge.egg-info/top_level.txt -> inbound_agent_channel_bridge-0.1.0/src/inbound_agent_channel_bridge.egg-info
copying tests/test_gateway.py -> inbound_agent_channel_bridge-0.1.0/tests
Writing inbound_agent_channel_bridge-0.1.0/setup.cfg
Creating tar archive
removing 'inbound_agent_channel_bridge-0.1.0' (and everything under it)
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
running bdist_wheel
running build
running build_py
creating build/lib/agent_channel_bridge
copying src/agent_channel_bridge/__init__.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/simulator.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/transport.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/models.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/gateway.py -> build/lib/agent_channel_bridge
copying src/agent_channel_bridge/api.py -> build/lib/agent_channel_bridge
running egg_info
writing src/inbound_agent_channel_bridge.egg-info/PKG-INFO
writing dependency_links to src/inbound_agent_channel_bridge.egg-info/dependency_links.txt
writing requirements to src/inbound_agent_channel_bridge.egg-info/requires.txt
writing top-level names to src/inbound_agent_channel_bridge.egg-info/top_level.txt
reading manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_agent_channel_bridge.egg-info/SOURCES.txt'
installing to build/bdist.linux-x86_64/wheel
running install
running install_lib
creating build/bdist.linux-x86_64/wheel
creating build/bdist.linux-x86_64/wheel/agent_channel_bridge
copying build/lib/agent_channel_bridge/__init__.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/simulator.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/transport.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/models.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/gateway.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
copying build/lib/agent_channel_bridge/api.py -> build/bdist.linux-x86_64/wheel/./agent_channel_bridge
running install_egg_info
Copying src/inbound_agent_channel_bridge.egg-info to build/bdist.linux-x86_64/wheel/./inbound_agent_channel_bridge-0.1.0-py3.12.egg-info
running install_scripts
creating build/bdist.linux-x86_64/wheel/inbound_agent_channel_bridge-0.1.0.dist-info/WHEEL
creating '/workspace/scratch/5b9cf5b7a0f5/channel-bridge/channel_bridge/dist/.tmp-exxdzdbw/inbound_agent_channel_bridge-0.1.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it
adding 'agent_channel_bridge/__init__.py'
adding 'agent_channel_bridge/api.py'
adding 'agent_channel_bridge/gateway.py'
adding 'agent_channel_bridge/models.py'
adding 'agent_channel_bridge/simulator.py'
adding 'agent_channel_bridge/transport.py'
adding 'inbound_agent_channel_bridge-0.1.0.dist-info/METADATA'
adding 'inbound_agent_channel_bridge-0.1.0.dist-info/WHEEL'
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
