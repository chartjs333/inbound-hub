# Validation evidence

Executed 2026-10-24 with Python 3.12.14.

## `python -m pytest -q`

Exit: 0

```text
...............                                                          [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /workspace/scratch/5b9cf5b7a0f5/inbound-hub/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
15 passed, 1 warning in 2.15s

```

## `python -m ruff check --config pyproject.toml src tests`

Exit: 0

```text
All checks passed!

```

## `python -m mypy --ignore-missing-imports --check-untyped-defs src`

Exit: 0

```text
Success: no issues found in 10 source files

```

## `python -m build --no-isolation`

Exit: 0

```text
running egg_info
writing src/inbound_hub.egg-info/PKG-INFO
writing dependency_links to src/inbound_hub.egg-info/dependency_links.txt
writing requirements to src/inbound_hub.egg-info/requires.txt
writing top-level names to src/inbound_hub.egg-info/top_level.txt
reading manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
running sdist
running egg_info
writing src/inbound_hub.egg-info/PKG-INFO
writing dependency_links to src/inbound_hub.egg-info/dependency_links.txt
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
copying src/inbound_hub/app.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/coordinator.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub/events.py -> inbound_hub-0.1.0/src/inbound_hub
copying src/inbound_hub.egg-info/PKG-INFO -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub.egg-info/SOURCES.txt -> inbound_hub-0.1.0/src/inbound_hub.egg-info
copying src/inbound_hub.egg-info/dependency_links.txt -> inbound_hub-0.1.0/src/inbound_hub.egg-info
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
Writing inbound_hub-0.1.0/setup.cfg
Creating tar archive
removing 'inbound_hub-0.1.0' (and everything under it)
running egg_info
writing src/inbound_hub.egg-info/PKG-INFO
writing dependency_links to src/inbound_hub.egg-info/dependency_links.txt
writing requirements to src/inbound_hub.egg-info/requires.txt
writing top-level names to src/inbound_hub.egg-info/top_level.txt
reading manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
running bdist_wheel
running build
running build_py
creating build/lib/inbound_hub
copying src/inbound_hub/__init__.py -> build/lib/inbound_hub
copying src/inbound_hub/events.py -> build/lib/inbound_hub
copying src/inbound_hub/app.py -> build/lib/inbound_hub
copying src/inbound_hub/coordinator.py -> build/lib/inbound_hub
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
writing requirements to src/inbound_hub.egg-info/requires.txt
writing top-level names to src/inbound_hub.egg-info/top_level.txt
reading manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
writing manifest file 'src/inbound_hub.egg-info/SOURCES.txt'
installing to build/bdist.linux-x86_64/wheel
running install
running install_lib
creating build/bdist.linux-x86_64/wheel
creating build/bdist.linux-x86_64/wheel/inbound_hub
copying build/lib/inbound_hub/__init__.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/events.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
creating build/bdist.linux-x86_64/wheel/inbound_hub/adapters
copying build/lib/inbound_hub/adapters/base.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/adapters
copying build/lib/inbound_hub/app.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
copying build/lib/inbound_hub/coordinator.py -> build/bdist.linux-x86_64/wheel/./inbound_hub
creating build/bdist.linux-x86_64/wheel/inbound_hub/domains
copying build/lib/inbound_hub/domains/musician.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
copying build/lib/inbound_hub/domains/__init__.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
copying build/lib/inbound_hub/domains/registry.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
copying build/lib/inbound_hub/domains/contracts.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/domains
creating build/bdist.linux-x86_64/wheel/inbound_hub/integrations
copying build/lib/inbound_hub/integrations/nginx_qa.py -> build/bdist.linux-x86_64/wheel/./inbound_hub/integrations
running install_egg_info
Copying src/inbound_hub.egg-info to build/bdist.linux-x86_64/wheel/./inbound_hub-0.1.0-py3.12.egg-info
running install_scripts
creating build/bdist.linux-x86_64/wheel/inbound_hub-0.1.0.dist-info/WHEEL
creating '/workspace/scratch/5b9cf5b7a0f5/inbound-hub/dist/.tmp-d8wfgmtj/inbound_hub-0.1.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it
adding 'inbound_hub/__init__.py'
adding 'inbound_hub/app.py'
adding 'inbound_hub/coordinator.py'
adding 'inbound_hub/events.py'
adding 'inbound_hub/adapters/base.py'
adding 'inbound_hub/domains/__init__.py'
adding 'inbound_hub/domains/contracts.py'
adding 'inbound_hub/domains/musician.py'
adding 'inbound_hub/domains/registry.py'
adding 'inbound_hub/integrations/nginx_qa.py'
adding 'inbound_hub-0.1.0.dist-info/METADATA'
adding 'inbound_hub-0.1.0.dist-info/WHEEL'
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
