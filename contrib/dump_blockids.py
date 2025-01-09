#!/usr/bin/env python3
"""
Outputs a list of all allocated block IDs and which namespaced block names are associated with them.

All blocks which share a (block id, data id) tuple will sit in the same array. Different data IDs go onto different
lines. There should be no unrelated blocks (from a rendering perspective) on the same line.
"""

from collections import OrderedDict
from overviewer_core import world


# noinspection PyProtectedMember
def main():
    w = world.RegionSet('.', '.')
    dataset = OrderedDict()

    for mc_id in w._blockmap:
        block_id = w._blockmap[mc_id][0]
        block_data = w._blockmap[mc_id][1]

        if block_id not in dataset:
            dataset[block_id] = OrderedDict()

        if block_data not in dataset[block_id]:
            dataset[block_id][block_data] = []

        dataset[block_id][block_data].append(mc_id)

        pass

    print("# All Overviewer block IDs to Minecraft namespaced block IDs")
    print("```")
    last = -1
    in_wall_section = False
    for block_id in OrderedDict(sorted(dataset.items())):
        if (last + 1) < block_id:
            print("\n-- unallocated space --\n")  # empty line to show a gap in numbering
        last = block_id

        if 1792 <= block_id <= 2047 and not in_wall_section:
            in_wall_section = True
            print('-=-=-=-=- Entering wall section -=-=-=-=-\n')
        if block_id >= 2048 and in_wall_section:
            in_wall_section = False
            print('-=-=-=-=- Leaving wall section -=-=-=-=-\n')

        item_set = [x[1] for x in dataset[block_id].items()]

        if len(item_set) == 1:
            print(("%d" % block_id).ljust(6), item_set[0])
        else:
            print(("%d" % block_id).ljust(6))
            for s in item_set:
                print("".ljust(6), s)

    print("```")
    print()
    print("# Data conflicts:")
    print("```")
    for block_id in dataset:
        for block_data in dataset[block_id]:
            if len(dataset[block_id][block_data]) > 1:
                print("(%d, %d)" % (block_id, block_data), dataset[block_id][block_data])

    print("```")


if __name__ == '__main__':
    main()
