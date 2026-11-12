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

# ---------------- references ----------------
refs=[]
for ln,line in enumerate(open(os.path.join(os.path.dirname(__file__),'refs.txt'),encoding='utf-8'),1):
    line=line.rstrip('\n')
    if not line.strip() or line.startswith('#'): continue
    f=line.split('|')
    if len(f)!=4: sys.exit(f'refs.txt:{ln}: expected 4 fields')
    refs.append({'key':f[0].strip(),'cite':f[1].strip(),'url':f[2].strip(),'note':f[3].strip()})
refkeys={r['key'] for r in refs}

# composition records: references + verification (from @ref/@ver in src files)
for path in sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'src_*.txt'))):
    pass  # handled in the main parser below (re-parse to attach)
def attach_comp_refs():
    byid={a['id']:a for a in alloys}
    for path in sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'src_*.txt'))):
        ref=[]; ver='std'
        for ln,line in enumerate(open(path,encoding='utf-8'),1):
            line=line.rstrip('\n')
            if line.startswith('@ref '): ref=line[5:].split(); continue
            if line.startswith('@ver '): ver=line[5:].strip(); continue
            if not line.strip() or line.startswith(('#','@')): continue
            aid=line.split('|')[0].strip()
            for k in ref:
                if k not in refkeys: sys.exit(f'{os.path.basename(path)}:{ln}: unknown ref {k}')
            byid[aid]['refs']=list(ref); byid[aid]['ver']=ver
attach_comp_refs()

# ASTM E140 Table 1 (non-austenitic steels): HRC -> (HV, HB 3000 kgf, tensile ksi)  [e140]
E140=[(20,238,226,110),(21,243,231,112),(22,248,237,115),(23,254,243,117),(24,260,247,119),(25,266,253,123),(26,272,258,125),
(27,279,264,128),(28,286,271,131),(29,294,279,135),(30,302,286,138),(31,310,294,141),(32,318,301,146),(33,327,311,149),
(34,336,319,152),(35,345,327,156),(36,354,336,161),(37,363,344,166),(38,372,353,171),(39,382,362,177),(40,392,371,182),
(41,402,381,188),(42,412,390,195),(43,423,400,201),(44,434,409,208),(45,446,421,215),(46,458,432,221),(47,471,443,229),
(48,484,455,237),(49,498,469,246),(50,513,481,255),(51,528,496,264),(52,544,512,273),(53,560,525,283),(54,577,543,292),
(55,595,560,301),(56,613,577,313),(57,633,595,325),(58,653,615,338),(59,674,634,351),(60,697,654,None)]
def interp(x, xs, ys):
    for i in range(len(xs)-1):
        if xs[i] <= x <= xs[i+1]:
            return ys[i] + (x-xs[i])/(xs[i+1]-xs[i])*(ys[i+1]-ys[i])
    raise ValueError(f'{x} outside E140 table range')
def hrc_to_hb(h): return interp(h,[r[0] for r in E140],[r[2] for r in E140])
def uts_to_hb(mpa):
    rows=[r for r in E140 if r[3]]; ts=[r[3]*6.894757 for r in rows]
    return interp(mpa, ts, [r[2] for r in rows])

# ---------------- mechanical-property database ----------------
props, proxy = [], {}
ids_all = {a['id'] for a in alloys}
pp = os.path.join(os.path.dirname(__file__), 'props_src.txt')
ref=[]; ver='unverified'
def hard(tok, uts=None, fam=''):
    tok=tok.strip()
    if tok.startswith('HB'): return float(tok[2:]), None
    if tok.startswith('HRC'):
        h=float(tok[3:]); hb=round(hrc_to_hb(h))
        note=f'{h:g} HRC → {hb} HB, ASTM E140 Table 1 (non-austenitic steels), linear interpolation'
        if fam and not fam.endswith('steel'): note += '; E140 Table 1 is for steels — approximate for this alloy family'
        return hb, note
    if tok=='UTS':
        hb=round(uts_to_hb(uts)); return hb, f'HB estimated from UTS {uts:g} MPa via ASTM E140 Table 1 tensile column (inverse interpolation)'
    raise ValueError(f'bad hardness {tok!r}')
for ln, line in enumerate(open(pp, encoding='utf-8'), 1):
    line = line.strip()
    if not line or line.startswith('#'): continue
    try:
        if line.startswith('@ref '): ref=line[5:].split(); [ (_ for _ in ()).throw(ValueError('unknown ref '+k)) for k in ref if k not in refkeys]; continue
        if line.startswith('@ver '): ver=line[5:].strip(); continue
        if line.startswith('@proxy'):
            _, f, u = line.split(); proxy[f] = u
            if f not in ids_all or u not in ids_all: raise ValueError('unknown id in proxy')
            continue
        f = [x.strip() for x in line.split('|')]
        if f[0] not in ids_all: raise ValueError(f'unknown alloy id {f[0]!r}')
        fam = next(a['fam'] for a in alloys if a['id']==f[0])
        e = {'id': f[0], 'cond': f[1], 'refs': list(ref), 'ver': ver}
        if f[2].startswith('curve'):
            pts = []; notes=[]
            for tok in f[2][5:].split(','):
                t, v = tok.strip().split(':'); u, y, el, hs = v.split('/')
                u,y,el=float(u),float(y),float(el); hb,note=hard(hs,u,fam)
                if note: notes.append(f'{t} °C: {note}')
                if y > u: raise ValueError(f'YS>UTS at {t}')
                pts.append([float(t), u, y, el, hb])
            pts.sort(); e['curve'] = pts
            if notes: e['hbnote']='; '.join(notes)
            e['cost'], e['avail'] = float(f[3]), f[4]
        else:
            u, y, el = map(float, f[2:5]); hb, note = hard(f[5], u, fam)
            if y > u: raise ValueError('YS>UTS')
            e.update(uts=u, ys=y, el=el, hb=hb, cost=float(f[6]), avail=f[7])
            if note: e['hbnote']=note
        if e['avail'] not in ('stock', 'specialty', 'import'): raise ValueError('bad avail')
        props.append(e)
    except Exception as ex:
        sys.exit(f'props_src.txt:{ln}: {ex}\n  {line}')
json.dump({'props': props, 'proxy': proxy, 'refs': refs}, open(os.path.join(os.path.dirname(__file__), 'props.json'), 'w'), separators=(',', ':'))
print(len(props), 'property records,', len({p["id"] for p in props}), 'grades,', sum(1 for p in props if 'curve' in p), 'tempering curves,',
      sum(1 for p in props if p['ver']=='web'), 'web-verified,', len(proxy), 'proxies,', len(refs), 'references')
print(sum(1 for a in alloys if a.get('ver')=='web'), 'composition records web-verified')
if '--inject' in sys.argv:
    page = sys.argv[sys.argv.index('--inject') + 1]
    html = open(page, encoding='utf-8').read()
    for name, val in (('ALLOYS', alloys), ('PROPDB', props), ('PROXY', proxy), ('REFS', refs)):
        marker = f'const {name} = '
        start = html.index(marker) + len(marker)
        end = html.index(';\nconst STEEL_FAMS', start) if name=='ALLOYS' else html.index(f'; // end {name}', start)
        html = html[:start] + json.dumps(val, separators=(',', ':'), ensure_ascii=False) + html[end:]
    open(page, 'w', encoding='utf-8').write(html)
    print('injected into', page)
