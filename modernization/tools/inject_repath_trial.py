"""Load the disposable rerouting DLL into a hash-verified owned x86 game."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import struct

from trace_engine import api, checked_file


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pid", type=int)
    ap.add_argument("dll", type=Path)
    args = ap.parse_args()
    dll = args.dll.resolve()
    data = dll.read_bytes()
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    if data[pe:pe+4]!=b"PE\0\0" or struct.unpack_from("<H", data,pe+4)[0]!=0x14c:
        raise RuntimeError("Trial DLL is not x86")
    k = api()
    digest = checked_file(k,args.pid)
    k.VirtualAllocEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,wintypes.DWORD]
    k.VirtualAllocEx.restype=ctypes.c_void_p
    k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.ReadProcessMemory.argtypes=k.WriteProcessMemory.argtypes
    k.CreateRemoteThread.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    k.CreateRemoteThread.restype=wintypes.HANDLE
    k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    k.GetExitCodeThread.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    k.VirtualFreeEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD]
    h=k.OpenProcess(0x103a,False,args.pid)
    if not h: raise ctypes.WinError(ctypes.get_last_error())
    remote=None
    thread=None
    try:
        n=ctypes.c_size_t()
        def read32(address):
            v=wintypes.DWORD()
            if not k.ReadProcessMemory(h,address,ctypes.byref(v),4,ctypes.byref(n)) or n.value!=4:
                raise ctypes.WinError(ctypes.get_last_error())
            return v.value
        # Resolve LoadLibraryA through this build's IAT, never the 64-bit
        # controller's kernel32 address. Import inspected from the known PE.
        # Discover and verify the import slot from the hash-verified image.
        exe=(Path(__file__).resolve().parents[2] / "game")/"Chaos.exe"
        blob=exe.read_bytes()
        header=struct.unpack_from("<I",blob,0x3c)[0]
        optional=header+24
        base=struct.unpack_from("<I",blob,optional+28)[0]
        imp_rva=struct.unpack_from("<I",blob,optional+104)[0]
        sections=struct.unpack_from("<H",blob,header+6)[0]
        section_table=optional+struct.unpack_from("<H",blob,header+20)[0]
        def offset(rva):
            for i in range(sections):
                vs,va,sz,raw=struct.unpack_from("<4I",blob,section_table+i*40+8)
                if va<=rva<va+max(vs,sz): return raw+rva-va
            raise RuntimeError("Invalid import RVA")
        found=None
        desc=offset(imp_rva)
        while any(blob[desc:desc+20]):
            original,_,_,name,thunk=struct.unpack_from("<5I",blob,desc)
            index=0
            while True:
                value=struct.unpack_from("<I",blob,offset(original or thunk)+index*4)[0]
                if not value: break
                if not value&0x80000000:
                    pos=offset(value)+2
                    label=blob[pos:blob.index(0,pos)]
                    if label==b"LoadLibraryA": found=base+thunk+index*4
                index+=1
            desc+=20
        if found is None: raise RuntimeError("LoadLibraryA import absent")
        loader=read32(found)
        if loader<0x10000 or loader>=0x100000000: raise RuntimeError("Invalid x86 loader")
        pathbytes=str(dll).encode("mbcs")+b"\0"
        remote=k.VirtualAllocEx(h,None,len(pathbytes),0x3000,4)
        if not remote or remote>=0x100000000: raise RuntimeError("Allocation failed")
        buf=ctypes.create_string_buffer(pathbytes)
        if not k.WriteProcessMemory(h,remote,buf,len(pathbytes),ctypes.byref(n)) or n.value!=len(pathbytes):
            raise ctypes.WinError(ctypes.get_last_error())
        tid=wintypes.DWORD()
        thread=k.CreateRemoteThread(h,None,0,loader,remote,0,ctypes.byref(tid))
        if not thread: raise ctypes.WinError(ctypes.get_last_error())
        if k.WaitForSingleObject(thread,10000)!=0: raise RuntimeError("DLL load did not finish")
        result=wintypes.DWORD()
        if not k.GetExitCodeThread(thread,ctypes.byref(result)) or not result.value:
            raise RuntimeError("DLL initialization failed")
        print(json.dumps({"pid":args.pid,"exe_sha256":digest,"dll_sha256":hashlib.sha256(data).hexdigest(),
                          "module":hex(result.value),"installed_files_modified":False,"experimental":True}))
    finally:
        if thread: k.CloseHandle(thread)
        if remote: k.VirtualFreeEx(h,remote,0,0x8000)
        k.CloseHandle(h)


if __name__=="__main__": main()
