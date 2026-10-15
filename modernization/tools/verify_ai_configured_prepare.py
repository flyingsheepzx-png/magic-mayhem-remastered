"""Configured four prepare animations staged from installed ANI records."""
import configparser,hashlib,json,struct
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_prepare_simulation import OFFSETS
from verify_ai_registration_lifecycle import MODE_FIELDS
from inspect_ai_animation_assets import RUNTIME

def verify():
    cfg_path=RUNTIME/'CFG/effectani.cfg';cfg_bytes=cfg_path.read_bytes()
    text=cfg_bytes.decode('latin1');text=text[text.index('[HEADER]'):]
    cfg=configparser.ConfigParser(inline_comment_prefixes=(';',),strict=False);cfg.read_string(text)
    prior=json.loads((ROOT/'modernization/docs/ai-animation-assets-verification.json').read_text())
    mapping=json.loads((ROOT/'modernization/docs/ai-effect-mapping-verification.json').read_text())
    assert mapping['result']=='passed' and mapping['engine_sha256']==SHA
    assert mapping['config_sha256']==hashlib.sha256(cfg_bytes).hexdigest()
    mapped={c['directory_index']:c for c in mapping['cases'] if 'directory_index' in c}
    assets={a['path'].split('\\')[-1].split('/')[-1].lower():a for a in prior['assets']}
    registry=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions'];cases=[]
    for row in registry:
        action=row['action_id']
        if action not in OFFSETS:continue
        effect_id=OFFSETS[action]//16;section=cfg[f'ANI_{effect_id}']
        filename=section['AnimationFileRef'].lower()+'.ani';animation=int(section['AnimationNo'])
        assert mapped[effect_id]['animation_value']==animation
        assert mapped[effect_id]['bank_index']==int(section['AnimationFileRef'][7:])
        asset=assets[filename];path=next(p for p in (RUNTIME/'Sprites').glob('*') if p.name.lower()==filename)
        raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==asset['sha256']
        count=struct.unpack_from('<I',raw,20)[0];record_start=44+count*4
        entry=asset['animations'][animation];assert entry['status']=='first_nonzero_event'
        for delay in (0,7,40):
            u=machine();a=0x2010000;directory=0x2020000;bank=0x2030000;indices=bank+0x400;records=bank+0x2000
            put(u,MODE_FIELDS[action],'I',0);put(u,0x6898d0,'I',directory);put(u,0x6894a0,'I',bank)
            put(u,directory+OFFSETS[action],'II',animation,0)
            put(u,bank+4,'II',indices,records);u.mem_write(indices,raw[44:record_start]);u.mem_write(records,raw[record_start:])
            put(u,a+0x14e,'I',delay);put(u,a+0x162,'B',1)
            duration=call(u,int(row['methods']['prepare_execute'],16),a,[])
            expected=delay+(8 if action==39 else 5)+entry['steps']
            assert duration==expected and bytes(u.mem_read(a+0x162,1))==b'\0'
            cases.append(dict(action_id=action,effect_directory_index=effect_id,animation=animation,asset=filename,asset_sha256=asset['sha256'],first_event=entry['event'],steps=entry['steps'],action_delay=delay,duration=duration))
    assert len(cases)==12 and cfg_path.read_bytes()==cfg_bytes
    report=dict(result='passed',engine_sha256=SHA,config_path=str(cfg_path),config_sha256=hashlib.sha256(cfg_bytes).hexdigest(),cases=cases,scope='Whole four mode0 native prepares on raw installed ANI instructions selected by effectani.cfg ANI_offset/16. Directory/bank manually staged,bank index normalized0; config/native file loader transformation unverified. No doubles,no player mutations. Validates configured first-event time conditionally on mapping/byte preservation.')
    (ROOT/'modernization/docs/ai-configured-prepare-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),animations=[{k:c[k] for k in ('action_id','asset','animation','steps','first_event')} for c in cases[::3]]))

if __name__=='__main__':verify()
