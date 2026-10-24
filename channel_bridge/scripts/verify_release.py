"""Browser qualification is mandatory; a skipped browser test is not a release pass."""
import os
import subprocess
import sys

if not os.environ.get('HUB_TEST_CHROMIUM'):
    raise SystemExit('BLOCKED: HUB_TEST_CHROMIUM must identify an executable Chromium for UI tests')
for command in [['pytest','-q'],['ruff','check','--config','pyproject.toml','src','tests'],
                ['mypy','--ignore-missing-imports','--check-untyped-defs','src'],
                ['build','--no-isolation'],['bandit','-r','src'],
                ['pip_audit','--disable-pip','--no-deps','-r','requirements-runtime.lock']]:
    subprocess.run([sys.executable,'-m',*command],check=True)
