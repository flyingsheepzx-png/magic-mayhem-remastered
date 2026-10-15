"""v25: allow bindings on purchased empty talisman slots; preserve v24 fixes."""
import argparse
import install_qol_refresh as installer

installer.BUILD = installer.ROOT/'modernization/build/qol-empty-slots-v1'
installer.PACKAGE = installer.ROOT/'modernization/build/wide169/package-v25-qol-empty-slots'
installer.OLD = '69018495fde8109d18f4aea69aefc2e1b9eb762b4c50045d7a39fda34e5bdac5'
installer.QOL = '14b047815a6aa54df179831f90b6e858f1e75e8a771bb584fda0ea055024765e'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'install', 'rollback'])
    action = parser.parse_args().action
    getattr(installer, action)()
