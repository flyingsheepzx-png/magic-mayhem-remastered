"""Whole465440 profile reset and465500/465570 symmetric relation setters."""
import itertools,json,struct
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA

def reset(slot,fill):
    u=machine();base=0x643a80;u.mem_write(base,bytes([fill])*0xaa8)
    expected=bytearray(u.mem_read(base,0xaa8));p=slot*0x154
    for offset in (0,4,8):struct.pack_into('<I',expected,p+offset,0)
    for offset in (12,16,20):struct.pack_into('<I',expected,p+offset,0xffffffff)
    expected[p+0x18:p+0x20]=bytes([1])*8
    expected[p+0x20:p+0x50]=bytes(48)
    call(u,0x465440,base+p,[])
    assert bytes(u.mem_read(base,0xaa8))==bytes(expected)
    return dict(slot=slot,fill=fill)

def setter(src,dst,value,all_targets=False,table=0x18):
    u=machine();base=0x643a80;u.mem_write(base,b'\xa5'*0xaa8);put(u,0x5fbf28,'I',base)
    expected=bytearray(u.mem_read(base,0xaa8))
    for target in (range(8) if all_targets else (dst,)):
        if target==src:continue
        expected[src*0x154+table+target]=value&255
        expected[target*0x154+table+src]=value&255
    assert not all_targets or table==0x18
    entry=0x465570 if all_targets else {0x18:0x465500,0x20:0x4655e0,0x28:0x465650}[table]
    call(u,entry,base+src*0x154,[value] if all_targets else [dst,value])
    assert bytes(u.mem_read(base,0xaa8))==bytes(expected)
    return dict(src=src,dst=dst,value=value,all_targets=all_targets,table=hex(table),entry=hex(entry))

def verify():
    defaults=[reset(*v) for v in itertools.product(range(8),(0,165,255))]
    setters=[setter(*v) for v in itertools.product(range(8),range(8),(0,1,255,256))]
    allset=[setter(src,0,value,True) for src,value in itertools.product(range(8),(0,1,255,256))]
    secondary=[setter(src,dst,value,table=table) for src,dst,value,table in itertools.product(range(8),range(8),(0,1,255,256),(0x20,0x28))]
    report=dict(result='passed',engine_sha256=SHA,defaults=defaults,setters=setters,all_target_setters=allset,secondary_table_setters=secondary,
        scope='24 whole465440 no-double reset cases and288 whole465500/465570 relation-setter cases;complete8profile+selectiontail snapshot comparison. Reset0/4/8 zero,c/10/14 -1,18table ones,20/28 tableszero,30..4f wordszero,rest preserved. Pair/alltarget18 setters mirror offdiagonal byte writes,skipself,truncate byte. Meaning ofrole4 andtable labels/other writers/initialization/network pending;does not prove global symmetry invariant.')
    report['secondary_scope']='512 additional whole4655e0/465650 no-double pairsetters for20/28 tables. All8x8pairs/byte0,1,255,256;mirroroffdiagonal,truncation,selfskip;completeaa8 snapshot. Settercaller meaning/otherdirectwriters/global symmetry/save/network stillpending.'
    (ROOT/'modernization/docs/ai-profile-defaults-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',defaults=len(defaults),setters=len(setters)+len(allset),secondary=len(secondary)))

if __name__=='__main__':verify()
