/*
 * This file is part of the Minecraft Overviewer.
 *
 * Minecraft Overviewer is free software: you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or (at
 * your option) any later version.
 *
 * Minecraft Overviewer is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
 * Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with the Overviewer.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "biomes.h"
#include "overlay.h"

typedef struct {
    /* inherits from overlay */
    RenderPrimitiveOverlay parent;

    void* biomes;
} RenderPrimitiveBiomes;

struct BiomeColor {
    uint8_t biome;
    uint8_t r, g, b;
};

static struct BiomeColor default_biomes[] = {
    {0, 0x00, 0x00, 0x00}, // The Void
    {1, 0x9A, 0xCD, 0x32}, // Plains
    {2, 0x93, 0xC5, 0x72}, // Sunflower Plains
    {3, 0xFF, 0xFF, 0xFF}, // Snowy Plains
    {4, 0x87, 0xCE, 0xEB}, // Ice Spikes
    {5, 0xFF, 0xBF, 0x00}, // Desert
    {6, 0xB4, 0xD7, 0xD6}, // Swamp
    {7, 0x80, 0x00, 0x20}, // Mangrove Swamp
    {8, 0x22, 0x8B, 0x22}, // Forest
    {9, 0x4C, 0x9A, 0x2A}, // Flower Forest
    {10, 0x50, 0xC8, 0x78}, // Birch Forest
    {11, 0x00, 0x64, 0x00}, // Dark Forest
    {12, 0x00, 0x9E, 0x60}, // Old Growth Birch Forest
    {13, 0x66, 0xCD, 0xAA}, // Old Growth Pine Taiga
    {14, 0x4F, 0x79, 0x42}, // Old Growth Spruce Taiga
    {15, 0x01, 0x79, 0x6F}, // Taiga
    {16, 0xD3, 0xD3, 0xD3}, // Snowy Taiga
    {17, 0xFF, 0x66, 0x00}, // Savanna
    {18, 0xFF, 0xDA, 0xB9}, // Savanna Plateau
    {19, 0xD2, 0xB4, 0x8C}, // Windswept Hills
    {20, 0xBE, 0xBE, 0xBE}, // Windswept Gravelly Hills
    {21, 0xB8, 0x73, 0x33}, // Windswept Forest
    {22, 0xFF, 0x7F, 0x50}, // Windswept Savanna
    {23, 0x7C, 0xFC, 0x00}, // Jungle
    {24, 0x7F, 0xFF, 0x00}, // Sparse Jungle
    {25, 0xAD, 0xFF, 0x2F}, // Bamboo Jungle
    {26, 0xDC, 0x14, 0x3C}, // Badlands
    {27, 0xB2, 0x22, 0x22}, // Eroded Badlands
    {28, 0xFA, 0x80, 0x72}, // Wooded Badlands
    {29, 0x32, 0xCD, 0x32}, // Meadow
    {30, 0xB0, 0xE0, 0xE6}, // Grove
    {31, 0xE0, 0xFF, 0xFF}, // Snowy Slopes
    {32, 0xAD, 0xD8, 0xE6}, // Frozen Peaks
    {33, 0xE6, 0xE6, 0xFA}, // Jagged Peaks
    {34, 0x36, 0x45, 0x4F}, // Stony Peaks
    {35, 0x00, 0x00, 0xFF}, // River
    {36, 0xA0, 0xA0, 0xFF}, // Frozen River
    {37, 0xFF, 0xFF, 0x00}, // Beach
    {38, 0xFF, 0xDB, 0x58}, // Snowy Beach
    {39, 0xDA, 0xA5, 0x20}, // Stony Shore
    {40, 0x00, 0xBF, 0xFF}, // Warm Ocean
    {41, 0x1E, 0x90, 0xFF}, // Lukewarm Ocean
    {42, 0x41, 0x69, 0xE1}, // Deep Lukewarm Ocean
    {43, 0x00, 0x00, 0xFF}, // Ocean
    {44, 0xA0, 0xA0, 0xFF}, // Deep Ocean
    {45, 0x00, 0x00, 0xCD}, // Cold Ocean
    {46, 0x00, 0x00, 0x8B}, // Deep Cold Ocean
    {47, 0x87, 0xCE, 0xFA}, // Frozen Ocean
    {48, 0x46, 0x82, 0xB4}, // Deep Frozen Ocean
    {49, 0xFF, 0x00, 0xFF}, // Mushroom Fields
    {50, 0xDA, 0xA5, 0x20}, // Dripstone Caves
    {51, 0xAD, 0xFF, 0x2F}, // Lush Caves
    {52, 0x00, 0x00, 0x8B}, // Deep Dark
    {53, 0xFF, 0x66, 0x00}, // Nether Wastes
    {54, 0x40, 0xE0, 0xD0}, // Warped Forest
    {55, 0xDC, 0x14, 0x3C}, // Crimson Forest
    {56, 0x46, 0x82, 0xB4}, // Soul Sand Valley
    {57, 0x80, 0x80, 0x80}, // Basalt Deltas
    {58, 0xFF, 0x00, 0xFF}, // The End
    {59, 0xFF, 0xBF, 0x00}, // End Highlands
    {60, 0xFF, 0xDA, 0xB9}, // End Midlands
    {61, 0x80, 0x80, 0x80}, // Small End Islands
    {62, 0xD3, 0xD3, 0xD3}, // End Barrens
    {63, 0xfb, 0xa7, 0xea}, // Cherry Grove
    {64, 0x8F, 0xBC, 0x8F}, // Pale Garden

    /* end of list marker */
    {255, 0, 0, 0}};

static void get_color(void* data, RenderState* state,
                      uint8_t* r, uint8_t* g, uint8_t* b, uint8_t* a) {
    uint8_t biome;
    int32_t x = state->x, z = state->z, y_max, y;
    RenderPrimitiveBiomes* self = (RenderPrimitiveBiomes*)data;
    struct BiomeColor* biomes = (struct BiomeColor*)(self->biomes);
    *a = 0;

    y_max = state->y + 1;
    for (y = state->chunky * -16; y <= y_max; y++) {
        int32_t i;
        biome = get_data(state, BIOMES, x, y, z);

        if (biome >= NUM_BIOMES) {
            biome = DEFAULT_BIOME;
        }

        for (i = 0; biomes[i].biome != 255; i++) {
            if (biomes[i].biome == biome) {
                *r = biomes[i].r;
                *g = biomes[i].g;
                *b = biomes[i].b;
                *a = self->parent.color->a;
                break;
            }
        }
    }
}

static bool
overlay_biomes_start(void* data, RenderState* state, PyObject* support) {
    PyObject* opt;
    RenderPrimitiveBiomes* self;
    uint8_t alpha_tmp = 0;

    /* first, chain up */
    bool ret = primitive_overlay.start(data, state, support);
    if (ret != false)
        return ret;

    /* now do custom initializations */
    self = (RenderPrimitiveBiomes*)data;

    // opt is a borrowed reference.  do not deref
    if (!render_mode_parse_option(support, "biomes", "O", &(opt)))
        return true;
    if (opt && opt != Py_None) {
        struct BiomeColor* biomes = NULL;
        Py_ssize_t biomes_size = 0, i;
        /* create custom biomes */

        if (!PyList_Check(opt)) {
            PyErr_SetString(PyExc_TypeError, "'biomes' must be a list");
            return true;
        }

        biomes_size = PyList_GET_SIZE(opt);
        biomes = self->biomes = calloc(biomes_size + 1, sizeof(struct BiomeColor));
        if (biomes == NULL) {
            return true;
        }

        for (i = 0; i < biomes_size; i++) {
            PyObject* biome = PyList_GET_ITEM(opt, i);
            char* tmpname = NULL;
            uint32_t j = 0;

            if (!PyArg_ParseTuple(biome, "s(bbb)", &tmpname, &(biomes[i].r), &(biomes[i].g), &(biomes[i].b))) {
                free(biomes);
                self->biomes = NULL;
                return true;
            }

            for (j = 0; j < NUM_BIOMES; j++) {
                if (strncmp(biome_table[j].name, tmpname, strlen(tmpname)) == 0) {
                    biomes[i].biome = j;
                    break;
                }
            }
        }

        //Because 0 is a valid biome, have to use 255 as the end of list marker instead. Fragile!
        biomes[biomes_size].biome = 255;

    } else {
        self->biomes = default_biomes;
    }

    if (!render_mode_parse_option(support, "alpha", "b", &(alpha_tmp))) {
        if (PyErr_Occurred()) {
            PyErr_Clear();
            alpha_tmp = 240;
        }

        self->parent.color->a = alpha_tmp;
    }
    /* setup custom color */
    self->parent.get_color = get_color;

    return false;
}

static void
overlay_biomes_finish(void* data, RenderState* state) {
    /* first free all *our* stuff */
    RenderPrimitiveBiomes* self = (RenderPrimitiveBiomes*)data;

    if (self->biomes && self->biomes != default_biomes) {
        free(self->biomes);
    }

    /* now, chain up */
    primitive_overlay.finish(data, state);
}

RenderPrimitiveInterface primitive_overlay_biomes = {
    "overlay-biomes",
    sizeof(RenderPrimitiveBiomes),
    overlay_biomes_start,
    overlay_biomes_finish,
    NULL,
    NULL,
    overlay_draw,
};
