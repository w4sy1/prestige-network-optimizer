"""Standalone graphical shell. This file is copied into each independent project."""
from pathlib import Path
import argparse
import json
import os
import queue
import runpy
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,simpledialog

FROZEN=getattr(sys,'frozen',False)
BUNDLE=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
TOOLS_ROOT=Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
ROOT=(Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'PrestigeTech'/Path(sys.executable).stem) if FROZEN else Path(__file__).resolve().parent
if FROZEN:
    ROOT.mkdir(parents=True,exist_ok=True)
    for name in ('metadata.json','prestige.ps1','src'):
        source=BUNDLE/name
        if source.is_file():shutil.copy2(source,ROOT/name)
        elif source.is_dir():shutil.copytree(source,ROOT/name,dirs_exist_ok=True)
    if not (ROOT/'config/author.json').exists() and (BUNDLE/'config').exists():shutil.copytree(BUNDLE/'config',ROOT/'config',dirs_exist_ok=True)
    for name in ('logs','reports'):(ROOT/name).mkdir(exist_ok=True)
    os.environ['PRESTIGE_DATA_DIR']=str(ROOT)
    os.environ.setdefault('PRESTIGE_TOOLS_ROOT',str(TOOLS_ROOT))
LABELS={'command':'Operacja','root':'Folder źródłowy','file':'Plik','input':'Dane wejściowe JSON','output':'Folder raportów',
    'destination':'Miejsce docelowe','source':'Foldery źródłowe (po jednym w wierszu)','apply':'Wykonaj zmiany',
    'collect':'Zbierz dane','dry_run':'Tylko plan, bez wykonania','support':'Wesprzyj autora','manifest':'Manifest',
    'other':'Drugi plik lub folder','database':'Baza danych','archive':'Archiwum','target':'Adres docelowy',
    'provider':'Tryb analizy AI','model':'Model AI','preview_send':'Podgląd wysyłanych metryk, bez wysyłania',
    'backend':'Metoda obserwacji','count':'Liczba prób','cycles':'Liczba cykli','interval':'Odstęp (sekundy)',
    'profile':'Profil','device':'Urządzenie ADB','package':'Pakiety (po jednym w wierszu)','plan':'Plik planu',
    'quarantine':'Folder kwarantanny','before':'Stan przed','after':'Stan po','snapshot':'Plik migawki',
    'authorized':'Mam uprawnienia do testowania wskazanej sieci','cidr':'Podsieć IPv4/CIDR','directory':'Folder raportów'}

def schema():
    if (ROOT/'prestige.ps1').exists():
        fields=[{'dest':'Command','option':'-Command','choices':['modules','collect','network-test','updates-check','repair','cleanup-scan','cleanup-preview','cleanup-clean','cleanup-restore','support'],'default':'modules'},
            {'dest':'Modules','option':'-Modules','default':'all'}, {'dest':'Operation','option':'-Operation','choices':['sfc','dism-scan','dism-restore','flush-dns','winsock-reset','dhcp-renew'],'default':'dism-scan'}]
        fields += [{'dest':name,'option':'-'+name,'default':''} for name in ('OutputDirectory','PlanPath','QuarantineDirectory','Gateway','InternetTarget','DnsName')]
        fields += [{'dest':name,'option':'-'+name,'boolean':True,'default':False} for name in ('DryRun','Execute','AcceptNoRollback')]
        return fields
    import app
    if not hasattr(app,'build'):return [{'dest':'arguments','option':None,'multiple':True,'default':''}]
    fields=[]
    for action in app.build()._actions:
        if action.dest=='help':continue
        fields.append({'dest':action.dest,'option':action.option_strings[-1] if action.option_strings else None,
            'choices':list(action.choices) if action.choices is not None else None,'default':action.default,
            'boolean':isinstance(action,(argparse._StoreTrueAction,argparse._StoreFalseAction)),
            'multiple':isinstance(action,argparse._AppendAction) or action.nargs in ('*','+'),
            'append':isinstance(action,argparse._AppendAction),'help':action.help or ''})
    return fields

def arguments(fields,values):
    positional=[];options=[]
    for field in fields:
        value=values.get(field['dest'],'');option=field.get('option')
        if field.get('boolean'):
            if value and option:options.append(option)
            continue
        if value is None or str(value).strip()=='':continue
        values_list=str(value).splitlines() if field.get('multiple') else [str(value)]
        for item in values_list:
            if not item.strip():continue
            if option:options.extend([option,item.strip()])
            else:positional.append(item.strip())
    return positional+options

def backend_command(args):
    if (ROOT/'prestige.ps1').exists():return ['pwsh','-NoProfile','-File',str(ROOT/'prestige.ps1'),*args]
    if getattr(sys,'frozen',False):return [sys.executable,'--backend',*args]
    return [sys.executable,str(ROOT/'app.py'),*args]


class Window:
    def __init__(self,window):
        self.window=window;self.process=None;self.events=queue.Queue();self.variables={};self.fields=schema();self.last_output=''
        metadata=json.loads((ROOT/'metadata.json').read_text(encoding='utf-8'))
        window.title(metadata['name']+' | PRESTIGE TECH');window.geometry('1120x820');window.minsize(850,600)
        style=ttk.Style();style.theme_use('clam')
        style.configure('TFrame',background='#101b2b');style.configure('TLabel',background='#101b2b',foreground='#e5edf5',font=('Segoe UI',10))
        style.configure('TCheckbutton',background='#101b2b',foreground='#e5edf5');style.map('TCheckbutton',background=[('active','#20334a')])
        style.configure('TButton',padding=8,font=('Segoe UI',10));style.configure('Title.TLabel',font=('Segoe UI',22,'bold'),foreground='#4ee1b3')
        outer=ttk.Frame(window,padding=20);outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='PRESTIGE TECH',style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer,text='by Dominik Wasilak   /   '+metadata['name']+'   /   '+metadata['version']).pack(anchor='w',pady=(0,12))
        if 'termux' in ROOT.name:
            ttk.Label(outer,text='Ten program wymaga środowiska Termux na Androidzie. Windows EXE nie zastępuje Termuxa.',wraplength=1000).pack(anchor='w',pady=5)
        self.hub(outer)
        tabs=ttk.Notebook(outer);tabs.pack(fill='both',expand=True)
        form=ttk.Frame(tabs);result=ttk.Frame(tabs);tabs.add(form,text='Parametry operacji');tabs.add(result,text='Wynik i raport')
        canvas=tk.Canvas(form,background='#101b2b',highlightthickness=0);scroll=ttk.Scrollbar(form,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        body=ttk.Frame(canvas,padding=12);panel=canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda event:canvas.itemconfigure(panel,width=event.width))
        body.columnconfigure(1,weight=1)
        for index,field in enumerate(self.fields):
            name=field['dest'];label=LABELS.get(name,name.replace('_',' '))
            ttk.Label(body,text=label,wraplength=230).grid(row=index,column=0,sticky='nw',padx=(0,14),pady=7)
            if field.get('boolean'):
                variable=tk.BooleanVar(value=False);ttk.Checkbutton(body,variable=variable).grid(row=index,column=1,sticky='w')
            else:
                default=field.get('default');default='' if default is None or default==argparse.SUPPRESS else default
                if isinstance(default,(list,tuple)):default='\n'.join(map(str,default))
                variable=tk.StringVar(value=str(default))
                if field.get('multiple'):
                    widget=tk.Text(body,height=3,width=45);widget.insert('1.0',str(default));variable=widget
                elif field.get('choices'):widget=ttk.Combobox(body,textvariable=variable,values=['']+list(map(str,field['choices'])),state='readonly')
                else:widget=ttk.Entry(body,textvariable=variable)
                widget.grid(row=index,column=1,sticky='ew',pady=5)
                if not field.get('multiple') and any(word in name.lower() for word in ('file','root','input','output','directory','destination','manifest','archive','database','snapshot','plan','quarantine')):
                    ttk.Button(body,text='Wybierz…',command=lambda v=variable,n=name:self.browse(v,n)).grid(row=index,column=2,padx=5)
            self.variables[name]=variable
        self.output=tk.Text(result,wrap='word',background='#0a1320',foreground='#e5edf5',insertbackground='white',font=('Consolas',10));self.output.pack(fill='both',expand=True)
        self.service_form(tabs)
        self.status=tk.StringVar(value='Gotowy. Wybierz operację i parametry.');ttk.Label(outer,textvariable=self.status).pack(anchor='w',pady=8)
        buttons=ttk.Frame(outer);buttons.pack(fill='x')
        ttk.Button(buttons,text='Pokaż polecenie',command=self.preview).pack(side='left',padx=3)
        self.start=ttk.Button(buttons,text='Uruchom',command=lambda:self.run(tabs,result));self.start.pack(side='left',padx=3)
        ttk.Button(buttons,text='Przerwij',command=self.stop).pack(side='left',padx=3)
        ttk.Button(buttons,text='Zapisz wynik TXT',command=self.save).pack(side='right',padx=3)
        ttk.Button(buttons,text='Eksport PDF',command=self.pdf).pack(side='right',padx=3)
        if ROOT.name=='prestige-ai-diagnostic-assistant':ttk.Button(buttons,text='Klucz API na tę sesję',command=lambda:self.secret('OPENAI_API_KEY','Klucz OpenAI API')).pack(side='left',padx=3)
        if (ROOT/'signing.py').exists() or ROOT.name in ('prestige-hash-checker','prestige-integrity-monitor'):
            ttk.Button(buttons,text='Hasło klucza podpisu',command=lambda:self.secret('PRESTIGE_SIGNING_PASSWORD','Hasło szyfrowania klucza')).pack(side='left',padx=3)
        window.protocol('WM_DELETE_WINDOW',self.close);window.after(100,self.poll)

    def hub(self,parent):
        if ROOT.name not in ('prestige-tech-dashboard','prestige-tech-cli'):return
        frame=ttk.Frame(parent);frame.pack(fill='x',pady=(0,10))
        candidates={path.stem:path for path in sorted(TOOLS_ROOT.glob('prestige-*.exe')) if path.stem!=ROOT.name}
        candidates.update({path.name:path for path in sorted(TOOLS_ROOT.glob('prestige-*')) if path.is_dir() and path.name!=ROOT.name and (path/'gui.py').exists()})
        choices=list(candidates)
        selection=tk.StringVar(value=choices[0] if choices else '')
        ttk.Combobox(frame,values=choices,textvariable=selection,state='readonly',width=55).pack(side='left')
        def launch():
            if selection.get() not in choices:return
            target=candidates[selection.get()]
            command=[str(target)] if target.suffix=='.exe' else [sys.executable,str(target/'gui.py')]
            subprocess.Popen(command,cwd=target.parent if target.is_file() else target,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        ttk.Button(frame,text='Otwórz narzędzie',command=launch).pack(side='left',padx=8)

    def service_form(self,tabs):
        if ROOT.name!='prestige-repair-report':return
        import app
        page=ttk.Frame(tabs,padding=12);tabs.add(page,text='Zlecenie serwisowe');tabs.select(page)
        canvas=tk.Canvas(page,background='#101b2b',highlightthickness=0);scroll=ttk.Scrollbar(page,orient='vertical',command=canvas.yview)
        scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True);canvas.configure(yscrollcommand=scroll.set)
        body=ttk.Frame(canvas);panel=canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda event:canvas.itemconfigure(panel,width=event.width));body.columnconfigure(1,weight=1)
        values={};defaults=app.template()
        for index,(key,label) in enumerate(app.LABELS.items()):
            ttk.Label(body,text=label).grid(row=index,column=0,sticky='nw',pady=5,padx=(0,10))
            widget=tk.Text(body,height=3 if key in ('zgloszony_problem','diagnoza','wykonane_czynnosci','zalecenia') else 1,width=45)
            widget.insert('1.0','\n'.join(defaults[key]) if isinstance(defaults[key],list) else str(defaults[key]));widget.grid(row=index,column=1,sticky='ew',pady=5);values[key]=widget
        def generate():
            try:
                record={key:widget.get('1.0','end-1c') for key,widget in values.items()}
                record['czas_pracy_min']=float(record['czas_pracy_min']);record['czesci']=[line for line in record['czesci'].splitlines() if line.strip()]
                record=app.validate(record)
                directory=filedialog.askdirectory(title='Folder gotowego raportu')
                if not directory:return
                result=app.render(record,directory)
                from pdf_export import export_pdf
                pdf=Path(result['files'][0]).with_suffix('.pdf');export_pdf({app.LABELS[key]:value for key,value in record.items()},pdf,'Raport serwisowy')
                self.status.set('Zapisano HTML, JSON, TXT i PDF: '+str(pdf))
                messagebox.showinfo('Raport gotowy','Zapisano raport serwisowy w czterech formatach w wybranym folderze.')
            except Exception as exc:messagebox.showerror('Nie można wygenerować raportu',str(exc))
        ttk.Button(body,text='Wygeneruj raport HTML / JSON / TXT / PDF',command=generate).grid(row=len(values),column=0,columnspan=2,pady=15)

    def browse(self,variable,name):
        folder=any(word in name.lower() for word in ('root','directory','destination','output','quarantine'))
        value=filedialog.askdirectory() if folder else filedialog.askopenfilename()
        if value:variable.set(value)

    def secret(self,name,title):
        value=simpledialog.askstring(title,'Wartość pozostaje tylko w pamięci tej sesji. Nie zapisujemy jej w plikach ani raportach.',show='*',parent=self.window)
        if value:
            os.environ[name]=value;self.status.set('Ustawiono sekret dla tej sesji. Wartość jest ukryta.')

    def args(self):
        values={name:value.get('1.0','end-1c') if isinstance(value,tk.Text) else value.get() for name,value in self.variables.items()}
        return arguments(self.fields,values)

    def preview(self):messagebox.showinfo('Polecenie',subprocess.list2cmdline(backend_command(self.args())))

    def run(self,tabs,result):
        if self.process is not None:return
        args=self.args()
        if '--provider' in args and args[args.index('--provider')+1]=='openai' and '--preview-send' not in args and '--dry-run' not in args:
            if not messagebox.askyesno('Zewnętrzne AI','Wybrane metryki zostaną wysłane do OpenAI. Obowiązują warunki i opłaty konta API. Kontynuować?'):return
        self.output.delete('1.0','end');self.last_output='';self.start.configure(state='disabled');self.status.set('Uruchamianie…');tabs.select(result)
        try:
            self.process=subprocess.Popen(backend_command(args),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),start_new_session=os.name!='nt')
        except OSError as exc:
            self.start.configure(state='normal');self.status.set('Nie można uruchomić programu');messagebox.showerror('Brak backendu',str(exc));return
        process=self.process
        def read():
            for line in process.stdout:self.events.put(('text',line))
            self.events.put(('exit',process.wait()))
        threading.Thread(target=read,daemon=True).start()

    def poll(self):
        while not self.events.empty():
            kind,value=self.events.get()
            if kind=='text':
                self.last_output+=value;self.output.insert('end',value);self.output.see('end')
            else:
                self.process=None;self.start.configure(state='normal');self.status.set('Zakończono pomyślnie' if value==0 else 'Zakończono z kodem '+str(value)+' — sprawdź wynik')
        self.window.after(100,self.poll)

    def stop(self):
        if self.process and self.process.poll() is None:
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(self.process.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                import signal
                os.killpg(self.process.pid,signal.SIGTERM)
            self.status.set('Przerwano proces. Sprawdź plan/kopię operacji przed ponownym uruchomieniem.')

    def close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno('Operacja trwa','Zamknąć okno i przerwać uruchomiony proces?'):return
            self.stop()
        self.window.destroy()

    def save(self):
        path=filedialog.asksaveasfilename(defaultextension='.txt')
        if path:Path(path).write_text(self.last_output,encoding='utf-8')

    def pdf(self):
        path=filedialog.asksaveasfilename(defaultextension='.pdf')
        if not path:return
        try:
            from pdf_export import export_pdf
            export_pdf({'wynik':self.last_output},path,title=self.window.title())
            self.status.set('Zapisano PDF: '+path)
        except Exception as exc:messagebox.showerror('Eksport PDF',str(exc))


def main():
    if '--backend' in sys.argv:
        if (ROOT/'prestige.ps1').exists():raise SystemExit(subprocess.run(backend_command(sys.argv[sys.argv.index('--backend')+1:])).returncode)
        sys.argv=[str(ROOT/'app.py'),*sys.argv[sys.argv.index('--backend')+1:]]
        runpy.run_module('app',run_name='__main__');return
    if '--schema' in sys.argv:print(json.dumps(schema(),ensure_ascii=False,default=str));return
    if os.name=='nt' and getattr(sys,'frozen',False):
        import ctypes
        handle=ctypes.windll.kernel32.GetConsoleWindow()
        if handle:ctypes.windll.user32.ShowWindow(handle,0)
    window=tk.Tk()
    if '--smoke' in sys.argv:window.withdraw()
    Window(window)
    if '--smoke' in sys.argv:window.after(400,window.destroy)
    window.mainloop()


if __name__=='__main__':main()
