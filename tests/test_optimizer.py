from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app import assess,apply,interface

class OptimizerTests(unittest.TestCase):
    def test_worse(self):self.assertTrue(assess([10]*10,[30]*10)['recommend_rollback'])
    def test_loss(self):self.assertTrue(assess([10]*10,[None]*10)['recommend_rollback'])
    def test_invalid(self):
        with self.assertRaises(ValueError):interface(-1)
    def test_backup_before_change(self):
        with tempfile.TemporaryDirectory() as d:
            backup=Path(d)/'backup.json'
            def check(*args):self.assertTrue(backup.exists())
            with patch('app.snapshot',return_value={'index':1}),patch('app.measure',return_value=[1]*10),patch('app.change',side_effect=check):apply(1,'mtu',1400,backup)
