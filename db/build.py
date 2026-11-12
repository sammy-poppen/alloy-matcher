#!/usr/bin/env python3
"""Builds alloys.json from the compact source files in this folder.

Line format (fields separated by '|'):
  id | name | standard | aka | origin | use | limits
limits: 'C .28-.33; Mn .40-.60; P -.035; B .0005-'   (-x = max only, x- = min only)
Block headers set defaults for the lines that follow:
  @family Alloy steel
  @base Fe
  @defaults Si .15-.35; P -.035; S -.040
  @oth 0.05        (limit for unlisted elements, 'others each', non-ferrous)
  @conf published
"""
import json, re, sys, glob, os

SYMS = set("""H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi""".split())

def num(t):
    t = t.strip()
    return float(t) if t else None

def parse_limits(s):
    L = {}
    for tok in [t.strip() for t in s.split(';') if t.strip()]:
        m = re.match(r'^([A-Z][a-z]?)\s+(.*)$', tok)
        if not m: raise ValueError(f'bad token {tok!r}')
        el, rng = m.group(1), m.group(2).replace(' ', '')
        if el not in SYMS: raise ValueError(f'bad element {el!r}')
        if '-' not in rng:  # single value = max
            L[el] = [None, num(rng)]
        else:
            a, b = rng.split('-', 1)
            L[el] = [num(a), num(b)]
            if L[el][0] is not None and L[el][1] is not None and L[el][0] > L[el][1]:
                raise ValueError(f'min>max {tok!r}')
    return L

alloys, ids = [], set()
for path in sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'src_*.txt'))):
    st = {'family': '', 'base': 'Fe', 'defaults': {}, 'oth': None, 'conf': 'published'}
    for ln, line in enumerate(open(path, encoding='utf-8'), 1):
        line = line.rstrip('\n')
        if not line.strip() or line.lstrip().startswith('#'): continue
        try:
            if line.startswith('@'):
                k, _, v = line[1:].partition(' ')
                v = v.strip()
                if k == 'defaults': st['defaults'] = parse_limits(v) if v else {}
                elif k == 'oth': st['oth'] = float(v) if v else None
                else: st[k] = v
                continue
            f = [x.strip() for x in line.split('|')]
            if len(f) != 7: raise ValueError(f'expected 7 fields, got {len(f)}')
            aid, name, std, aka, origin, use, lim = f
            L = dict(st['defaults']); L.update(parse_limits(lim))
            # a 'none' value removes a default: written as 'X x' -> skip; not used
            if aid in ids: raise ValueError(f'duplicate id {aid}')
            ids.add(aid)
            a = {'id': aid, 'name': name, 'std': std, 'aka': aka, 'origin': origin, 'use': use,
                 'fam': st['family'], 'base': st['base'], 'conf': st['conf'], 'L': L}
            if st['oth'] is not None: a['oth'] = st['oth']
            alloys.append(a)
        except Exception as e:
            sys.exit(f'{os.path.basename(path)}:{ln}: {e}\n  {line}')

out = os.path.join(os.path.dirname(__file__), 'alloys.json')
json.dump(alloys, open(out, 'w'), separators=(',', ':'))
from collections import Counter
print(len(alloys), 'alloys')
for k, v in Counter(a['fam'] for a in alloys).most_common(): print(f'  {v:4d}  {k}')

# Optional: write the database into index.html (python3 db/build.py --inject index.html)
if '--inject' in sys.argv:
    page = sys.argv[sys.argv.index('--inject') + 1]
    html = open(page, encoding='utf-8').read()
    start = html.index('const ALLOYS = ') + len('const ALLOYS = ')
    end = html.index(';\nconst STEEL_FAMS', start)
    html = html[:start] + json.dumps(alloys, separators=(',', ':')) + html[end:]
    open(page, 'w', encoding='utf-8').write(html)
    print('injected into', page)

# ---------------- mechanical-property database ----------------
props, proxy = [], {}
ids_all = {a['id'] for a in alloys}
pp = os.path.join(os.path.dirname(__file__), 'props_src.txt')
for ln, line in enumerate(open(pp, encoding='utf-8'), 1):
    line = line.strip()
    if not line or line.startswith('#'): continue
    try:
        if line.startswith('@proxy'):
            _, f, u = line.split(); proxy[f] = u
            if f not in ids_all or u not in ids_all: raise ValueError('unknown id in proxy')
            continue
        f = [x.strip() for x in line.split('|')]
        if f[0] not in ids_all: raise ValueError(f'unknown alloy id {f[0]!r}')
        e = {'id': f[0], 'cond': f[1]}
        if f[2].startswith('curve'):
            pts = []
            for tok in f[2][5:].split(','):
                t, v = tok.strip().split(':'); u, y, el, hb = map(float, v.split('/'))
                if y > u: raise ValueError(f'YS>UTS at {t}')
                pts.append([float(t), u, y, el, hb])
            pts.sort(); e['curve'] = pts
            e['cost'], e['avail'], e['src'] = float(f[3]), f[4], f[5]
        else:
            u, y, el, hb = map(float, f[2:6])
            if y > u: raise ValueError('YS>UTS')
            e.update(uts=u, ys=y, el=el, hb=hb, cost=float(f[6]), avail=f[7], src=f[8])
        if e['avail'] not in ('stock', 'specialty', 'import'): raise ValueError('bad avail')
        props.append(e)
    except Exception as ex:
        sys.exit(f'props_src.txt:{ln}: {ex}\n  {line}')
json.dump({'props': props, 'proxy': proxy}, open(os.path.join(os.path.dirname(__file__), 'props.json'), 'w'), separators=(',', ':'))
print(len(props), 'property records,', len({p["id"] for p in props}), 'grades,', sum(1 for p in props if 'curve' in p), 'tempering curves,', len(proxy), 'proxies')
if '--inject' in sys.argv:
    page = sys.argv[sys.argv.index('--inject') + 1]
    html = open(page, encoding='utf-8').read()
    for name, val in (('PROPDB', props), ('PROXY', proxy)):
        start = html.index(f'const {name} = ') + len(f'const {name} = ')
        end = html.index(f'; // end {name}', start)
        html = html[:start] + json.dumps(val, separators=(',', ':')) + html[end:]
    open(page, 'w', encoding='utf-8').write(html)
    print('injected properties into', page)
