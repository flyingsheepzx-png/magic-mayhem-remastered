"""Native game formats must survive release cleanup, independently of inventory."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from release_remastered_11 import excluded

class ReleaseAssetPolicy(unittest.TestCase):
    def test_native_world_sections_are_runtime_data(self):
        for path in ['Realms/Celtic/Tutorial/CTsec00.map','Realms/Greek/Island/GIsec12.MAP',
                     'Realms/Medieval/Castle/MCsec01.map','Realms/Multiplayer/Map01.map']:
            self.assertFalse(excluded(path),path)

    def test_player_and_probe_outputs_are_excluded(self):
        for path in ['Save/test18.sav','ss/shot.png','modernization/logs/wrapper.csv',
                     'fmv-h264-events.jsonl','wide169-lab.json','Uninst.isu']:
            self.assertTrue(excluded(path),path)

if __name__=='__main__':unittest.main()
