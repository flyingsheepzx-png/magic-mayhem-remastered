"""v32: extend exhausted ground-click formation slots using native validation."""
import argparse
import pefile
import install_path_review as installer

installer.BUILD=installer.ROOT/'modernization/build/group-slots-v1'
installer.PACKAGE=installer.ROOT/'modernization/build/wide169/package-v32-group-slots'
installer.OLD='6ea707dc60df1f4baf3056b5f1cad443e1af493a396a6ba02df7546e8e6099ca'
installer.REPATH='acb354ea1e7d8ea1f8d90bbaeed671caaf96cb2536b2c19f99f619027f3173d4'
installer.SOURCE_HEADERS=('command_index.h',)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','install','rollback'])
    action=parser.parse_args().action
    if action=='build':
        engine=installer.ROOT/'game-wide169/Chaos-Wide169-engine.exe'
        original=installer.ROOT/'game/Chaos.exe'
        assert installer.sha(engine)==installer.ENGINE
        assert installer.sha(original)=='b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291'
        a,b=pefile.PE(str(original)),pefile.PE(str(engine))
        for address,size in ((0x517a50,0x430),(0x4fefa0,0x60),(0x414890,0x170)):
            assert a.get_data(address-0x400000,size)==b.get_data(address-0x400000,size)
        assert b.get_data(0x117a81,9).hex()=='83f8100f8fff020000'
    getattr(installer,action)()
