"""v26: double-press bound spell keys to submit a native validated self-cast."""
import argparse
import pefile
import install_qol_refresh as installer

installer.BUILD = installer.ROOT/'modernization/build/qol-double-key-v1'
installer.PACKAGE = installer.ROOT/'modernization/build/wide169/package-v26-qol-double-key'
installer.OLD = 'a7928183cd379f8c0885413c3d6007a4409b99ba9884c1e994994e0ee3e05f60'
installer.QOL = 'cfddc8c477284ff58fde4088d0b49563ddb513afae3f980f1281d4230a782c61'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'install', 'rollback'])
    action = parser.parse_args().action
    if action == 'build':
        engine = installer.ROOT/'game-wide169/Chaos-Wide169-engine.exe'
        assert installer.sha(engine) == installer.ENGINE
        native = pefile.PE(str(installer.ROOT/'game/Chaos.exe'))
        assert installer.sha(installer.ROOT/'game/Chaos.exe') == 'b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291'
        current = pefile.PE(str(engine))
        for start, size in ((0x57cf40, 0xea), (0x57ce70, 0xc8), (0x466870, 0x70)):
            assert native.get_data(start-0x400000, size) == current.get_data(start-0x400000, size)
    getattr(installer, action)()
