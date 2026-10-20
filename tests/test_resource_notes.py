#!/usr/bin/env python3
"""Check portable resource skills/templates and the read-only note checker."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import common

registry = common.tomllib.loads((ROOT / 'extensions/registry.toml').read_text())
for name in ('create-resource', 'create-project-note', 'maintain-resources'):
    text = (ROOT / 'skills' / name / 'SKILL.md').read_text()
    assert re.search(r'^name: ' + name + r'$', text, re.M), name
    assert re.search(r'^description: .+', text, re.M), name
    assert '## Check' in text, name
    assert registry[name]['status'] == 'active', name
resource = (ROOT / 'templates/resource.md').read_text()
for key in ('summary', 'kind', 'status', 'verified', 'sources'):
    assert re.search(r'^' + key + ':', resource, re.M), key
project = (ROOT / 'templates/project.md').read_text()
assert re.search(r'^type: project$', project, re.M)
assert '../../resources/' in project
assert len([line for line in project.split('---', 2)[2].splitlines() if line.strip()]) <= 10
result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s',
                         str(ROOT / 'skills/maintain-resources/scripts'), '-p', 'test_*.py'])
if result.returncode:
    raise SystemExit(result.returncode)
print('PASS resource skills, templates, registry and read-only checker fixtures')
