"""v37: half-transparent reveal of native-submitted opaque unit bodies."""
import argparse
import pefile
import install_path_review as installer

installer.BUILD=installer.ROOT/'modernization/build/speech-layout-v1'
installer.PACKAGE=installer.ROOT/'modernization/build/wide169/package-v37-speech-layout'
installer.OLD='6614d8876879755d25d2b0744d59dafd320c463bd0997e71b6b29b5045703f7d'
installer.REPATH='716c004dd13a6525c1c41e15a4bbf94302a11ce4b01d82ad8cb43c6190034a69'
installer.SOURCE_HEADERS=('command_index.h','ui_layout.h')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','install','rollback'])
    action=parser.parse_args().action
    if action=='build':
        engine=installer.ROOT/'game-wide169/Chaos-Wide169-engine.exe'
        original=installer.ROOT/'game/Chaos.exe'
        assert installer.sha(engine)==installer.ENGINE
        assert installer.sha(original)=='b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291'
        a,b=pefile.PE(str(original)),pefile.PE(str(engine))
        for address,size in ((0x57de00,0x740),(0x57dc20,0x60),(0x4fa61d,0x10),(0x4fa6fe,9),(0x4fa7c4,9),(0x500780,0x60),(0x573363,0x12)):
            assert a.get_data(address-0x400000,size)==b.get_data(address-0x400000,size)
    getattr(installer,action)()

