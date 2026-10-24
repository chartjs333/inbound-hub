"""Mandatory release checks: absent integration source is a failure, not a successful skip."""
import os
import subprocess
import sys

if not os.environ.get('NGINX_QA_SOURCE'):
    raise SystemExit('BLOCKED: NGINX_QA_SOURCE must point to an unchanged nginx-qa checkout')
commands=[['pytest','-q'],['ruff','check','--config','pyproject.toml','src','tests'],
          ['mypy','--ignore-missing-imports','--check-untyped-defs','src'],
          ['build','--no-isolation'],['bandit','-r','src'],
          ['pip_audit','--disable-pip','--no-deps','-r','requirements-runtime.lock']]
for command in commands:
    subprocess.run([sys.executable,'-m',*command],check=True)
