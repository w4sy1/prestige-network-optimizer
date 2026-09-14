"""Local stdlib helpers; this file is shipped inside each independent tool."""
from pathlib import Path
import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import uuid

for stream in (sys.stdout,sys.stderr):
    if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8',errors='replace')

ROOT = Path(__file__).resolve().parent
NOTICE = 'Narzędzie przeznaczone do celów edukacyjnych, diagnostycznych oraz do pracy z systemami i sieciami, których właścicielem jest użytkownik lub na których testowanie posiada zgodę.'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def read_json(path):
    path=Path(path)
    if path.stat().st_size > 64*1024*1024:
        raise ValueError('JSON przekracza limit 64 MiB.')
    return json.loads(path.read_text(encoding='utf-8-sig'))

def atomic_json(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

def digest(path, algorithm='sha256'):
    if algorithm not in ('sha256','sha512','sha1','md5'):
        raise ValueError('Nieobsługiwany algorytm.')
    h=hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def inside(root, relative):
    root=Path(root).resolve()
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts or ':' in str(rel):
        raise ValueError('Niebezpieczna ścieżka.')
    target=root/rel
    cursor=target
    while cursor != root:
        if cursor.is_symlink() or (hasattr(cursor,'is_junction') and cursor.is_junction()):
            raise ValueError('Dowiązania nie są obsługiwane.')
        cursor=cursor.parent
    target.resolve().relative_to(root)
    return target

def files(root):
    root=Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Wymagany zwykły katalog.')
    result=[]
    def fail(error):
        raise error
    for current, directories, names in os.walk(root, followlinks=False, onerror=fail):
        directories[:]=[d for d in directories if not (Path(current)/d).is_symlink() and not (hasattr(Path(current)/d,'is_junction') and (Path(current)/d).is_junction())]
        for name in sorted(names):
            path=Path(current)/name
            if path.is_symlink():
                continue
            if path.is_file():
                result.append(path)
    return sorted(result)

def run(command, timeout=60):
    if not command or not shutil.which(str(command[0])):
        raise FileNotFoundError('Brak wymaganego programu.')
    result=subprocess.run([str(c) for c in command], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout, shell=False)
    if result.returncode:
        raise RuntimeError(f'Backend zakończony kodem {result.returncode}.')
    return result.stdout

def powershell(script, timeout=90):
    if os.name != 'nt':
        raise OSError('Funkcja wymaga Windows.')
    executable=shutil.which('pwsh') or shutil.which('powershell')
    if not executable:
        raise FileNotFoundError('Brak PowerShell.')
    preamble="$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
    encoded=base64.b64encode((preamble+script).encode('utf-16le')).decode()
    text=run([executable,'-NoProfile','-NonInteractive','-EncodedCommand',encoded],timeout)
    return json.loads(text.lstrip('\ufeff')) if text.strip() else None

def log(action, result, error=None):
    (ROOT/'logs').mkdir(exist_ok=True)
    with (ROOT/'logs/audit.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(timestamp=now(),module=ROOT.name,action=action,result=result,error=error),ensure_ascii=False)+'\n')

def export(data, directory, metadata):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    base=directory/('report-'+uuid.uuid4().hex)
    text=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)
    documents={'json':text,'txt':f'PRESTIGE TECH\nby Dominik Wasilak\n{text}',
       'html':f'<!doctype html><html lang="pl"><meta charset="utf-8"><title>{html.escape(metadata["name"])}</title><style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;padding:20px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style><h1>PRESTIGE TECH</h1><p>by Dominik Wasilak</p><pre>{html.escape(text)}</pre></html>'}
    for extension,content in documents.items():
        base.with_suffix('.'+extension).write_text(content,encoding='utf-8')
    return str(base.with_suffix('.json'))

def parser(description):
    result=argparse.ArgumentParser(description=description)
    result.add_argument('--output',help='Katalog raportów JSON/TXT/HTML')
    result.add_argument('--dry-run',action='store_true',help='Pokaż plan bez wykonywania')
    result.add_argument('--support',action='store_true',help='Wesprzyj autora')
    return result

def entry(build, handler):
    p=build();args=p.parse_args()
    meta=read_json(ROOT/'metadata.json')
    print(f'PRESTIGE TECH\nby Dominik Wasilak\n{meta["name"]} v{meta["version"]}\n{NOTICE}',file=sys.stderr)
    try:
        if args.support:
            author=read_json(ROOT/'config/author.json')
            print(author.get('support_url') or 'Opcja wsparcia autora zostanie udostępniona w przyszłości.')
            return 0
        if args.dry_run:
            print(json.dumps({'dry_run':True,'plan':vars(args)},ensure_ascii=False))
            return 0
        data=handler(args)
        report=dict(schema_version=1,tool=meta['name'],version=meta['version'],created_utc=now(),data=data)
        if args.output:
            print(export(report,args.output,meta))
        else:
            print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
        code=2 if isinstance(data,dict) and data.get('ok') is False else 0
        log(getattr(args,'command',None) or 'run','PARTIAL' if code else 'OK')
        return code
    except (KeyboardInterrupt,EOFError):
        print('Przerwano.',file=sys.stderr)
        return 130
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,sqlite3.Error,subprocess.SubprocessError) as exc:
        try: log(getattr(args,'command',None) or 'run','ERROR',type(exc).__name__)
        except OSError: pass
        print(f'Błąd: {type(exc).__name__}. Sprawdź dane wejściowe, uprawnienia i zależności.',file=sys.stderr)
        return 1
