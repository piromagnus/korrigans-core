import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('check_notes', Path(__file__).with_name('check_notes.py'))
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


class NotesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.put('korrigans.toml', '[korrigans]\n')
        self.put('resources/README.md', '---\nsummary: "Index"\n---\n# Index\n[Data](datasets/sample.md)\n')
        self.resource = ('---\nsummary: "Sample"\nkind: dataset\nstatus: uncertain\n'
                         'verified: "2026-01-01"\nsources:\n  - "/unavailable/data"\n---\n'
                         '# Sample\n- Path: `/unavailable/data`.\n')
        self.put('resources/datasets/sample.md', self.resource)
        self.project = '---\nsummary: "Goal"\n---\n# Project\n- Resources: [sample](../../resources/datasets/sample.md).\n'
        self.put('projects/test/project.md', self.project)

    def put(self, relative, content):
        p = self.root / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def test_valid_and_unavailable_data_do_not_fail(self):
        result = notes.check(self.root)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['counts'], {'resources': 1, 'projects': 1})

    def test_broken_note_link_fails(self):
        self.put('projects/test/project.md', self.project + '[missing](missing.md)\n')
        self.assertTrue(any('broken link' in x for x in notes.check(self.root)['errors']))

    def test_oversized_project_fails(self):
        self.put('projects/test/project.md', self.project + '- extra\n' * 21)
        self.assertTrue(any('body lines' in x for x in notes.check(self.root)['errors']))

    def test_invalid_kind_and_date_fail(self):
        self.put('resources/datasets/sample.md', self.resource.replace('kind: dataset', 'kind: repo').replace('2026-01-01', 'not-a-date'))
        result = notes.check(self.root)
        self.assertTrue(any('kind' in x for x in result['errors']))
        self.assertTrue(any('verification date' in x for x in result['errors']))

    def test_future_date_fails(self):
        self.put('resources/datasets/sample.md', self.resource.replace('2026-01-01', '2999-01-01'))
        self.assertTrue(any('future' in x for x in notes.check(self.root)['errors']))

    def test_history_is_not_an_active_project(self):
        self.put('projects/test/_archive/project.md', 'historic untyped text')
        self.assertEqual(notes.check(self.root)['errors'], [])

    def test_read_only_and_repeatable(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(notes.check(self.root), notes.check(self.root))
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})


if __name__ == '__main__':
    unittest.main()
