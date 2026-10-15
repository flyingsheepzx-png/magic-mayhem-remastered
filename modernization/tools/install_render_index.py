"""v28: indexed replay ownership, preserving exact first-match semantics."""
import argparse
import install_path_review as installer

installer.BUILD = installer.ROOT/'modernization/build/render-index-v1'
installer.PACKAGE = installer.ROOT/'modernization/build/wide169/package-v28-render-index'
installer.OLD = '685b7452096bd22ba1bbcb37a3dc78d6199fa147561b4cc1621890369742e16c'
installer.REPATH = '1f7f52edffb2681db7a8ef0f6effe6c344e2765278cad1877a9044ddbb610b7a'
installer.SOURCE_HEADERS = ('command_index.h',)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'install', 'rollback'])
    getattr(installer, parser.parse_args().action)()
