"""Explicit bounded paired UI regressions while production keeps generating."""
import argparse
import compare_remastered_ui_11 as c

def run(case, name):
 lock=c.ROOT/'modernization/assets/hd/seedvr2-ui-1.1/test.lock'
 if lock.exists():raise RuntimeError('Existing test lock: inspect owner before testing')
 lock.write_text('Owned paired SeedVR2 background regression\n',encoding='utf-8')
 try:
  baseline={'settings-battle':'minimap-pair-20260930',
            'portmanteau-full':'port-full-after-20260930',
            'realm-loaded':'campaign-map-pair-20260930',
            'new-game-ui':'map-fix-pair-20260930'}[case]
  args=['--run','--candidate-in-place','--case',case,
        '--candidate-manifest-sha256',c.sha(c.CANDIDATE/'manifest.json'),
        '--baseline-capture',str(c.ROOT/'modernization/logs/remastered-ui'/baseline/'1.0/capture.json'),
        '--out',str(c.ROOT/'modernization/logs/remastered-ui'/name)]
  if case!='new-game-ui':
   fixture='test2-legacy.sav' if case=='settings-battle' else 'test5.sav'
   digest='56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d' if case=='settings-battle' else '2b00d8425eb01bb913b7b380f30f18f4e3d1948a0c05168c022819fca7205b7b'
   args+=['--fixture',str(c.CANDIDATE/'runtime/Save'/fixture),'--fixture-sha256',digest]
  c.main(args)
 finally:lock.unlink(missing_ok=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',required=True,choices=['settings-battle','portmanteau-full','realm-loaded','new-game-ui']);p.add_argument('--name',required=True)
 a=p.parse_args();run(a.case,a.name)
