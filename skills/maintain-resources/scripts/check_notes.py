#!/usr/bin/env python3
"""Read-only structural checks for compact resource and project notes (stdlib only).

Usage: python3 check_notes.py /path/to/workspace [--json]
Does not scan actual datasets, follow data links, update dates or change files.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

REQUIRED = ('summary', 'kind', 'status', 'verified', 'sources')
KINDS = {'datasets': 'dataset', 'repos': 'repo', 'tools': 'tool'}


def split_note(text):
    match = re.match(r'\A---\n(.*?)\n---\n(.*)\Z', text, re.S)
    if not match:
        raise ValueError('Missing frontmatter')
    header, body = match.groups()
    fields = {}
    for line in header.splitlines():
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if m:
            fields[m[1]] = m[2].strip().strip('"').strip("'")
    return fields, body


def local_links(text):
    # Compact notes use simple inline links; typed/wiki links belong to korrigans check.
    for raw in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', text):
        target = raw.strip().split(' "', 1)[0].strip('<>')
        url = urlsplit(target)
        if url.scheme or target.startswith('//') or not url.path:
            continue
        yield unquote(url.path)


def check(workspace):
    root = workspace.resolve()
    errors, warnings, measurements = [], [], []
    paths = [root / 'resources/README.md']
    for folder in KINDS:
        paths.extend(sorted((root / 'resources' / folder).glob('*.md')))
    paths.extend(sorted((root / 'projects').glob('*/project.md')))
    for path in paths:
        rel = str(path.relative_to(root))
        if path.is_symlink():
            errors.append(f'{rel}: note must not be a symlink')
            continue
        try:
            text = path.read_text(encoding='utf-8')
            fields, body = split_note(text)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f'{rel}: {exc}')
            continue
        is_resource = path.parent.name in KINDS and path.parent.parent == root / 'resources'
        is_project = path.name == 'project.md'
        body_lines = len([line for line in body.splitlines() if line.strip()])
        measurements.append({'path': rel, 'chars': len(text), 'body_lines': body_lines})
        if not fields.get('summary'):
            errors.append(f'{rel}: missing summary')
        if is_resource:
            for key in REQUIRED:
                # sources may use a YAML block list, so an empty first line is allowed.
                if key not in fields or key != 'sources' and not fields[key]:
                    errors.append(f'{rel}: missing {key}')
            if fields.get('kind') != KINDS[path.parent.name]:
                errors.append(f'{rel}: kind does not match folder')
            if fields.get('status') not in {'confirmed', 'uncertain', 'proposed'}:
                errors.append(f'{rel}: invalid observation status')
            try:
                verified = date.fromisoformat(fields.get('verified', ''))
                if verified > date.today():
                    errors.append(f'{rel}: verification date is in the future')
            except ValueError:
                errors.append(f'{rel}: invalid verification date')
            if len(body) > 2000:
                warnings.append(f'{rel}: resource body exceeds 2000 characters')
        if (is_resource or is_project) and body_lines > 20:
            errors.append(f'{rel}: {body_lines} body lines (max 20)')
        if is_project and body_lines > 10:
            warnings.append(f'{rel}: project exceeds target of 10 body lines')
        for target in local_links(text):
            linked = Path(target) if target.startswith('/') else path.parent / target
            if not linked.exists():
                errors.append(f'{rel}: broken link {target}')
    counts = {'resources': sum(1 for m in measurements if m['path'].startswith(tuple('resources/' + k + '/' for k in KINDS))),
              'projects': sum(m['path'].endswith('/project.md') for m in measurements)}
    return {'counts': counts, 'errors': errors, 'warnings': warnings, 'measurements': measurements}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if not (args.workspace / 'korrigans.toml').is_file():
        parser.error('Expected a workspace containing korrigans.toml')
    result = check(args.workspace)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"{result['counts']['resources']} resources; {result['counts']['projects']} projects; "
              f"{len(result['errors'])} errors; {len(result['warnings'])} warnings")
        for level in ('errors', 'warnings'):
            for item in result[level]:
                print(f'{level}: {item}')
    raise SystemExit(bool(result['errors']))


if __name__ == '__main__':
    main()
