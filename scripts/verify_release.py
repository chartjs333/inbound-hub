"""Local release checks independent of any external repository checkout."""
import subprocess
import sys

commands=[['pytest','-q'],['ruff','check','--config','pyproject.toml','src','tests'],
          ['mypy','--ignore-missing-imports','--check-untyped-defs','src'],
          ['build','--no-isolation'],['bandit','-r','src'],
          ['pip_audit','--disable-pip','--no-deps','-r','requirements-runtime.lock']]
for command in commands:
    subprocess.run([sys.executable,'-m',*command],check=True)
