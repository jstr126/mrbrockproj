"""Deploy the self-hosted camera server through an existing SSH connection."""
import argparse
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import time


def bundle(root, model):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        files = [root / 'bolt_sizer' / (name + '.py') for name in
                 ('__init__', 'board', 'catalog', 'standards', 'infer', 'measure')]
        files += [p for p in (root / 'pi_web').rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts]
        files.append(root / 'tools/deploy_pi.py')
        for p in files:
            archive.add(p, arcname=str(p.relative_to(root)), recursive=False)
        archive.add(model, arcname='models/' + model.name, recursive=False)
    return output.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', help='existing SSH user@hostname or SSH alias')
    ap.add_argument('--ssh-port', type=int, default=22)
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--bind', default='0.0.0.0', help='LAN by default; use 127.0.0.1 for SSH-only access')
    ap.add_argument('--camera', default='0')
    ap.add_argument('--model', default='models/boltnet_v3.onnx')
    a = ap.parse_args()
    if a.target.startswith('-') or any(c.isspace() for c in a.target):
        ap.error('target must be one SSH address or alias')
    if not 1 <= a.port <= 65535 or not 1 <= a.ssh_port <= 65535:
        ap.error('ports must be between 1 and 65535')
    root = Path(__file__).resolve().parents[1]
    model = Path(a.model).resolve()
    if not model.is_file():
        ap.error(f'model does not exist: {model}')
    ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-p', str(a.ssh_port), a.target]
    def remote(code, payload=None, capture=False):
        return subprocess.run([*ssh, 'python3 -c ' + shlex.quote(code)], input=payload,
                              check=True, capture_output=capture)
    probe = remote("import json,platform,sys;from pathlib import Path;print(json.dumps({'home':str(Path.home()),'arch':platform.machine(),'system':platform.system(),'python':list(sys.version_info[:3])}))", capture=True)
    info = json.loads(probe.stdout)
    if info['system'] != 'Linux' or info['arch'] not in ('aarch64', 'arm64'):
        raise SystemExit(f"This package requires a 64-bit ARM Linux Pi; found {info['system']} {info['arch']}")
    if info['python'] < [3, 10]:
        raise SystemExit('Python 3.10 or newer is required')
    print('SSH connected:', info['arch'], 'Python', '.'.join(map(str, info['python'])), flush=True)
    base = str(Path(info['home']) / 'bolt-sorter')
    release = str(Path(base) / 'releases' / str(time.time_ns()))
    archive_path = str(Path(base) / ('upload-' + str(time.time_ns()) + '.tar.gz'))
    upload = f"from pathlib import Path;import sys;p=Path({archive_path!r});p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(sys.stdin.buffer.read())"
    remote(upload, bundle(root, model))
    setup = f'''
import os,signal,subprocess,sys,tarfile,time,urllib.request,json
from pathlib import Path
base=Path({base!r});release=Path({release!r});package=Path({archive_path!r})
release.mkdir(parents=True)
with tarfile.open(package) as archive:
    for member in archive.getmembers():
        p=Path(member.name)
        if p.is_absolute() or '..' in p.parts or not (member.isfile() or member.isdir()):raise RuntimeError('Unsafe package path')
    archive.extractall(release,filter='data') if sys.version_info>=(3,12) else archive.extractall(release)
package.unlink()
venv=base/'.venv'
if not (venv/'bin/python').exists():subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
python=str(venv/'bin/python')
subprocess.run([python,'-m','pip','install','--only-binary=:all:','-r',str(release/'pi_web/requirements.txt')],check=True)
pidfile=base/'server.pid'
if pidfile.exists():
    pid=int(pidfile.read_text())
    proc=Path('/proc')/str(pid)
    if proc.exists():
        command=(proc/'cmdline').read_bytes()
        cwd=(proc/'cwd').resolve()
        if b'pi_web.server' not in command or base not in cwd.parents or proc.stat().st_uid!=os.getuid():raise RuntimeError('Recorded PID is not this deployment; refusing to stop it')
        os.kill(pid,signal.SIGTERM)
        for _ in range(50):
            if not proc.exists():break
            time.sleep(.1)
        if proc.exists():raise RuntimeError('Previous server did not stop')
current=base/'current'
if current.exists() and not current.is_symlink():raise RuntimeError('current is an existing non-symlink directory')
link=base/'current.new';link.unlink(missing_ok=True);link.symlink_to(release,target_is_directory=True);link.replace(current)
with open(base/'server.log','ab') as log:
    process=subprocess.Popen([python,'-m','pi_web.server','--model','models/{model.name}','--camera',{a.camera!r},'--bind',{a.bind!r},'--port',{str(a.port)!r}],cwd=release,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
pidfile.write_text(str(process.pid))
for attempt in range(100):
    if process.poll() is not None:raise RuntimeError('Server exited; inspect '+str(base/'server.log'))
    try:
        with urllib.request.urlopen('http://{a.bind if a.bind != '0.0.0.0' else '127.0.0.1'}:{a.port}/api/health',timeout=2) as response:health=json.load(response)
        if health.get('server_pid')!=process.pid or health['state']=='starting':
            time.sleep(.2)
            continue
        urls=[]
        if {a.bind!r}=='0.0.0.0':
            try:
                interfaces=json.loads(subprocess.check_output(['ip','-j','-4','addr','show']))
                for interface in interfaces:
                    if interface['ifname']=='lo':continue
                    for address in interface.get('addr_info',[]):
                        if address.get('family')=='inet':urls.append({{'interface':interface['ifname'],'url':'http://'+address['local']+':{a.port}'}})
            except (OSError,subprocess.CalledProcessError):pass
        else:urls=[{{'interface':'configured bind','url':'http://{a.bind}:{a.port}'}}]
        print(json.dumps({{'lan_urls':urls,'pid':process.pid,'release':str(release),'health':health}}),flush=True)
        break
    except OSError:time.sleep(.2)
else:raise RuntimeError('Server did not become healthy; inspect '+str(base/'server.log'))
'''
    remote(setup)
    print('Open a Pi LAN URL shown above from any computer on the same Ethernet/LAN. Viewers need only a browser.', flush=True)
    print('Optional encrypted SSH tunnel for access from outside that LAN:', flush=True)
    print(shlex.join(['ssh', '-N', '-o', 'ExitOnForwardFailure=yes', '-p', str(a.ssh_port),
                      '-L', f'8788:127.0.0.1:{a.port}', a.target]), flush=True)
    print('Then open http://127.0.0.1:8788', flush=True)


if __name__ == '__main__':
    main()
