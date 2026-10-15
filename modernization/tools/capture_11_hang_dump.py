"""Read-only, hash/PID gated minidump of a user-retained hung1.1 engine."""
import argparse,ctypes,struct,json,time
from ctypes import wintypes as W
from pathlib import Path
import build_remastered_11 as b
from verify_hd60_runtime import configured_kernel,read
from probe_11_close_wait import chains

def run(pid,name):
 k=configured_kernel();h=k.OpenProcess(0x1010,False,pid)
 if not h:raise ctypes.WinError(ctypes.get_last_error())
 k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
 k.QueryFullProcessImageNameW.restype=W.BOOL
 try:
  buf=ctypes.create_unicode_buffer(32768);length=W.DWORD(32768)
  if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(length)):raise ctypes.WinError(ctypes.get_last_error())
  path=Path(buf.value).resolve();assert path==(b.TARGET/'runtime/Chaos-Wide169-engine.exe').resolve()
  assert b.sha(path)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  out=b.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
  states=[]
  for _ in range(2):
   states.append({hex(a):int.from_bytes(read(k,h,a,4),'little',signed=True) for a in [0x641fbc,0x6903e8,0x642c68,0x6df180,0x6def58,0x6c54dc]});time.sleep(.1)
  b.write(out/'wait-chains.json',chains(pid))
  dll=Path('C:/Program Files (x86)/Windows Kits/10/Debuggers/x64/dbghelp.dll')
  dbg=ctypes.WinDLL(str(dll),use_last_error=True)
  dbg.MiniDumpWriteDump.argtypes=[W.HANDLE,W.DWORD,W.HANDLE,W.DWORD,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
  dbg.MiniDumpWriteDump.restype=W.BOOL
  import msvcrt
  with (out/'hang.dmp').open('wb') as f:
   if not dbg.MiniDumpWriteDump(h,pid,msvcrt.get_osfhandle(f.fileno()),0x1820,None,None,None):raise ctypes.WinError(ctypes.get_last_error())
  raw=(out/'hang.dmp').read_bytes();assert raw[:4]==b'MDMP'
  count,directory=struct.unpack_from('<II',raw,8);streams={}
  for i in range(count):
   typ,size,rva=struct.unpack_from('<III',raw,directory+12*i);streams[typ]=(size,rva)
  threads=[]
  if 3 in streams:
   start=streams[3][1];n=struct.unpack_from('<I',raw,start)[0]
   for i in range(n):
    row=start+4+i*48;tid=struct.unpack_from('<I',raw,row)[0]
    stack_base,stack_size,stack_rva,context_size,context_rva=struct.unpack_from('<QIIII',raw,row+24)
    ctx=raw[context_rva:context_rva+context_size]
    info=dict(tid=tid,stack_base=hex(stack_base),context_size=context_size)
    if len(ctx)>=204 and struct.unpack_from('<I',ctx)[0]&0x10000:
     info.update(eip=hex(struct.unpack_from('<I',ctx,184)[0]),esp=hex(struct.unpack_from('<I',ctx,196)[0]),ebp=hex(struct.unpack_from('<I',ctx,180)[0]))
    stack=raw[stack_rva:stack_rva+stack_size]
    info['stack_words']=[hex(v) for v in struct.unpack('<'+'I'*(min(len(stack),4096)//4),stack[:min(len(stack),4096)//4*4])]
    threads.append(info)
  modules=[]
  if 4 in streams:
   start=streams[4][1];n=struct.unpack_from('<I',raw,start)[0]
   for i in range(n):
    row=start+4+i*108;base,size=struct.unpack_from('<QI',raw,row);rva=struct.unpack_from('<I',raw,row+20)[0];length=struct.unpack_from('<I',raw,rva)[0]
    modules.append(dict(base=hex(base),size=size,path=raw[rva+4:rva+4+length].decode('utf-16le')))
  b.write(out/'summary.json',dict(pid=pid,engine_sha256=b.sha(path),states=states,threads=threads,modules=modules,dump_sha256=b.sha(out/'hang.dmp'),scope='No input, suspension API, memory write or termination; MiniDumpWriteDump observes process'))
  print(out,'threads',len(threads),[(x['tid'],x.get('eip')) for x in threads],flush=True)
 finally:k.CloseHandle(h)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--name',required=True);a=p.parse_args();run(a.pid,a.name)
