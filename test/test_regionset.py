import unittest
from overviewer_core import world


class RegionSetTests(unittest.TestCase):
    def test_wall_blockids(self):
        w = world.RegionSet('.', '.')

        for mc_id in w._blockmap:
            block_id = w._blockmap[mc_id][0]
            is_wall = False

            if mc_id.endswith('_wall'):
                is_wall = True

            if 1792 <= block_id < 2048:
                self.assertTrue(is_wall, f'{mc_id} is in wall range')
            else:
                self.assertFalse(is_wall, f'{mc_id} is not in wall range')
