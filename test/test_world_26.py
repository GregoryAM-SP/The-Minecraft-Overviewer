import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy
from PIL import Image

from overviewer_core import nbt, textures, world
from overviewer_core.blockstate_defaults import DEFAULT_BLOCK_PROPERTIES


class DimensionLayoutTests(unittest.TestCase):
    def test_legacy_and_namespaced_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, legacy in (("overworld", "DIM0"), ("the_nether", "DIM-1"),
                                 ("the_end", "DIM1")):
                for kind in ("region", "entities"):
                    suffix = "/entities" if kind == "entities" else ""
                    paths = [os.path.join("dimensions", "minecraft", name, kind),
                             kind if legacy == "DIM0" else os.path.join(legacy, kind)]
                    for rel in paths:
                        with self.subTest(rel=rel):
                            rset = world.RegionSet(directory, rel)
                            self.assertEqual(rset.get_type(), "minecraft:" + name + suffix)

    def test_custom_dimension_identity_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            dimension = os.path.join("dimensions", "example", "custom")
            rset = world.RegionSet(directory, os.path.join(dimension, "region"))
            self.assertEqual(rset.get_type(), dimension)

    def test_world_discovers_converted_overworld_and_ignores_poi(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "level.dat").touch()
            for rel in ("region", "dimensions/minecraft/overworld/region",
                        "dimensions/minecraft/overworld/entities",
                        "dimensions/minecraft/overworld/poi"):
                target = root / rel
                target.mkdir(parents=True)
                (target / "r.0.0.mca").touch()
            with patch.object(nbt, "load", return_value=("", {
                "Data": {"version": 19133, "LevelName": "Test"},
            })):
                result = world.World(directory)
            overworld = result.get_regionset("minecraft:overworld")
            self.assertEqual(overworld.rel,
                             os.path.join("dimensions", "minecraft", "overworld", "region"))
            self.assertIs(result.get_regionset(0), overworld)
            self.assertIsNotNone(result.get_regionset("minecraft:overworld/entities"))
            self.assertEqual(len(result.get_regionsets()), 3)


class BlockstateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.rset = world.RegionSet(self.directory.name, "region")

    def test_default_encodings_match_explicit_properties(self):
        for name in ("stone", "grass_block", "deepslate", "rail", "chest", "oak_log",
                     "oak_stairs", "oak_fence", "water", "lava", "sulfur_spike",
                     "potent_sulfur"):
            name = "minecraft:" + name
            explicit = {"Name": name, "Properties": DEFAULT_BLOCK_PROPERTIES.get(name, {})}
            for entry in (name, {"": name}, {"id": name}):
                with self.subTest(entry=entry):
                    self.assertEqual(self.rset._get_block(entry), self.rset._get_block(explicit))

    def test_new_properties_override_defaults_without_mutating_inputs(self):
        entry = {"id": "minecraft:oak_log", "properties": {"axis": "x"}}
        before = copy.deepcopy(entry)
        self.assertEqual(self.rset._get_block(entry), (17, 4))
        self.assertEqual(entry, before)
        self.assertEqual(DEFAULT_BLOCK_PROPERTIES["minecraft:oak_log"]["axis"], "y")
        self.assertEqual(self.rset._get_block("minecraft:chest"), (54, 2))

    def test_legacy_palette_is_not_reinterpreted(self):
        entry = {"Name": "minecraft:oak_log", "Properties": {"axis": "z"}}
        self.assertEqual(world.normalize_blockstate(entry),
                         {"id": "minecraft:oak_log", "properties": {"axis": "z"}})
        self.assertEqual(self.rset._get_block(entry), (17, 8))

    def test_malformed_new_states_are_explicit_errors(self):
        for entry in (None, 4, {}, {"id": 4}, {"id": "minecraft:stone", "properties": []},
                      {"id": "minecraft:stone", "properties": {"axis": 1}}):
            with self.subTest(entry=entry):
                with self.assertRaises(nbt.CorruptChunkError):
                    world.normalize_blockstate(entry)

    def chunk(self, palette, packed=None):
        states = {"palette": palette}
        if packed is not None:
            states["data"] = packed
        return {"DataVersion": 5023, "Status": "minecraft:full", "sections": [{
            "Y": 0, "block_states": states, "biomes": {"palette": ["minecraft:plains"]},
        }]}

    def read_chunk(self, chunk):
        region = Mock()
        region.load_chunk.return_value = ("", copy.deepcopy(chunk))
        with patch.object(self.rset, "_get_region_path", return_value="region.mca"), \
                patch.object(self.rset, "_get_regionobj", return_value=region):
            return self.rset.get_chunk(0, 0)

    def test_mixed_palette_decodes_all_4096_blocks(self):
        palette = ["minecraft:grass_block", {"": "minecraft:sulfur"},
                   {"id": "minecraft:oak_log", "properties": {"axis": "x"}},
                   {"Name": "minecraft:stone"}]
        packed = (sum((i % 4) << (4 * i) for i in range(16)),) * 256
        section = self.read_chunk(self.chunk(palette, packed))["Sections"][0]
        numpy.testing.assert_array_equal(section["Blocks"].ravel(),
                                         numpy.tile([2, 265, 17, 1], 1024))
        numpy.testing.assert_array_equal(section["Data"].ravel(),
                                         numpy.tile([0, 0, 4, 0], 1024))

    def test_single_palette_without_packed_data(self):
        section = self.read_chunk(self.chunk(["minecraft:chest"]))["Sections"][0]
        self.assertEqual(section["Blocks"].shape, (16, 16, 16))
        self.assertTrue(numpy.all(section["Blocks"] == 54))
        self.assertTrue(numpy.all(section["Data"] == 2))

    def test_unknown_block_is_reported_once(self):
        chunk = self.chunk(["example:unknown"])
        with self.assertLogs(level="WARNING") as logs:
            self.read_chunk(chunk)
            self.read_chunk(chunk)
        self.assertEqual(len(logs.output), 1)
        self.assertIn("example:unknown", logs.output[0])

    def test_bad_known_properties_do_not_silently_become_air(self):
        chunk = self.chunk([
            {"id": "minecraft:rail", "properties": {"shape": "invalid"}},
        ])
        with self.assertRaisesRegex(nbt.CorruptChunkError, "Invalid properties"):
            self.read_chunk(chunk)

    def test_new_biomes_and_unknown_biome_diagnostic(self):
        for name, expected in (("sulfur_caves", 65), ("dappled_forest", 66)):
            with self.subTest(name=name):
                section = {"biomes": {"palette": ["minecraft:" + name]}}
                result = self.rset._get_biomedata_v118(section)
                self.assertEqual(result.shape, (4, 4, 4))
                self.assertTrue(numpy.all(result == expected))
        with self.assertRaisesRegex(nbt.CorruptChunkError, "Unsupported biome"):
            self.rset._get_biomedata_v118({"biomes": {"palette": ["minecraft:future"]}})

    def test_sulfur_spike_direction_and_thickness(self):
        for direction, flag in (("up", 0), ("down", 8)):
            for thickness, value in (("tip", 0), ("tip_merge", 1), ("middle", 2),
                                     ("frustum", 3), ("base", 4)):
                block, data = self.rset._get_block({
                    "id": "minecraft:sulfur_spike",
                    "properties": {"vertical_direction": direction, "thickness": thickness},
                })
                self.assertEqual((block, data), (268, flag | value))
                tex = textures.Textures()
                with patch.object(tex, "load_image_texture",
                                  return_value=Image.new("RGBA", (16, 16), "yellow")) as load:
                    image = textures.blockmap_generators[block, data](tex, block, data)
                load.assert_called_once_with(
                    textures.BLOCKTEXTURE + "sulfur_spike_%s_%s.png" % (direction, thickness))
                self.assertIsNotNone(image)


class SpawnTests(unittest.TestCase):
    def test_spawn_uses_absolute_section_y_and_yzx_array_order(self):
        rset = Mock()
        blocks = numpy.ones((16, 16, 16), dtype=numpy.uint16)
        blocks[3, 5, 7] = 0
        rset.get_chunk.return_value = {"Sections": [
            {"Y": -4, "Blocks": numpy.zeros_like(blocks)},
            {"Y": 4, "Blocks": blocks},
        ]}
        level = world.World.__new__(world.World)
        level.leveldat = {"spawn": {"pos": (7, 63, 5), "dimension": "minecraft:overworld"}}
        level.get_regionset = Mock(return_value=rset)
        self.assertEqual(level.find_true_spawn(("overworld", "minecraft:overworld", 0, "minecraft:overworld")),
                         (7, 67, 5))
