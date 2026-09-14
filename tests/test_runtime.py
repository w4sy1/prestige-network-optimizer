import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import runtime

class RuntimeTests(unittest.TestCase):
    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad';p.write_text('{')
            with self.assertRaises(ValueError): runtime.read_json(p)
    def test_missing_dependency(self):
        with patch('runtime.shutil.which',return_value=None):
            with self.assertRaises(FileNotFoundError):runtime.run(['missing'])
    def test_permission_denied(self):
        with patch('pathlib.Path.open',side_effect=PermissionError):
            with self.assertRaises(PermissionError):runtime.digest('fixture')
    def test_empty_folder(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(runtime.files(d),[])
    def test_system_error(self):
        with patch('runtime.shutil.which',return_value='test'),patch('runtime.subprocess.run',side_effect=OSError):
            with self.assertRaises(OSError):runtime.run(['test'])
    def test_path_escape(self):
        with self.assertRaises(ValueError):runtime.inside('.','../secret')
    def test_reports_escape_html(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(runtime.export({'text':'<script>secret</script>'},d,{'name':'test'}))
            self.assertNotIn('<script>',p.with_suffix('.html').read_text())
            self.assertEqual(runtime.read_json(p)['text'],'<script>secret</script>')
    def test_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'file';p.write_bytes(b'abc')
            self.assertEqual(runtime.digest(p),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

if __name__=='__main__':unittest.main()
