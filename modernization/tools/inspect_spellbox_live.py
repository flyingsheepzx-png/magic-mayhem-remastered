from pathlib import Path
import ctypes,json,struct
from ctypes import wintypes
state=json.loads(Path('modernization/logs/hd-qol-background-session.json').read_text());pid=state['pid']
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.ReadProcessMemory.restype=wintypes.BOOL
k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x1010,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);c=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(c)) or c.value!=n:raise RuntimeError(hex(a))
 return b.raw
def d(a):return struct.unpack('<I',read(a,4))[0]
try:
 u=d(0x6def58);print('unit',hex(u),'spellbox',hex(0x6a2dd0))
 for base,off,ln in [(u,0x8e0,0x130),(0x6a2dd0,0x1800,0x140)]:
  print('BASE',hex(base),'OFFSET',hex(off))
  for o in range(off,off+ln,16):
   b=read(base+o,16)
   vals=struct.unpack('<4I',b)
   if any(vals):print(hex(o),*[hex(v) for v in vals])
 print('unit spells:')
 for o in range(0x900,0xb00,4):
  v=d(u+o)
  if v in (1,14,71,19,3,9,2):print(hex(o),v)
 print('battle slots',d(0x6a2dd0+0x1518))
 for i in range(min(d(0x6a2dd0+0x1518),12)):
  base=0x6a2dd0+0xfc+i*0xc6
  print('slot',i,'base',hex(base),'id',d(base+0xb5),'other',d(base+0xb9),'extra',d(base+0xbd),d(base+0xc1),read(base+0xc5,1).hex(),'rect',*[hex(d(base+x)) for x in (0x11,0x15,0x19,0x1d)])
finally:k.CloseHandle(h)
