"""v34: half-transparent reveal of native-submitted opaque unit bodies."""
import argparse
import pefile
import install_path_review as installer

installer.BUILD=installer.ROOT/'modernization/build/occluded-units-v1'
installer.PACKAGE=installer.ROOT/'modernization/build/wide169/package-v34-occluded-units'
installer.OLD='211f731a94be48d4adfe1240408c195be7f7d9ebd54a331d0761b739a7a852a1'
installer.REPATH='14f26593d6e6eb00651593d7b1a3365fd72dfa99fcbe0a59274f4a089657769c'
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
        for address,size in ((0x57de00,0x740),(0x57dc20,0x60),(0x4fa61d,0x10)):
            assert a.get_data(address-0x400000,size)==b.get_data(address-0x400000,size)
    getattr(installer,action)()
