from io import BytesIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import numpy
from PIL import Image

from overviewer_core import textures


class TextureVersionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.environment = patch.dict(os.environ, {
            "APPDATA": str(self.root), "HOME": str(self.root),
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def archive(self, name, images):
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            for filename, image in images.items():
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                archive.writestr(filename, buffer.getvalue())
        return path

    def texture_object(self, path):
        result = textures.Textures(texturepath=str(path))
        self.addCleanup(lambda: [jar.close() for jar in result.jars.values()])
        return result

    def test_renamed_asset_keeps_explicit_pack_precedence(self):
        modern = textures.BLOCKTEXTURE + "quartz_pillar_side.png"
        legacy = textures.BLOCKTEXTURE + "quartz_pillar.png"
        pack = self.archive("custom.zip", {legacy: Image.new("RGBA", (16, 16), "red")})
        fallback = self.archive("fallback.jar", {modern: Image.new("RGBA", (16, 16), "blue")})
        tex = self.texture_object(pack)
        tex.jars[str(fallback)] = zipfile.ZipFile(fallback)
        image = tex.load_image_texture((modern, legacy))
        self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))

    def test_renamed_asset_in_current_jar_precedes_cached_old_jar(self):
        modern = textures.BLOCKTEXTURE + "purpur_pillar_side.png"
        legacy = textures.BLOCKTEXTURE + "purpur_pillar.png"
        pack = self.archive("current.zip", {modern: Image.new("RGBA", (16, 16), "blue")})
        fallback = self.archive("old.jar", {legacy: Image.new("RGBA", (16, 16), "red")})
        tex = self.texture_object(pack)
        tex.jars[str(fallback)] = zipfile.ZipFile(fallback)
        self.assertEqual(tex.load_image_texture((modern, legacy)).getpixel((0, 0)),
                         (0, 0, 255, 255))

    def test_missing_variants_raise(self):
        tex = self.texture_object(self.root / "absent")
        with self.assertRaises(textures.TextureException):
            tex.load_image(("example:first.png", "example:second.png"))

    def test_modern_sign_atlas_uses_new_uvs(self):
        pixels = numpy.zeros((32, 32, 4), dtype=numpy.uint8)
        pixels[:, :, 0] = numpy.arange(32)
        pixels[:, :, 1] = numpy.arange(32)[:, None]
        pixels[:, :, 3] = 255
        image = Image.fromarray(pixels, "RGBA")
        pack = self.archive("signs.zip", {
            textures.BLOCKTEXTURE + "oak_hanging_sign.png": image,
            textures.BLOCKTEXTURE + "bamboo_sign.png": image,
        })
        tex = self.texture_object(pack)
        hanging = tex.load_sign_texture("oak", hanging=True)
        self.assertEqual(hanging.getpixel((2, 14)), image.getpixel((2, 14)))
        self.assertEqual(hanging.getpixel((4, 0)), image.getpixel((4, 0)))
        self.assertEqual(hanging.getpixel((22, 7)), image.getpixel((22, 7)))
        self.assertEqual(tex.load_sign_texture("bamboo").getpixel((2, 2)),
                         image.getpixel((2, 2)))

    def test_legacy_sign_atlas_is_converted_to_modern_layout(self):
        image = Image.new("RGBA", (64, 32), "red")
        pack = self.archive("old-sign.zip", {
            "assets/minecraft/textures/entity/signs/hanging/oak.png": image,
        })
        tex = self.texture_object(pack)
        converted = tex.load_sign_texture("oak", hanging=True)
        self.assertEqual(converted.size, (32, 32))
        self.assertEqual(converted.getpixel((2, 16)), (255, 0, 0, 255))

    def test_modern_beds_render_without_entity_atlas(self):
        image = Image.new("RGBA", (16, 16), "red")
        images = {textures.BLOCKTEXTURE + name + ".png": image for name in (
            "white_bed_head_up", "white_bed_head_west", "white_bed_head_east",
            "bed_head_north", "white_bed_foot_up", "white_bed_foot_west",
            "white_bed_foot_east", "white_bed_foot_south",
        )}
        tex = self.texture_object(self.archive("beds.zip", images))
        for rotation in range(4):
            tex.rotation = rotation
            for data in range(16):
                with self.subTest(rotation=rotation, data=data):
                    result = textures.bed(tex, 26, data)
                    self.assertEqual(result.size, (24, 24))
                    self.assertIsNotNone(result.getchannel("A").getbbox())

    def test_legacy_beds_still_render(self):
        tex = self.texture_object(self.archive("legacy-bed.zip", {
            "assets/minecraft/textures/entity/bed/white.png":
                Image.new("RGBA", (64, 64), "red"),
        }))
        for data in range(16):
            self.assertIsNotNone(textures.bed(tex, 26, data).getchannel("A").getbbox())

    def test_modern_bed_legs_stay_at_outer_ends_in_all_directions(self):
        image = Image.new("RGBA", (16, 16), "red")
        images = {textures.BLOCKTEXTURE + name + ".png": image for name in (
            "white_bed_head_up", "white_bed_head_west", "white_bed_head_east",
            "bed_head_north", "white_bed_foot_up", "white_bed_foot_west",
            "white_bed_foot_east", "white_bed_foot_south",
        )}
        tex = self.texture_object(self.archive("bed-legs.zip", images))
        for head in (False, True):
            for direction in range(4):
                with self.subTest(head=head, direction=direction):
                    with patch.object(tex, "build_full_block") as build:
                        textures.bed(tex, 26, direction | (8 if head else 0))
                    long_side = build.call_args.args[3 if direction % 2 == 0 else 4]
                    at_left = head == (direction >= 2)
                    self.assertEqual(long_side.getpixel((0, 14))[3],
                                     255 if at_left else 0)
                    self.assertEqual(long_side.getpixel((15, 14))[3],
                                     0 if at_left else 255)
