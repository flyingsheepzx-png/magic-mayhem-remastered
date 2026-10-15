"""Hash-gated realm toolbar geometry repair in isolated v4 only."""
import hashlib
import json
import shutil
import subprocess
import capstone
import pefile
from compare_hd_baseline import baseline_identity
from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB
from wide169_build import ROOT

SOURCE='324594eed030aa62fd1ac2e7355213f72c811b81726538d3456cb5330a1490bd'

def sha(data):return hashlib.sha256(data).hexdigest()

def stage():
    baseline_identity()
    path=LAB/'Chaos-Wide169-engine.exe';raw=path.read_bytes()
    if sha(raw)!=SOURCE:raise RuntimeError('Unknown v4 engine')
    backup=BASE/'before-realm-toolbar'
    if backup.exists() and (backup/'Chaos-Wide169-engine.exe').read_bytes()!=raw:
        raise RuntimeError('Previous toolbar backup differs')
    pe=pefile.PE(data=raw);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);cs.detail=True
    output=bytearray(raw);changes=[]
    for va,mnemonic,old,new in [(0x54fdb0,'mov',52,104),(0x54fdd2,'add',48,96),
                                  (0x54fdd5,'mov',4,8),(0x54ff5f,'mov',52,104)]:
        offset=pe.get_offset_from_rva(va-0x400000)
        ins=next(cs.disasm(raw[offset:offset+15],va,1));field=offset+ins.imm_offset
        if ins.mnemonic!=mnemonic or int.from_bytes(raw[field:field+ins.imm_size],'little')!=old:
            raise RuntimeError('Unknown toolbar instruction '+hex(va))
        output[field:field+ins.imm_size]=new.to_bytes(ins.imm_size,'little')
        changes.append(dict(va=hex(va),old=old,new=new))
    runtime=ROOT/'modernization/build/mixed-ui-v4-runtime'
    launcher=runtime/'launcher.cpp';launcher_raw=launcher.read_bytes()
    if SOURCE.encode() not in launcher_raw:raise RuntimeError('Launcher gate mismatch')
    if not backup.exists():
        backup.mkdir();shutil.copy2(path,backup/path.name)
        shutil.copy2(BASE/'game/Chaos-Mixed-UI-Preview.exe',backup/'Chaos-Mixed-UI-Preview.exe')
        (backup/'launcher.cpp').write_bytes(launcher_raw)
        (backup/'manifest.json').write_bytes((BASE/'manifest.json').read_bytes())
    try:
        path.write_bytes(output);launcher.write_bytes(launcher_raw.replace(SOURCE.encode(),sha(output).encode()))
        subprocess.run(['cmd','/c','build-candidate.cmd'],cwd=runtime,check=True,timeout=180)
        dest=BASE/'game/Chaos-Mixed-UI-Preview.exe';shutil.copy2(runtime/dest.name,dest)
        manifest=json.loads((BASE/'manifest.json').read_text())
        manifest['files']['game-wide169/Chaos-Wide169-engine.exe']=sha(output)
        manifest['files']['game/Chaos-Mixed-UI-Preview.exe']=sha(dest.read_bytes())
        (BASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    except Exception:
        path.write_bytes(raw);launcher.write_bytes(launcher_raw)
        shutil.copy2(backup/'Chaos-Mixed-UI-Preview.exe',BASE/'game/Chaos-Mixed-UI-Preview.exe')
        shutil.copy2(backup/'manifest.json',BASE/'manifest.json')
        raise
    report=dict(status='staged-requires-paired-verification',source_sha256=SOURCE,
                engine_sha256=sha(output),patches=changes)
    (BASE/'realm-toolbar-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':stage()
