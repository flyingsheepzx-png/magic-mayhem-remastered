"""Hash-gated read-only inspection of the native shutdown surface table."""
import ctypes,hashlib,json,struct,sys,time
from pathlib import Path
import verify_hd60_runtime as v

pid=int(sys.argv[1]);out=Path(sys.argv[2])
k=v.configured_kernel();h=k.OpenProcess(0x1010,False,pid)
if not h:raise ctypes.WinError(ctypes.get_last_error())
try:
 k.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)]
 path=ctypes.create_unicode_buffer(32768);n=ctypes.c_ulong(len(path))
 if not k.QueryFullProcessImageNameW(h,0,path,ctypes.byref(n)):raise ctypes.WinError(ctypes.get_last_error())
 engine=Path(path.value)
 assert engine==Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime/Chaos-Wide169-engine.exe')
 assert hashlib.sha256(engine.read_bytes()).hexdigest()=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
 rows=[]
 for _ in range(3):
  table=struct.unpack('<128I',v.read(k,h,0x6f6950,512))
  objects=[]
  for slot,p in enumerate(table):
   if not p:continue
   try:
    raw=v.read(k,h,p,48);words=struct.unpack('<12I',raw)
    objects.append(dict(slot=slot,address=hex(p),words=[hex(x) for x in words],raw=raw.hex()))
   except OSError as e:objects.append(dict(slot=slot,address=hex(p),error=str(e)))
  rows.append(dict(objects=objects,count=struct.unpack('<I',v.read(k,h,0x6f8154,4))[0],ddraw=v.read(k,h,0x6f98c0,20).hex(),cleanup_code=v.read(k,h,0x58acf0,41).hex()))
  time.sleep(.15)
 result=dict(pid=pid,path=str(engine),samples=rows)
 out.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
finally:k.CloseHandle(h)
