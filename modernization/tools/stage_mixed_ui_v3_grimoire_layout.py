"""Adapt traced Grimoire content pitch/clip instructions in isolated v3."""
import json
import struct
import capstone
import pefile
from wide169_build import ROOT
from stage_mixed_ui_v3_pages import sha

BASE=ROOT/'modernization/playtests/mixed-ui-v3'

def stage():
    from compare_hd_baseline import baseline_identity
    baseline_identity()
    path=BASE/'game-wide169/Chaos-Wide169-engine.exe';raw=path.read_bytes()
    if sha(raw)!='c19b01f77a8ae548e2acd027c3e782274380cde0cc4a50de4066167b9795d7ff':
        raise RuntimeError('Unknown native-page candidate')
    backup=BASE/'before-grimoire-layout'
    if backup.exists():raise RuntimeError('Preserve earlier layout evidence')
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);decoder.detail=True
    pe=pefile.PE(data=raw);output=bytearray(raw);changes=[]
    sites={0x4c842a:('cmp',40,80,'icon row height gate'),
           0x4c875c:('add',42,84,'caption horizontal offset'),
           0x4c8786:('mov',40,80,'caption row height'),
           0x4c8822:('mov',40,80,'empty caption row height')}
    for a in [0x4c7b34,0x4c82f0,0x4c86af,0x4ca1b3]:
        sites[a]=('add',480,1320,'native Grimoire content clip height')
    for a in [0x4c7b46,0x4c8302,0x4c86c1,0x4ca1c5]:
        sites[a]=('add',640,2400,'native Grimoire content clip width')
    for a,(mnemonic,old,new,label) in sites.items():
        offset=pe.get_offset_from_rva(a-0x400000)
        ins=next(decoder.disasm(raw[offset:offset+15],a,1))
        if ins.mnemonic!=mnemonic or ins.imm_size not in (1,4):raise RuntimeError(f'Unknown layout instruction {a:#x}')
        field=offset+ins.imm_offset
        if int.from_bytes(raw[field:field+ins.imm_size],'little')!=old:raise RuntimeError(f'Unknown layout value {a:#x}')
        output[field:field+ins.imm_size]=new.to_bytes(ins.imm_size,'little')
        changes.append(dict(va=hex(a),old=old,new=new,label=label))
    backup.mkdir();(backup/path.name).write_bytes(raw);path.write_bytes(output)
    report=dict(source_sha256=sha(raw),sha256=sha(output),patches=changes,status='staged-requires-paired-game-verification')
    (BASE/'grimoire-layout-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    m=json.loads((BASE/'manifest.json').read_text());m['files']['game-wide169/'+path.name]=sha(output)
    (BASE/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(report['sha256'])

if __name__=='__main__':stage()
