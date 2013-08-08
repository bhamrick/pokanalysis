#!/usr/bin/python

import os
import os.path
import simplejson as json
import sys

import pokerom

from PIL import Image
from StringIO import StringIO

def ppm_string(width, height, data):
    return "P6\n%d %d\n255\n%s" % (width, height, data)

def write_ppm(outfile, width, height, data):
    with open(outfile, "w") as f:
        f.write(ppm_string(width, height, data))

def write_map_ppm(outfile, map_data):
    write_ppm(outfile, 32*map_data['map_w'], 32*map_data['map_h'], map_data['map_pic'])

def write_map_png(outfile, map_data):
    im = Image.open(StringIO(ppm_string(32*map_data['map_w'], 32*map_data['map_h'], map_data['map_pic'])))
    im.save(outfile)

def object_description(object_data):
    if object_data.get('bank') == 29 and object_data.get('faddr') == 26248:
        # Items
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
        'obj_x': 16*location[0]+8,
        'obj_y': 16*location[1]+8,
        'obj_w': 16,
        'obj_h': 16,
    }

def map_string(map_data):
    map_image_file = 'out/map%d.png' % map_data['id']

    write_map_png(map_image_file, map_data)

    object_data = "\n".join(object_string(loc, data) for loc, data in map_data['objects'].iteritems())
    return """
<div id="map%(id)dimg" style="background: url(%(img)s); width:%(img_w)dpx; height:%(img_h)dpx;">
%(objects)s
</div>
""" % {'id': map_data['id'],
       'img': "file://%s" % os.path.abspath(map_image_file),
       'img_w': 32*map_data['map_w'],
       'img_h': 32*map_data['map_h'],
       'objects': object_data}

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
        os.mkdir(OUTPUT_DIRECTORY)

    rom = pokerom.ROM(sys.argv[1])

    maps = rom.get_maps()
    write_map_ppm('out/overworld.ppm', maps[0])
    write_map_png('out/overworld.png', maps[0])

    for m in maps:
        write_map_page(m)

if __name__ == '__main__':
    main()
