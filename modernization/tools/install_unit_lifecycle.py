"""v29: invalidate redirect/replay state on native unit reset and deserialize."""
import argparse
import pefile
import install_path_review as installer

installer.BUILD = installer.ROOT/'modernization/build/unit-lifecycle-v1'
installer.PACKAGE = installer.ROOT/'modernization/build/wide169/package-v29-unit-lifecycle'
installer.OLD = '44ed2a6cedacf57da5c0102d5126e485acd1a6a915fb3b8343a6183a2f2f830c'
installer.REPATH = '5b0c29c146b4e7b403ba8da045ffea37120a8941ed0d00d9771d4516f2849f4f'
installer.SOURCE_HEADERS = ('command_index.h',)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'install', 'rollback'])
    action=parser.parse_args().action
    if action=='build':
        engine=installer.ROOT/'game-wide169/Chaos-Wide169-engine.exe'
        native=installer.ROOT/'game/Chaos.exe'
        assert installer.sha(engine)==installer.ENGINE
        assert installer.sha(native)=='b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291'
        a,b=pefile.PE(str(native)),pefile.PE(str(engine))
        for address,size in ((0x5060a0,0x17b),(0x527310,0x30),(0x52c160,0x130)):
            assert a.get_data(address-0x400000,size)==b.get_data(address-0x400000,size)
        for address,expected in ((0x5060a0,'6aff681b245c00'),(0x527310,'81ec48010000')):
            assert b.get_data(address-0x400000,len(bytes.fromhex(expected))).hex()==expected
    getattr(installer,action)()
