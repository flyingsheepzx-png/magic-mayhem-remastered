"""Save preservation on failed and completed comparison sessions; no game launch."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compare_hd_baseline import CaptureSession
from wide169_trial import Session


class CaptureSaveSafetyTest(unittest.TestCase):
    def test_unknown_label_cannot_select_installed_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'baseline or hd'):
                CaptureSession('hd-retry', Path(folder))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def make_session(self, root, ready=False):
        s = CaptureSession.__new__(CaptureSession)
        s.lab = root / 'runtime'
        (s.lab / 'Save').mkdir(parents=True)
        s.run = root / 'report'
        s.run.mkdir()
        s.proc = s.handle = None
        s.original = {}
        s.mutable = {}
        s.before_saves = set()
        s.snapshot_ready = ready
        s.records = {}
        s.result = {}
        return s

    def test_identity_failure_before_snapshot_preserves_existing_save(self):
        with tempfile.TemporaryDirectory() as folder:
            s = self.make_session(Path(folder))
            save = s.lab / 'Save/user.sav'
            save.write_bytes(b'user-save-before-start')
            def fail_start():
                raise RuntimeError('Baseline identity mismatch')
            s.start = fail_start
            with self.assertRaisesRegex(RuntimeError, 'identity mismatch'):
                Session.__enter__(s)
            self.assertEqual(save.read_bytes(), b'user-save-before-start')

    def test_new_save_is_retained_and_archived_after_started_run(self):
        with tempfile.TemporaryDirectory() as folder:
            s = self.make_session(Path(folder), ready=True)
            save = s.lab / 'Save/new-user.sav'
            save.write_bytes(b'new-user-save')
            s.__exit__(None, None, None)
            self.assertEqual(save.read_bytes(), b'new-user-save')
            self.assertEqual((s.run / 'new-saves/new-user.sav').read_bytes(), save.read_bytes())
            self.assertEqual(s.result['preserved_new_saves'], [str(save)])

    def test_existing_save_restored_on_runtime_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            s = self.make_session(Path(folder), ready=True)
            save = s.lab / 'Save/existing.sav'
            save.write_bytes(b'original')
            stat = save.stat()
            s.mutable[save] = (save.read_bytes(), stat.st_atime_ns, stat.st_mtime_ns)
            s.before_saves.add(save)
            save.write_bytes(b'game-modified')
            s.__exit__(RuntimeError, RuntimeError('capture failed'), None)
            self.assertEqual(save.read_bytes(), b'original')
            self.assertTrue(json.loads((s.run / 'capture.json').read_text())['restored'])


if __name__ == '__main__':
    unittest.main()
