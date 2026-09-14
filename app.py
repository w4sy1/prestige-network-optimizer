from pathlib import Path
import ipaddress
import statistics
import sys
from runtime import atomic_json,entry,parser,powershell,read_json

def interface(value):
    value=int(value)
    if not 1<=value<=65535:raise ValueError('Nieprawidłowy indeks interfejsu.')
    return value

def snapshot(index):
    index=interface(index)
    return powershell(f"$a=Get-NetAdapter -InterfaceIndex {index};$p=Get-ItemProperty ('HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\'+$a.InterfaceGuid);[pscustomobject]@{{index={index};dns=@((Get-DnsClientServerAddress -InterfaceIndex {index} -AddressFamily IPv4).ServerAddresses);automatic=[string]::IsNullOrWhiteSpace($p.NameServer);mtu=(Get-NetIPInterface -InterfaceIndex {index} -AddressFamily IPv4).NlMtu;link_speed=$a.LinkSpeed}}|ConvertTo-Json")

def measure(kind='dns',target=None,mtu=None):
    if kind=='mtu':
        target=str(ipaddress.IPv4Address(target))
        mtu=int(mtu)
        if not 576<=mtu<=9000:raise ValueError('MTU poza zakresem.')
        return powershell(f"$ping=[Net.NetworkInformation.Ping]::new();$options=[Net.NetworkInformation.PingOptions]::new(64,$true);$buffer=[byte[]]::new({mtu-28});$r=@();try{{1..10|ForEach-Object {{try{{$reply=$ping.Send('{target}',1000,$buffer,$options);if($reply.Status -eq 'Success'){{$r+=$reply.RoundtripTime}}else{{$r+=$null}}}}catch{{$r+=$null}}}}}}finally{{$ping.Dispose()}};ConvertTo-Json -InputObject $r",30)
    # Jawny pomiar systemowego resolvera; nie opróżnia cache.
    return powershell("$r=@();1..10|ForEach-Object {$s=[Diagnostics.Stopwatch]::StartNew();try{Resolve-DnsName example.com -DnsOnly -ErrorAction Stop|Out-Null;$r+=$s.Elapsed.TotalMilliseconds}catch{$r+=$null}};ConvertTo-Json -InputObject $r",90)

def assess(before,after):
    valid_before=[x for x in before if isinstance(x,(int,float))];valid_after=[x for x in after if isinstance(x,(int,float))]
    worse=len(valid_after)<len(valid_before) or (valid_before and valid_after and statistics.median(valid_after)>statistics.median(valid_before)*1.2)
    return {'before_median_ms':statistics.median(valid_before) if valid_before else None,'after_median_ms':statistics.median(valid_after) if valid_after else None,'recommend_rollback':bool(worse),'note':'Pomiar resolvera obejmuje cache i szum czasowy; nie dowodzi przyspieszenia łącza.'}

def inspect_modules(index):
    index=interface(index)
    script=f"$adapter=Get-NetAdapter -InterfaceIndex {index};$r=[ordered]@{{}};"
    queries={
        'tcp':'Get-NetTCPSetting | Select-Object SettingName,AutoTuningLevelLocal,CongestionProvider',
        'nic_power_saving':'Get-NetAdapterPowerManagement -Name $adapter.Name | Select-Object Name,AllowComputerToTurnOffDevice,SelectiveSuspend,DeviceSleepOnDisconnect,WakeOnMagicPacket',
        'ipv4_ipv6':f'Get-NetIPInterface -InterfaceIndex {index} | Select-Object AddressFamily,ConnectionState,Dhcp,NlMtu,InterfaceMetric',
        'bindings':'Get-NetAdapterBinding -Name $adapter.Name | Where-Object {$_.ComponentID -in @(\'ms_tcpip\',\'ms_tcpip6\')} | Select-Object ComponentID,Enabled',
        'dns_cache':'[pscustomobject]@{entries=@(Get-DnsClientCache).Count;note="Tylko liczba wpisów; nie eksportujemy odwiedzanych nazw."}'
    }
    for name,query in queries.items():
        script+=f"try{{$r['{name}']=@{{status='OK';data=@({query})}}}}catch{{$r['{name}']=@{{status='UNKNOWN';error=$_.Exception.GetType().Name}}}};"
    return powershell(script+'$r|ConvertTo-Json -Depth 6',90)

def change(index,kind,value):
    index=interface(index)
    if kind=='dns':
        values=[str(ipaddress.IPv4Address(v)) for v in value]
        if not values:raise ValueError('Brak DNS.')
        address=','.join("'"+v+"'" for v in values)
        script=f'Set-DnsClientServerAddress -InterfaceIndex {index} -ServerAddresses @({address})'
    elif kind=='automatic':script=f'Set-DnsClientServerAddress -InterfaceIndex {index} -ResetServerAddresses'
    elif kind=='mtu':
        mtu=int(value)
        if not 576<=mtu<=9000:raise ValueError('MTU poza zakresem.')
        script=f'Set-NetIPInterface -InterfaceIndex {index} -AddressFamily IPv4 -NlMtuBytes {mtu}'
    else:raise ValueError('Rodzaj zmiany.')
    return powershell(script+";[pscustomobject]@{changed=$true}|ConvertTo-Json")

def apply(index,kind,value,backup,target=None):
    backup=Path(backup)
    if backup.exists():raise FileExistsError(backup)
    if kind=='mtu' and not target:raise ValueError('Zmiana MTU wymaga IPv4 --probe-target do testów DF.')
    if target:target=str(ipaddress.IPv4Address(target))
    original=snapshot(index);before=measure(kind,target,original.get('mtu'))
    record={'schema_version':1,'original':original,'kind':kind,'value':value,'before':before,'status':'PREPARED','probe_target':target,
        'measurement':'ICMP DF z rozmiarem payload MTU-28; routing systemowy' if kind=='mtu' else 'Resolver systemowy z cache; routing systemowy'}
    atomic_json(backup,record)
    change(index,kind,value)
    record['status']='APPLIED';atomic_json(backup,record)
    after=measure(kind,target,value if kind=='mtu' else None);record['after']=after;record['comparison']=assess(before,after)
    if kind=='mtu':record['comparison']['note']='Test ICMP DF porównuje dostępność i RTT dla rozmiaru starego i nowego MTU. Brak ICMP nie dowodzi awarii; routing systemowy może użyć innego interfejsu.'
    atomic_json(backup,record)
    return record

def rollback(path,execute):
    record=read_json(path)
    if record.get('schema_version')!=1 or record.get('kind') not in ('dns','mtu'):raise ValueError('Nieprawidłowy backup.')
    original=record['original'];index=interface(original['index']);current=snapshot(index)
    if not execute:return {'plan':'Przywrócenie poprzedniego ustawienia','original':original,'current':current}
    if record['kind']=='dns':
        if current['dns']!=record['value']:raise ValueError('DNS zmieniono od czasu operacji; rollback odmówiony.')
        change(index,'automatic' if original['automatic'] else 'dns',original['dns'])
    else:
        if current['mtu']!=record['value']:raise ValueError('MTU zmieniono od czasu operacji.')
        change(index,'mtu',original['mtu'])
    return {'restored':True}

def build():
    p=parser('Bez magicznego boostera. Zmiany wymagają administratora i --apply.')
    p.add_argument('command',nargs='?',choices=['inspect','dns','mtu','rollback'])
    p.add_argument('--interface',type=int);p.add_argument('--server',action='append');p.add_argument('--value',type=int)
    p.add_argument('--backup');p.add_argument('--apply',action='store_true')
    p.add_argument('--probe-target',help='IPv4 odpowiadający na ICMP, wymagany przy zmianie MTU')
    return p

def handle(a):
    if a.command=='rollback' and a.backup:return rollback(a.backup,a.apply)
    if a.interface is None:raise ValueError('Podaj indeks interfejsu.')
    index=interface(a.interface)
    if a.command=='inspect':return {'interface':snapshot(index),'modules':inspect_modules(index),
        'recommendation':'Automatyczne zmiany TCP, energii karty i wyłączanie IPv6 nie są proponowane bez powtarzalnego pomiaru konkretnego problemu.'}
    if a.command=='dns':
        if not a.server:raise ValueError('Podaj DNS.')
        value=[str(ipaddress.IPv4Address(v)) for v in a.server]
    elif a.command=='mtu':
        if a.value is None or not 576<=a.value<=9000:raise ValueError('MTU 576–9000.')
        value=a.value
    else:raise ValueError('Wybierz polecenie.')
    if not a.apply:return {'plan':{'interface':index,'kind':a.command,'value':value},'steps':['TEST BEFORE','BACKUP','CHANGE','TEST AFTER','COMPARE','ROLLBACK na żądanie']}
    if not a.backup:raise ValueError('Podaj nowy plik backup.')
    return apply(index,a.command,value,a.backup,a.probe_target)

if __name__=='__main__':sys.exit(entry(build,handle))
