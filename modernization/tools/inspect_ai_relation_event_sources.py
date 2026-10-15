"""Hash-gated static spell dispatch and direct counter call evidence."""
import configparser,hashlib,json,struct
from verify_ai_training_math import native
from verify_ai_model_native import ROOT,SHA

def inspect():
    cfgpath=ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Cfg/Spells.cfg'
    raw=cfgpath.read_bytes();cfg=configparser.ConfigParser(interpolation=None,strict=False);cfg.read_string(raw.decode('latin1'))
    mapped=[]
    for spell,call in ((50,0x48d11d),(54,0x48c07e)):
        index=native.image[0x48ead0-0x400000+spell]
        target=struct.unpack_from('<I',native.image,0x48ea2c-0x400000+4*index)[0]
        code=native.image[call-0x400000:call-0x400000+5]
        assert code[0]==0xe8 and call+5+struct.unpack_from('<i',code,1)[0]==0x4656c0
        assert native.image[call-2-0x400000:call-0x400000]==b'\x6a\x64'
        mapped.append(dict(spell=spell,label=cfg[f'SPELL_{spell}']['TextName'],dispatch_byte_index=index,
                           dispatch_target=hex(target),counter_call=hex(call),call_bytes=code.hex(),delta=100))
    report=dict(engine_sha256=SHA,result='passed',config_sha256=hashlib.sha256(raw).hexdigest(),spell_mappings=mapped,
        static_exports='D:/Tools/magic-mayhem-re/projects/ai-review-20261001/functions-relation-events',
        function_entries=dict(effect_dispatch='0x48b0f0',profile28_caller='0x5606f0',profile20_caller='0x56a8d0'),
        scope='Exact48b173..48b18a spellID4c/twoleveljumptable verifieddisassembly;Ghidra containingfunction exports identifycases50Lure/54Subversion andbothdirectdelta100calls,callbytes checkedhere. NativeLureprefix separatelyverified;Subversiongates/probability/ownership effectpending. Ghidra48b0f0 warns unreachable/typepropagation;notcomplete recoveredsource. Profile20/28 callerentries identified,meaning stillpending.')
    (ROOT/'modernization/docs/ai-relation-event-sources.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(mapped)

if __name__=='__main__':inspect()
