"""Build this repository's standalone GUI executable on Windows."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent
if os.name != 'nt':
    raise SystemExit('Windows EXE must be built on Windows.')
command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile',
           '--console', '--name', root.name, '--hidden-import', 'pdf_export',
           '--collect-all', 'reportlab']
for name in ('metadata.json', 'LICENSE', 'THIRD_PARTY_NOTICES.txt', 'config', 'assets'):
    destination = name if (root / name).is_dir() else '.'
    command += ['--add-data', str(root / name) + ';' + destination]
if (root / 'app.py').exists():
    command += ['--hidden-import', 'app']
if (root / 'prestige.ps1').exists():
    command += ['--add-data', 'prestige.ps1;.', '--add-data', 'src;src']
if (root / 'prestige_cli').exists():
    command += ['--add-data', 'prestige_cli/author.json;prestige_cli']
command.append('gui.py')
subprocess.run(command, cwd=root, check=True)
executable = root / 'dist' / (root.name + '.exe')
for arguments in (['--schema'], ['--smoke']):
    subprocess.run([str(executable), *arguments], cwd=root, check=True, timeout=90)
print(executable)
