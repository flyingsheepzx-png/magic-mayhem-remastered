"""Recover tactical names from native config -> wizard profile -> unit flow."""
import configparser,json,re,struct
from verify_ai_model_native import NativeScore,ROOT,SHA

def recover():
    n=NativeScore(ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe')
    names=['AggressiveAttack','CautiousAttack','OccupyPowerPoint','CollectMana','EvadeDetection','Scout','Retreat','CollectFood','ProtectWizard']
    cfg=configparser.ConfigParser(strict=False);cfg.read('D:/Games/Magic&Mayham_Remastered_1.1/runtime/CFG/chaos.cfg',encoding='latin1')
    rows=[]
    for i,name in enumerate(names):
        needle=name.encode()+bytes([0]);p=n.image.find(needle);assert p>=0
        va=n.base+p;refs=[n.base+m.start() for m in re.finditer(re.escape(struct.pack('<I',va)),n.image)]
        assert len(refs)>=3
        rows.append(dict(action_id=i+6,name=name,registered=i+6 not in (7,10),unit_preference_offset=hex(0x936+i*4),wizard_profile_offset=hex(0x60+i*4),global_preference_va=hex(0x5e18c4+i*4),global_constructor_default=100,installed_personality=int(cfg['PERSONALITY'][name]),outcome_fraction_va=hex(0x6c4944+i*12),installed_outcome_fractions=[float(x) for x in cfg['OUTCOME_FRACTIONS'][name].split(',')],name_va=hex(va),name_references=[hex(x) for x in refs]))
    for r in rows:
        assert int(r['outcome_fraction_va'],16)==0x6c48fc+12*r['action_id']
        r['raw_model_score_formula']='min(0.999, OUTCOME_FRACTIONS[name][2]*P(label2) - OUTCOME_FRACTIONS[name][0]*P(label0))'
    return dict(engine_sha256=SHA,actions=rows,evidence=dict(global_config='0x4e4270',wizard_profile_general_override='0x590c10',default_profile_personality='0x592170',unit_profile_copy='0x592780',neutral_unit_constructor='0x5065e0',unit_score_bias='0x40edb0',eligibility='0x40eed0',outcome_fraction_direct_score='0x414ff0'),note='Names are native config strings, corroborated by profile+60..80 copied into unit+936..956. Constructor100 differs from actual global/profile personality. OUTCOME_FRACTIONS are directly the first/third class score weights, not inferred priors; middle weight is not used by414ff0.')

if __name__=='__main__':
    report=recover();(ROOT/'modernization/docs/ai-tactical-actions.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print([(r['action_id'],r['name'],r['installed_personality']) for r in report['actions']])
