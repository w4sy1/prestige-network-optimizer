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
            with patch('app.snapshot',return_value={'index':1,'mtu':1500}),patch('app.measure',return_value=[1]*10),patch('app.change',side_effect=check):apply(1,'mtu',1400,backup,'192.168.1.1')

    def test_mtu_uses_actual_old_and_new_sizes(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch('app.snapshot',return_value={'index':1,'mtu':1500}),patch('app.measure',return_value=[1]*10) as measurement,patch('app.change'):
                apply(1,'mtu',1400,Path(temporary)/'backup.json','192.168.1.1')
                self.assertEqual(measurement.call_args_list[0].args,('mtu','192.168.1.1',1500))
                self.assertEqual(measurement.call_args_list[1].args,('mtu','192.168.1.1',1400))

    def test_mtu_requires_probe_before_change(self):
        with tempfile.TemporaryDirectory() as temporary,patch('app.change') as change:
            with self.assertRaises(ValueError):apply(1,'mtu',1400,Path(temporary)/'backup.json')
            change.assert_not_called()
