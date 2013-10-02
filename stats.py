base_stats = {}

stat_names = ['ATK', 'DEF', 'SPD', 'SPC']

def prepare_name(name):
    return filter(lambda x: x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                  name.upper())

def init_data(pokedex):
    global base_stats
    for p in pokedex:
        if p['id'] == 29:
            name = 'NIDORANF'
        elif p['id'] == 32:
            name = 'NIDORANM'
        else:
            name = prepare_name(p['name'])
        stats_dict = p['stats']
        stats_dict['SPC'] = stats_dict['SPE']
        del stats_dict['SPE']
        base_stats[name] = stats_dict

# Not valid for HP stat
def stat_value(dv, base, ev, level):
    return ((dv + base + int(ev**0.5)//8) * level)//50 + 5

def trainer_stats(species, level):
    ret = {}
    for stat in stat_names:
        base = base_stats[species][stat]
        dv = 9 if stat == 'ATK' else 8
        ev = 0
        ret[stat] = stat_value(dv, base, ev, level)
    return ret
