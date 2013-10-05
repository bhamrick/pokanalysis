#!/usr/bin/python
import pokerom
import stats
import sys

def find_magic(goal, dv, base, min_level):
    ret = []
    if min_level <= 100:
        max_level = 100
    else:
        max_level = 255
    for ncalcium in range(11):
        for level in range(min_level, max_level + 1):
            spc = stats.stat_value(dv, base, ncalcium*2560, level)
            if spc == goal:
                ret.append((ncalcium, level))
    return ret

def main(goal, species, min_level):
    rom = pokerom.ROM('pokered.gbc')
    stats.init_data(rom.get_pokedex())
    try:
        base = stats.base_stats[species]['SPC']
    except KeyError:
        print "Unknown species: %s" % species
        return 1
    for dv in range(16):
        print "%2d   %s" % (dv, find_magic(goal, dv, base, min_level))
    return 0

if __name__ == '__main__':
    try:
        goal = int(sys.argv[1])
        species = sys.argv[2].upper()
        level = int(sys.argv[3])
        exit(main(goal, species, level))
    except (ValueError, IndexError):
        print "Usage: %s goal species level" % sys.argv[0]
