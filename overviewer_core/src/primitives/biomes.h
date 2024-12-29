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

#include <stdint.h>

#define DEFAULT_BIOME 8 /* forest, nice and green */

typedef struct {
    const char* name;

    float temperature;
    float rainfall;

    uint32_t r, g, b;
    uint32_t water_r, water_g, water_b;
} Biome;

/* each entry in this table is yanked *directly* out of the minecraft source
 * temp/rainfall are taken from what MCP calls setTemperatureRainfall
 *
 * Some biomes, like Swamp, do a bit of post-processing by multiplying on a
 * hard-coded color. The RGB tuple used follows the temp/rainfall.
 * 255, 255, 255 is white, which means do nothing
 *
 * keep in mind the x/y coordinate in the color tables is found *after*
 * multiplying rainfall and temperature for the second coordinate, *and* the
 * origin is in the lower-right. <3 biomes.
 *
 * REMEMBER: if you're updating this table, update the list in overlay-biomes.c too!
 */
static Biome biome_table[] = {
    /* 0 */
    {"The Void",                    0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"Plains",                      0.8,  0.4, 255, 255, 255,  64, 118, 228},
    {"Sunflower Plains",            0.8,  0.4, 255, 255, 255,  64, 118, 228},
    {"Snowy Plains",                0.0,  0.5, 255, 255, 255,  64, 118, 228},
    {"Ice Spikes",                  0.0,  0.5, 255, 255, 255,  64, 118, 228},
    /* 5 */
    {"Desert",                      2.0,  0.0, 255, 255, 255,  64, 118, 228},
    {"Swamp",                       0.8,  0.9, 205, 128, 255,  97, 123, 100},
    {"Mangrove Swamp",              0.8,  0.9, 205, 128, 255,  58, 122, 106},
    {"Forest",                      0.7,  0.8, 255, 255, 255,  64, 118, 228},
    {"Flower Forest",               0.7,  0.8, 255, 255, 255,  64, 118, 228},
    /* 10 */
    {"Birch Forest",                0.6,  0.6, 255, 255, 255,  64, 118, 228},
    {"Dark Forest",                 0.7,  0.8, 255, 255, 255,  64, 118, 228},
    {"Old Growth Birch Forest",     0.6,  0.6, 255, 255, 255,  64, 118, 228},
    {"Old Growth Pine Taiga",       0.3,  0.8, 255, 255, 255,  64, 118, 228},
    {"Old Growth Spruce Taiga",     0.25, 0.8, 255, 255, 255,  64, 118, 228},
    /* 15 */
    {"Taiga",                       0.25, 0.8, 255, 255, 255,  64, 118, 228},
    {"Snowy Taiga",                -0.5,  0.4, 255, 255, 255,  64, 118, 228},
    {"Savanna",                     1.2,  0.0, 255, 255,  25,  64, 118, 228},
    {"Savanna Plateau",             1.0,  0.0, 255, 255, 255,  64, 118, 228},
    {"Windswept Hills",             0.2,  0.3, 255, 255, 255,  64, 118, 228},
    /* 20 */
    {"Windswept Gravelly Hills",    0.2,  0.3, 255, 255, 255,  64, 118, 228},
    {"Windswept Forest",            0.2,  0.3, 255, 255, 255,  64, 118, 228},
    {"Windswept Savanna",           1.1,  0.0, 255, 255, 255,  64, 118, 228},
    {"Jungle",                      0.95, 0.9, 255, 255, 255,  64, 118, 228},
    {"Sparse Jungle",               0.95, 0.8, 255, 255, 255,  64, 118, 228},
    /* 25 */
    {"Bamboo Jungle",               0.95, 0.9, 255, 255, 255,  64, 118, 228},
    {"Badlands",                    2.0,  0.0, 144, 129,  77,  64, 118, 228},
    {"Eroded Badlands",             2.0,  0.0, 144, 129,  77,  64, 118, 228},
    {"Wooded Badlands",             2.0,  0.0, 144, 129,  77,  64, 118, 228},
    {"Meadow",                      0.5,  0.8, 255, 255, 255,  64, 118, 228},
    /* 30 */
    {"Grove",                      -0.2,  0.8, 255, 255, 255,  64, 118, 228},
    {"Snowy Slopes",               -0.3,  0.9, 255, 255, 255,  64, 118, 228},
    {"Frozen Peaks",               -0.7,  0.9, 255, 255, 255,  64, 118, 228},
    {"Jagged Peaks",               -0.7,  0.9, 255, 255, 255,  64, 118, 228},
    {"Stony Peaks",                 1.5,  0.3, 255, 255, 255,  64, 118, 228},
    /* 35 */
    {"River",                       0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"Frozen River",                0.0,  0.5, 255, 255, 255,  57,  56, 201},
    {"Beach",                       0.8,  0.4, 255, 255, 255,  64, 118, 228},
    {"Snowy Beach",                 0.05, 0.3, 255, 255, 255,  61,  87, 214},
    {"Stony Shore",                 0.2,  0.3, 255, 255, 255,  64, 118, 228},
    /* 40 */
    {"Warm Ocean",                  0.5,  0.5, 255, 255, 255,  67, 213, 238},
    {"Lukewarm Ocean",              0.5,  0.5, 255, 255, 255,  69, 173, 242},
    {"Deep Lukewarm Ocean",         0.5,  0.5, 255, 255, 255,  69, 173, 242},
    {"Ocean",                       0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"Deep Ocean",                  0.5,  0.5, 255, 255, 255,  64, 118, 228},
    /* 45 */
    {"Cold Ocean",                  0.5,  0.5, 255, 255, 255,  61,  87, 214},
    {"Deep Cold Ocean",             0.5,  0.5, 255, 255, 255,  61,  87, 214},
    {"Frozen Ocean",                0.0,  0.5, 255, 255, 255,  57,  56, 201},
    {"Deep Frozen Ocean",           0.5,  0.5, 255, 255, 255,  57,  56, 201},
    {"Mushroom Fields",             0.9,  1.0, 255, 255, 255,  64, 118, 228},
    /* 50 */
    {"Dripstone Caves",             0.8,  0.4, 255, 255, 255,  64, 118, 228},
    {"Lush Caves",                  0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"Deep Dark",                   0.8,  0.4, 255, 255, 255,  64, 118, 228},
    {"Nether Wastes",               2.0,  0.0, 255, 255, 255,  64, 118, 228},
    {"Warped Forest",               2.0,  0.0, 255, 255, 255,  64, 118, 228},
    /* 55 */
    {"Crimson Forest",              2.0,  0.0, 255, 255, 255,  64, 118, 228},
    {"Soul Sand Valley",            2.0,  0.0, 255, 255, 255,  64, 118, 228},
    {"Basalt Deltas",               2.0,  0.0, 255, 255, 255,  64, 118, 228},
    {"The End",                     0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"End Highlands",               0.5,  0.5, 255, 255, 255,  64, 118, 228},
    /* 60 */
    {"End Midlands",                0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"Small End Islands",           0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"End Barrens",                 0.5,  0.5, 255, 255, 255,  64, 118, 228},
    {"Cherry Grove",                0.5,  0.8, 353, 297, 225,  93, 183, 239},
    {"Pale Garden",                 0.7,  0.8, 119, 130, 114,  63, 118, 228},
    /* 65 */
};

#define NUM_BIOMES (sizeof(biome_table) / sizeof(Biome))
