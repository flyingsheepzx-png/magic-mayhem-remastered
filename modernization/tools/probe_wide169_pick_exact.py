"""Reversible test9 probe for exact sprite-mask unit picking."""
from pathlib import Path
import hashlib, json, struct, sys, time
import pefile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wide169_trial import ROOT, GAME, LAB, BUILD, Session, sha

ENGINE = LAB / 'Chaos-Wide169-engine.exe'
LAUNCHER = GAME / 'Chaos-Wide169-Trial.exe'
IDENTITY = BUILD / 'engine.json'
EXPECTED = '57b6327d178d798285c5ca64391c1fff5453c12b2af1c35438f117c298985626'

def main():
    original = {p:p.read_bytes() for p in (ENGINE,LAUNCHER,IDENTITY)}
    if sha(original[ENGINE]) != EXPECTED or sha(original[ENGINE]) != json.loads(original[IDENTITY])['sha256']:
        raise RuntimeError('Unknown development engine')
    pe = pefile.PE(data=original[ENGINE])
    offset = pe.get_offset_from_rva(0x4fa419-0x400000)
    old = bytes.fromhex('8b86bd000000')
    if original[ENGINE][offset:offset+6] != old: raise RuntimeError('Unknown pick fallback bytes')
    patch = b'\xe9' + struct.pack('<i',0x4fa4db-0x4fa419-5) + b'\x90'
    changed = bytearray(original[ENGINE]);changed[offset:offset+6] = patch
    newhash = sha(changed)
    marker_old = EXPECTED.encode('utf-16le');marker_new = newhash.encode('utf-16le')
    if original[LAUNCHER].count(marker_old) != 1:raise RuntimeError('Launcher hash marker missing')
    backup = ROOT/'modernization/backups/wide169'/('pick-probe-'+str(time.time_ns()))
    backup.mkdir(parents=True)
    for p,data in original.items():(backup/p.name).write_bytes(data)
    try:
        ENGINE.write_bytes(changed)
        LAUNCHER.write_bytes(original[LAUNCHER].replace(marker_old,marker_new))
        state=json.loads(original[IDENTITY]);state['sha256']=newhash
        IDENTITY.write_text(json.dumps(state,indent=2)+'\n')
        with Session() as s:
            s.load('test9')
            base=s.i(0x6def58);count=s.i(0x6def5c)
            for x,y in ((480,340),(540,340),(610,340),(640,320),(640,360),(740,500)):
                s.message(0x200,x,y);time.sleep(.08)
                ptr=s.i(0x656600)
                index=(ptr-base)//0xe4b if base<=ptr<base+count*0xe4b and (ptr-base)%0xe4b==0 else -1
                print(x,y,index,flush=True)
            s.click(610,340);time.sleep(.15)
            print('blank_selection',s.i(0x6e984c),s.i(base+0x68),flush=True)
            s.click(640,320);time.sleep(.15)
            print('hero_selection',s.i(0x6e984c),s.i(base+0x68),flush=True)
            print('report',s.run,flush=True)
    finally:
        for p,data in original.items():p.write_bytes(data)
        print('restored',backup,flush=True)

if __name__=='__main__':main()
