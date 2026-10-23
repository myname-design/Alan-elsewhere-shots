import re, sys
html = open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/cam.html').read()
skip = ('Skyline','TOP','New Live','City Views','Beaches','Landscapes',
        'Marinas','Unesco','Ski','Animals','Volcanoes','Lakes','From the')
seen = set()
for m in re.finditer(r'alt="([^"]+)"', html):
    a = m.group(1)
    if not a or a.startswith(skip):
        continue
    tail = html[m.end():m.end()+2500]
    mm = re.search(r'live(\d+)', tail)
    if mm and mm.group(1) not in seen:
        seen.add(mm.group(1))
        print(mm.group(1), a)
