#!/usr/bin/python

import os
import os.path
try:
    import simplejson as json
except ImportError:
    import json
import sys

import pokerom

try:
    from PIL import Image
except ImportError:
    print >>sys.stderr, "PIL not loaded, not writing images"
    Image = None
from StringIO import StringIO

def ppm_string(width, height, data):
    return "P6\n%d %d\n255\n%s" % (width, height, data)

def write_ppm(outfile, width, height, data):
    with open(outfile, "w") as f:
        f.write(ppm_string(width, height, data))

def write_map_ppm(outfile, map_data):
    write_ppm(outfile, 32*map_data['map_w'], 32*map_data['map_h'], map_data['map_pic'])

def write_map_png(outfile, map_data):
    if Image is None:
        return
    im = Image.open(StringIO(ppm_string(32*map_data['map_w'], 32*map_data['map_h'], map_data['map_pic'])))
    im.save(outfile)

def object_description(object_data):
    if object_data.get('bank') == 29 and object_data.get('faddr') == 26248:
        # Hidden Items
        return object_data['item_name']
    elif 'item_name' in object_data:
        # Nonhidden items, but also triggers on PCs and such
        return object_data['item_name']
    elif 'text' in object_data:
        # Signs
        return object_data['text']
    elif 'to_map' in object_data:
        # Warps, don't display anything
        return ""
    elif 'trainer_name' in object_data:
        # Trainers
        return "%s<br/>\nOffset: 0x%X" % (object_data['trainer_name'], object_data['trainer_offset'])
    else:
        # This includes things like other NPCs and the pokemon on the overworld
        return "Not a trainer or item"

def object_string(location, object_data):
    popup_text = object_description(object_data)
    if not popup_text:
        return ""
    else:
        return """
<div class="object" style="position:absolute; top:%(obj_y)dpx; left:%(obj_x)dpx; width:%(obj_w)dpx; height:%(obj_h)dpx">
<div class="popup triangle-border">
%(text)s
</div>
</div>""" % {
        'text': popup_text,
        'obj_x': 16*location[0],
        'obj_y': 16*location[1],
        'obj_w': 16,
        'obj_h': 16,
    }

def map_string(map_data):
    map_image_file = 'out/map%d.png' % map_data['id']

    write_map_png(map_image_file, map_data)

    object_data = "\n".join(object_string(loc, data) for loc, data in map_data['objects'].iteritems())
    return """
<div id="map%(id)dimg" style="background: url(%(img)s); width:%(img_w)dpx; height:%(img_h)dpx; position:relative;">
%(objects)s
</div>
""" % {'id': map_data['id'],
       'img': "file://%s" % os.path.abspath(map_image_file),
       'img_w': 32*map_data['map_w'],
       'img_h': 32*map_data['map_h'],
       'objects': object_data}

def compute_warps(maps):
    maps_by_id = {}
    submaps_by_id = {}
    overworld_maps = set()
    for m in maps:
        maps_by_id[m['id']] = m
        m['warps'] = []
        for submap in m['info']:
            submap['main_map'] = m
            submaps_by_id[submap['id']] = submap
    visited_maps = set()
    def walk(submap, last_overworld_map):
        visited_maps.add(submap['id'])
        if submap['main_map']['id'] == 1:
            last_overworld_map = submap['id']
        for idx, w in enumerate(submap['warps']):
            w_dict = {
                'x': w['x'] + submap['map_x'],
                'y': w['y'] + submap['map_y'],
                'on_submap': submap['id'],
                'warp_index': idx,
                'to_submap': w['to_map'],
                'to_warp': w['to_point'],
                }
            if w['to_map'] in submaps_by_id:
                w_dict['computed_to_submap'] = w['to_map']
            else:
                w_dict['computed_to_submap'] = last_overworld_map
            w_dict['to_map'] = submaps_by_id[w_dict['computed_to_submap']]['main_map']['id']
            to_submap = submaps_by_id[w_dict['computed_to_submap']]
            try:
                to_warp = to_submap['warps'][w['to_point']]
                w_dict['to_x'] = to_warp['x'] + to_submap['map_x']
                w_dict['to_y'] = to_warp['y'] + to_submap['map_y']
            except IndexError:
                w_dict['to_x'] = 0
                w_dict['to_y'] = 0
            submap['main_map']['warps'].append(w_dict)
            if w['to_map'] in submaps_by_id and w['to_map'] not in visited_maps:
                walk(submaps_by_id[w['to_map']], last_overworld_map)
        for c in submap['connections']:
            if c['index'] not in visited_maps:
                walk(submaps_by_id[c['index']], last_overworld_map)

    walk(submaps_by_id[0], 0)

def write_map_json(map_data):
    map_json_file = 'out/json/%d.json' % map_data['id']

    map_dict = {}
    map_dict['warps'] = []
    map_dict['objects'] = []
    map_dict['map_img'] = '/static/images/rb/map%d.png' % map_data['id']
    map_dict['map_px_w'] = 32*map_data['map_w']
    map_dict['map_px_h'] = 32*map_data['map_h']

    if map_data['id'] == 1:
        # Special case for overworld minimap
        map_dict['minimap_img'] = '/static/images/rb/map1_small.png'
        map_dict['minimap_w'] = 200
        map_dict['minimap_h'] = 212

    for loc, o in map_data['objects'].iteritems():
        o_data = {
            'px_x': 16*loc[0],
            'px_y': 16*loc[1],
            'px_w': 16,
            'px_h': 16,
            'description': object_description(o)
            }
        map_dict['objects'].append(o_data)

    for w in map_data['warps']:
        w_data = {
            'x': w['x'],
            'y': w['y'],
            'to_map': w['to_map'],
            'to_x': w['to_x'],
            'to_y': w['to_y'],
            'index': 'submap %d warp %d' % (w['on_submap'], w['warp_index']),
            'to_submap': w['to_submap'],
            'to_index': w['to_warp'],
            'description': 'On submap %d index %d<br/>To submap %d index %d' % (w['on_submap'], w['warp_index'], w['computed_to_submap'], w['to_warp']),
            }
        map_dict['warps'].append(w_data)

    with open(map_json_file, 'w') as f:
        f.write(json.dumps(map_dict))

def write_map_page(map_data):
    map_html_file = 'out/map%d.html' % map_data['id']

    map_str = map_string(map_data)

    page_data = """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<style media="screen" type="text/css">
.popup {
    position:absolute;
    width: 150px;
    bottom: -20px;
    left:-53px;
    background: white;
    text-align: center;
}
.triangle-border {
    padding:5px;
    margin: 1em 0 3em;
    color:#000;
    -moz-border-radius: 10px;
    -webkit-border-radius: 10px;
    border-radius: 10px;
    border: 1px solid black;
}
.triangle-border:before {
    content:"";
    position:absolute;
    bottom:-14px;
    left:46px;
    border-width:14px 14px 0;
    border-style:solid;
    border-color:black transparent;
    display:block;
    width:0;
}
.triangle-border:after {
    content:"";
    position:absolute;
    bottom:-13px;
    left:47px;
    border-width:13px 13px 0;
    border-style:solid;
    border-color:white transparent;
    display:block;
    width:0;
}
.object .popup {
    display: none;
}
.object:hover .popup {
    display: block;
}
</style>
</head>
<body>
%(map_str)s
</body>
</html>
""" % {'map_str': map_str}

    with open(map_html_file, "w") as f:
        f.write(page_data)

def main():
    if len(sys.argv) != 2:
        print('Usage: %s file' % sys.argv[0])
        return

    if not os.path.isdir('out/'):
        if os.path.exists('out/'):
            print 'Output directory location taken!'
            return
        os.mkdir('out/')

    if not os.path.isdir('out/json/'):
        if os.path.exists('out/json/'):
            print 'JSON output directory location taken!'
            return
        os.mkdir('out/json')

    rom = pokerom.ROM(sys.argv[1])

    maps = rom.get_maps()
    compute_warps(maps)
    write_map_ppm('out/overworld.ppm', maps[0])
    write_map_png('out/overworld.png', maps[0])

    for m in maps:
        write_map_page(m)
        write_map_json(m)

if __name__ == '__main__':
    main()
