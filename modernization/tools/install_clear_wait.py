"""v33: wake recorded ordinary movement occupancy waits when the edge clears."""
import argparse
import pefile
import install_path_review as installer

installer.BUILD=installer.ROOT/'modernization/build/clear-wait-v1'
installer.PACKAGE=installer.ROOT/'modernization/build/wide169/package-v33-clear-wait'
installer.OLD='7826a458658809e67c9994dc1524df09cf10495168eb2b3c1bb4c35adbca0dc9'
installer.REPATH='4ef098328705e276531c47cc2f48bc4692e7d46fdd98f5b2d3e5c1dc8b14c1e6'
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
        for address,size in ((0x511bc9,0x77),(0x50f7c0,0x90),(0x514360,0x2d0)):
            assert a.get_data(address-0x400000,size)==b.get_data(address-0x400000,size)
        for address,expected in ((0x511bdd,'c7866c06000007000000'),(0x50f823,'8b866c060000')):
            assert b.get_data(address-0x400000,len(bytes.fromhex(expected))).hex()==expected
    getattr(installer,action)()
