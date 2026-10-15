"""v36: half-transparent reveal of native-submitted opaque unit bodies."""
import argparse
import pefile
import install_path_review as installer

installer.BUILD=installer.ROOT/'modernization/build/occluded-units-v3'
installer.PACKAGE=installer.ROOT/'modernization/build/wide169/package-v36-occluded-units-final'
installer.OLD='031b8d03e3aee332379bc6538c37ea31f9767f86ee8e2b7f5a9738cbfbb25b19'
installer.REPATH='415b65d38169b8465aa45e1b710cfcbb79b05a77e1d40f190f7fe4185c1b0604'
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
        for address,size in ((0x57de00,0x740),(0x57dc20,0x60),(0x4fa61d,0x10),(0x4fa6fe,9),(0x4fa7c4,9),(0x500780,0x60)):
            assert a.get_data(address-0x400000,size)==b.get_data(address-0x400000,size)
    getattr(installer,action)()

