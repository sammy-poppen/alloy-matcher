# Alloy Composition Matcher

A single-page browser tool that identifies an alloy from a measured chemical composition (wt%). It checks the input against a built-in database of **546 grades**.

| Family | Grades | Standards covered |
|---|---|---|
| Alloy steels | 182 | SAE J404 / ASTM A29, EN 10083/10084/10085/10089/10250, BS 970, AIR 9160, JIS G4053, GOST 4543, GB/T 3077, aerospace AMS grades, ASTM A182/A193 |
| Carbon steels | 89 | SAE J403 (10xx, 11xx, 12xx, 15xx), EN 10083-2/10087, JIS G4051, GOST 1050, ASTM A36/A105/A516 |
| Stainless steels | 60 | ASTM A240/A276/A564/A743 — austenitic, duplex, ferritic, martensitic, PH, cast |
| Aluminum | 85 | Aluminum Association wrought (1xxx–8xxx) and cast (2xx.0–8xx.0) |
| Copper alloys | 32 | UNS C1xxxx–C9xxxx: coppers, brasses, bronzes, Cu-Ni, BeCu |
| Nickel alloys | 30 | Inconel, Incoloy, Monel, Hastelloy, Waspaloy, René 41, Nimonic, Haynes, Invar, Kovar |
| Tool steels | 29 | ASTM A681/A600 — W, O, A, D, S, H, M, T, L, P |
| Titanium | 18 | ASTM B348 grades 1–23, aerospace alpha/alpha-beta/beta alloys |
| Magnesium / Cobalt / Zinc | 21 | ASTM B90/B93/B107, Stellite, L-605, MP35N, Zamak, ZA |

Cast irons and precious metals are not included.

## How it works

1. Enter each element symbol and its measured wt%, one per row. Use **+ Add element** for more rows and **×** to remove one. Symbols are case-insensitive (`cr` → `Cr`). Values like `<0.01` are accepted, and rows with a blank wt% are skipped. **Clear all** empties every row.
   - **Remainder:** tick *Final element is the remainder (balance)*, or type `rem` / `bal` in any wt% box, to make that element the balance. Its value is computed as 100 − the sum of the other entries. It passes if it matches the grade's base metal (Fe, Al, Ti, Ni, Co, Cu, Zn or Mg). A different balance element is a decisive mismatch, unless the grade gives a range for it, in which case the computed value is checked against that range.
   - **Search in:** limit the search to one family, or search all of them.
2. Each grade is checked element by element:
   - **Specified elements** must fall within the grade's min/max.
   - **Unspecified elements:** carbon and alloy steels use residual limits (option), and aluminum and titanium use the "others, each" limit. For any other grade, an unspecified element above 0.5 wt% rules that grade out.
   - **Required elements not entered:** if a grade has a minimum for an element you didn't enter (for example Ti in 316Ti), it shows as "not measured" and ranks below grades that are fully confirmed.
3. Ranking order: wrong base metal → number of out-of-range elements → number of required elements not measured → total normalized deviation → specificity (more elements specified and narrower ranges first).
4. The top result is the identified alloy, followed by the next three closest grades. When several grades match fully (e.g. 316L and 316, or 7075 and 7175), they are all listed and the message says so. The full ranking table shows the top 50 and can show every grade.

### Options
- **Residual limits** (carbon/alloy steels): Ni ≤ 0.25, Cr ≤ 0.20, Mo ≤ 0.06, Cu ≤ 0.35, V ≤ 0.05.
- **Product analysis tolerances:** widens each limit by approximate ASTM A29 check-analysis tolerances.

## US-available alternatives

The search scores every US-standard grade and condition in the property database: 178 records from 146 grades, including 25 tempering curves, 14 of them web-verified. Foreign grades are used only as targets.

**Total equivalence (0–100%)** is a weighted average of sub-scores, each between 0 and 1:

| Criterion | Base weight | Sub-score |
|---|---|---|
| UTS | 0.30 | see strength scoring below |
| Yield | 0.25 | see strength scoring below |
| Hardness (HB) | 0.15 | see strength scoring below |
| Elongation | 0.10 | min(1, candidate / target), one-sided |
| Hardenability, D<sub>I</sub> (carbon/alloy steels only) | 0.10 | min(1, D<sub>I</sub> candidate / D<sub>I</sub> target), one-sided |
| Cost (optional) | 0.10 | min(1, reference cost / candidate cost), one-sided |

Criteria that don't apply are removed, and the remaining weights are rescaled to sum to 1.

**Strength scoring** applies to UTS, yield and hardness, with r = candidate / target:
- **Minimum (default):** r = 1.00–1.15 scores 1. Below target the score is 1 − 2(1 − r), and the candidate is flagged ▼ below target. Above 1.15 it is 1 − 0.5(r − 1.15).
- **Closest match:** the score is 1 − |r − 1|.

**Hardenability** is the ASTM A255 / Grossmann ideal critical diameter D<sub>I</sub> (inches, grain size 7), calculated from chemistry. It is the alloy's capacity for depth of hardening, not a measured hardening depth for the part. Elements above the A255 calculation range are capped and flagged.

**Hardness conversions** use ASTM E140 Table 1 (non-austenitic steels) with linear interpolation. Each record stores its published hardness scale, and every converted value states the conversion it used.

**Tempering curves:** the search scans 5 °C steps between published points and interpolates linearly.

**Verification status:** every record carries reference numbers and one of three statuses: ✓ web-verified, ◇ standard (not re-checked), or ⚠ unverified. The option "Only web-verified property data" limits the search to verified records.

## Exporting a report (PDF / PNG)

Under the results, **Export report** has optional fields (part, lab/report number, prepared by, organization, notes) and two buttons:

- **Export PDF:** US Letter, multi-page, with a footer on every page showing the report number, identified alloy and page X of Y.
- **Export PNG image:** the same report as one tall image.

The report always uses a light, print-ready layout, even in dark mode. It contains:
1. Header fields, date, search scope and options.
2. Measured composition.
3. Identified alloy with its element-by-element checklist.
4. The next three closest grades with their checklists.
5. US alternatives: a summary table plus the full calculation for each.
6. Method, data sources and limitations.

Exports use [html2canvas](https://html2canvas.hertzen.com/) and [jsPDF](https://github.com/parallax/jsPDF), loaded from cdnjs, so the page needs an internet connection to export.

## Running it

No dependencies. Open `index.html` in a browser, or host it with GitHub Pages (Settings → Pages → deploy from the main branch). The database is embedded in `index.html`, so the page is a single self-contained file.

## Data caveats

- Composition limits come from published summaries of the governing standards. 31CrMo12 and 30NCD16 were checked against several datasheets; the other grades were not individually re-verified, and standards get revised. Confirm the governing specification before making a final determination.
- Some combined limits (e.g. Si+Fe in 1100 aluminum, Co+Ni in C17200, Ti ≥ 5×(C+N) in 321) are simplified to individual element limits.
- Mechanical properties are typical quenched-and-tempered values, not specification minimums. The cost index is a rough relative estimate (4140 = 1.00), not a quote.

## References

The bibliography is in `db/refs.txt` (IEEE style, with a link wherever a free or official web page exists). It is shown at the bottom of the page and printed in every PDF report. Composition and property records cite it with `@ref KEY` and `@ver web|std|unverified` lines.

## Editing the database

The database source is in `db/`, one text file per family (`src_01_carbon.txt` … `src_07_nonferrous.txt`). Each grade is one line:

```
id | name | standard | also known as | origin | use | limits
4140|AISI 4140|SAE J404 · UNS G41400|≈ 42CrMo4|US|Q&T general purpose|C .38-.43; Mn .75-1.00; Cr .80-1.10; Mo .15-.25
```

Limits: `C .28-.33` (range), `P -.035` (max only), `Ti .15-` (min only). Lines starting with `@` set defaults for the lines below them (`@family`, `@base`, `@defaults`, `@oth` for "others each", `@conf`).

After editing (composition files or `props_src.txt`), rebuild and write both databases into the page:

```
python3 db/build.py --inject index.html
```

The script checks for unknown element symbols, duplicate IDs and min > max, and stops with the line number if it finds one.
