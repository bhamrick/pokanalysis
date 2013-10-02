#!/usr/bin/python
import sys

import pokerom
from biglist import indices, encounter_pcts, get_submap_name
from stats import init_data, trainer_stats

def print_maps(maps, f=sys.stdout):
    for m in maps:
        for sm in m['info']:
            if sm['wild-pkmn']:
                f.write(get_submap_name(sm['id']) + '\n')
                if 'grass' in sm['wild-pkmn']:
                    f.write("Grass rate %d:\n" % sm['wild-pkmn']['grass-rate'])
                    for i, (level, index) in enumerate(sm['wild-pkmn']['grass']):
                        f.write("%2d%% L%d %s\n" % (encounter_pcts[i], level, indices[index]))
                if 'water' in sm['wild-pkmn']:
                    f.write("Water rate %d:\n" % sm['wild-pkmn']['water-rate'])
                    for i, (level, index) in enumerate(sm['wild-pkmn']['water']):
                        f.write("%2d%% L%d %s\n" % (encounter_pcts[i], level, indices[index]))
                f.write("\n")
    overworld = maps[0]
    for sm in overworld['info']:
        f.write("Overworld submap ID %d top left %d,%d\n" % (sm['id'], sm['map_x'], sm['map_y']))

def print_trainers(trainers, f=sys.stdout):
    for t in trainers:
        if 'team' not in t:
            continue
        team = t['team']
        f.write("%s 0x%X\n" % (t['name'], t['offset']))
        for (index, level) in team:
            pokemon_string = "L%d %s" % (level, indices[index])
            special = trainer_stats(indices[index], level)['SPC']
            if special in indices:
                pokemon_string += " " * (25 - len(pokemon_string)) + "| " + indices[special]
            f.write("%s\n" % pokemon_string)
        last_index, last_level = team[-1]
        last_special = trainer_stats(indices[last_index], last_level)['SPC']
        if last_special in indices:
            f.write("Trainer fly species: %s\n" % indices[last_special])
        f.write("\n")

def main(rom):
    init_data(rom.get_pokedex())
    maps = rom.get_maps()
    print_maps(maps)
    trainers = rom.get_trainers()
    print_trainers(trainers)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s romfile" % sys.argv[0]
    main(pokerom.ROM(sys.argv[1]))
