"""Hash-gated destination-marker correction; rollback restores response-v1."""
import argparse
import install_11_command_response as prior
prior.base.OUT=prior.base.b.ROOT/'modernization/build/remastered-1.1-command-response-v2'
prior.base.BACK=prior.base.b.ROOT/'modernization/backups/remastered-1.1-command-response-v2'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['install','rollback']);a=p.parse_args()
 if a.action=='install':prior.install()
 else:prior.base.rollback()
