"""v30: bounded 600-expansion ordinary searches in single-player."""
import argparse
import pefile
import install_path_review as installer

installer.BUILD = installer.ROOT/'modernization/build/search-budget-v1'
installer.PACKAGE = installer.ROOT/'modernization/build/wide169/package-v30-search-budget'
installer.OLD = '00cb0da333587c05d5edc135006a8b3e25f94538a8a4b6ccb0d00bea611b975a'
installer.REPATH = '13c95b9c40f5ba0c7c7b22e154354e7a7d5d3e976b41c4a664155301a535316c'
installer.SOURCE_HEADERS = ('command_index.h',)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['build','install','rollback'])
    action=parser.parse_args().action
    if action=='build':
        engine=installer.ROOT/'game-wide169/Chaos-Wide169-engine.exe'
        original=installer.ROOT/'game/Chaos.exe'
        assert installer.sha(engine)==installer.ENGINE
        assert installer.sha(original)=='b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291'
        a,b=pefile.PE(str(original)),pefile.PE(str(engine))
        for address,size in ((0x5130d4,0x290),(0x54b800,0x640),
                             (0x4ebae0,0xbc0),(0x440260,0x190)):
            assert a.get_data(address-0x400000,size)==b.get_data(address-0x400000,size)
        assert b.get_data(0x113162,6).hex()=='8b3588f16d00'
    getattr(installer,action)()
