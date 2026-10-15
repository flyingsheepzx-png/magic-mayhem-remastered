"""Run actual compiled hook and native x86 validator on isolated RAM snapshots."""
import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from emulate_terrain_diagonal import Native

class TerrainDiagonal(unittest.TestCase):
    def setUp(self):self.n=Native();self.n.patch()
    def address(self,x,y,z):return 0x1000000+12*(x+80*y+6400*z)
    def flags(self,x,y,z,value):self.n.u.mem_write(self.address(x,y,z)+10,struct.pack('<H',value))
    def portal(self):return self.n.edge((54,74,5),(53,73,5))[0]
    def test_clear_slope_all_single_cell_heights(self):
        for h in (1,2,3,4,5,6,7,8):
            self.n.set_profile(h,1);self.assertEqual(self.portal(),1)
    def test_start_solid_obstacle_still_blocks(self):
        self.assertEqual(self.n.edge((58,78,4),(57,77,4))[0],0)
    def test_both_directions(self):
        self.assertEqual(self.portal(),1);self.assertEqual(self.n.edge((53,73,5),(54,74,5))[0],1)
    def test_multiplayer_unchanged(self):
        self.n.w(0x6e1f0c,2);self.assertEqual(self.portal(),0)
    def test_tall_unit_needs_headroom(self):
        self.flags(54,73,9,0x4000);self.assertEqual(self.portal(),0)
    def test_neighbor_unit_blocks(self):
        self.n.u.mem_write(self.address(54,73,6)+4,struct.pack('<H',123));self.flags(54,73,6,1)
        self.assertEqual(self.portal(),0)
    def test_lower_reservation_blocks(self):
        self.n.u.mem_write(self.address(54,73,5)+4,struct.pack('<H',123));self.flags(54,73,5,0x4001)
        self.assertEqual(self.portal(),0)
    def test_prop_is_not_terrain_exception(self):
        self.n.u.mem_write(self.address(54,73,5),struct.pack('<H',704));self.assertEqual(self.portal(),0)
    def test_missing_support_blocks(self):
        self.n.u.mem_write(self.address(54,73,6),struct.pack('<H',0));self.assertEqual(self.portal(),0)
    def test_cliff_height_blocks(self):
        self.n.w(0x1400000+540*0x164+0x94,16);self.assertEqual(self.portal(),0)
    def test_closed_door_blocks(self):
        self.n.u.mem_write(self.address(54,73,6)+2,struct.pack('<H',123));self.assertEqual(self.portal(),0)
    def test_large_unit_native_footprint_unchanged(self):
        n=Native();n.set_profile(4,2);self.n.set_profile(4,2)
        self.assertEqual(self.portal(),n.edge((54,74,5),(53,73,5))[0])
    def test_native_original_reproduces_report(self):
        n=Native();self.assertEqual(n.edge((54,74,5),(53,73,5)),[0,5])
        self.assertEqual(n.edge((54,74,5),(54,73,6)),[1,0])
    def test_rotated_and_reflected_terrain(self):
        original=bytes(self.n.u.mem_read(0x1000000,80*80*25*12))
        for reflect in (False,True):
            for turns in range(4):
                def transform(p):
                    x,y,z=p
                    if reflect:x=79-x
                    for _ in range(turns):x,y=79-y,x
                    return x,y,z
                rotated=bytearray(len(original))
                for z in range(25):
                    for y in range(80):
                        for x in range(80):
                            a=12*(x+80*y+6400*z);xx,yy,zz=transform((x,y,z));b=12*(xx+80*yy+6400*zz)
                            rotated[b:b+12]=original[a:a+12]
                self.n.u.mem_write(0x1000000,bytes(rotated))
                self.assertEqual(self.n.edge(transform((54,74,5)),transform((53,73,5)))[0],1)
                self.assertEqual(self.n.edge(transform((58,78,4)),transform((57,77,4)))[0],0)
    def test_special_movement_modes_keep_native_results(self):
        native=Native()
        for mode in (0,2):
            native.set_profile(4,1,mode);self.n.set_profile(4,1,mode)
            self.assertEqual(self.portal(),native.edge((54,74,5),(53,73,5))[0])
    def test_no_unit_index_or_faction_specific_gate(self):
        # profile+0x11 identifies a creature type, not a whitelist of heroes.
        for creature_type in (0,1,9,10,23,35):
            self.n.w(self.n.profile+0x11,creature_type);self.assertEqual(self.portal(),1)

if __name__=='__main__':unittest.main()
