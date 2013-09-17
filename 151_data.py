#!/usr/bin/python
import sys

import pokerom
from biglist import indices, encounter_pcts

def print_maps(maps):
    for m in maps:
        for sm in m['info']:
            if sm['wild-pkmn']:
                print "Submap ID %d" % sm['id']
                if 'grass' in sm['wild-pkmn']:
                    print "Grass rate %d:" % sm['wild-pkmn']['grass-rate']
                    for i, (level, index) in enumerate(sm['wild-pkmn']['grass']):
                        print "%2d%% L%d %s" % (encounter_pcts[i], level, indices[index])
                if 'water' in sm['wild-pkmn']:
                    print "Water rate %d:" % sm['wild-pkmn']['water-rate']
                    for i, (level, index) in enumerate(sm['wild-pkmn']['water']):
                        print "%2d%% L%d %s" % (encounter_pcts[i], level, indices[index])
                print

def main(rom):
    maps = rom.get_maps()
    print_maps(maps)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s romfile" % sys.argv[0]
    main(pokerom.ROM(sys.argv[1]))
