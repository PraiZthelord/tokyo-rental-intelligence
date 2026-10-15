# Decisions log

A running record of choices I made, what else I considered, and why.

## 2026-10-10: Raw data
- File: tokyo.csv
- Rows: (count)
- Source: (where you downloaded it)
- Downloaded: (date)
- Licensing note: SUUMO-derived. Raw data and listing URLs are not published in this repo.

## 2026-10-10: Modeling choices (to confirm after the data audit)
- Target: asking rent excluding admin fee
- Deposit and key money: kept out of model features (they are multiples of rent, so they leak the target)
- Grouping key for CV: (to decide after checking the URL `jnc` / `bc` values)

# Audit
## 2026-10-10: Manual audit 1 (raw file, nothing cleaned yet)

### Shape and missing values
- Shape: 191,508 rows x 13 columns
- `isna()` reports zero nulls in every column. This is misleading: missing data is stored as the string `-`, which `isna()` cannot see.

### Missing-value token `-`
| Column | Rows with `-` | Share of rows | Provisional meaning |
|---|---|---|---|
| Administrative Costs | 35,100 | 18.3% | Probably "no admin fee" (なし) |
| Deposit | 55,734 | 29.1% | Probably "none", to verify |
| Gratuity (key money) | 73,168 | 38.2% | Probably "none", to verify |

- Decision (provisional): treat `-` as 0 / none, not as missing. Verify by checking whether `-` clusters in old buildings or areas far from stations, which would support "none" over "missing". [result: ...]
- Deposit and gratuity are excluded from model features (they are multiples of rent and would leak the target).

### Column vocabularies
- **Building Age:** max 77 years (appears once; check if real or outlier [result: ...]). `新築` (brand new) is the most common value: 30,059 rows (15.7%). Plan: `is_new` flag, with age handled separately from 築1年 and up.
- **Stories Tall:** most common is 2階建 (54,555 rows). Unusual format exists, e.g. `地下1地上38階建` (basement + above ground), which needs its own parsing rule. [count of basement patterns: ...]
- **Floor:** most common is 1階 (63,924 rows). Multi-floor units exist, e.g. `5-7階` and `1-2階`, which need min / max / is_multi_floor handling. [count: ...]
- **Rooms:** most common is 1K (76,095 rows). Suffix vocabulary seen: K, DK, LDK, SK, SLDK, ワンルーム. Rare values like 8K (1 row) need a floor-area plausibility check. [result: ...]

### Duplicates
- Exact duplicate rows (extra copies): 8,002 = 4.2% of the data (`df.duplicated().sum()`).
- Rows involved in any duplicate group, originals included: 13,632 (`df.duplicated(keep=False).sum()`). This implies about 5,630 distinct listings appear more than once.
- Note: an earlier note said 24%. That was a miscalculation. The correct figure is 4.2%.
### jnc non-exact duplicates
- ~19 rows share a listing ID (`jnc`) with different contents.
- Differing columns (pairs): Stations 8, Building Age 3, Title 3, Floor 2, Rooms 1, Square Meters 1.
- Rule: drop exact duplicates (8,002). For non-exact repeats, keep first if only Stations/Age/Title differ; exclude both rows if Floor, Rooms, or Area differ (conflicting records).
- Affected rows: [n kept], [n excluded]
- Note: Building Age differing across rows of one listing suggests listings may have been scraped on different dates, so the scrape date is not a single snapshot. Revisit before the 1981 threshold test.

### Listing identifiers (URL column)
- URL format: `.../jnc_<number>/?bc=<number>`
- `jnc` repeated values: 8,021. `bc` repeated values: 8,021. Both match each other and are close to the 8,002 exact-duplicate count.
- Conclusion: `jnc` and `bc` are both **listing IDs**, not building IDs. My earlier hypothesis that `jnc` was a building ID was wrong.
- About 19 rows share a listing ID but are not exact duplicates (20 rows flagged in the check). [what differs in these rows: ...]
- Decision: building key will be a **composite** of normalized title + municipality/town + stories + age, plus the station string for auto-generated titles. After building it, check the number of distinct keys and the largest group sizes. [result: ...]

### Listing titles
- Many titles are auto-generated in the form `<line> <station>駅 <N>階建 築<N>年`, which usually means an unnamed building. Named buildings (e.g. ルアナ) are the minority. [count of each: ...]
- The age and stories in the title appear to match the Building Age and Stories Tall columns. [verified on a sample of N rows: ...]

### Decisions made today
1. Never edit the raw file. All cleaning goes through code into `data/interim/`.
2. Deduplicate before any train / test split. Dedup rule: on listing ID (`jnc`), keep first occurrence. [pending what differs in the 19 non-exact repeats]
3. `-` in deposit / gratuity / admin treated as "none" provisionally.
4. Building key is composite, since no ID identifies a building.
5. Target is asking rent excluding admin fee.

### Open questions
- [ ] What differs in the ~19 rows that share a listing ID but are not exact copies?
    -
- [ ] Does `-` cluster in old / remote listings (supports "none" over "missing")?
- [ ] Is the 77-year-old building real?
- [ ] How many titles are auto-generated vs named?
- [ ] What is the scrape date? (needed to anchor building age and the 1981 test)


🏠 Japanese Apartment Layouts: Quick Guide


Layout Codes (What the letters mean)

• ワンルーム (1R): One single room. The kitchen is inside your bedroom.
• K (Kitchen): Studio room. The kitchen is in a separate tiny room.
• DK (Dining-Kitchen): The kitchen area is big enough for a small dining table.
• LDK (Living-Dining-Kitchen): A large, modern open-plan living room and kitchen combined.
• S (Service Room): A bonus room. It lacks enough window light to legally be called a bedroom, but you can use it as one. (e.g., SLDK = 1 Bedroom + 1 Service Room + Living/Dining/Kitchen).
Note: The number before the letters tells you how many private bedrooms you have (e.g., a 2LDK has 2 bedrooms plus the main living area).




## 2026-10-11: Manual Audit 2 

### Dedup applied (notebook: 02_cleaning)
| Step | Rule | Before | After | Removed |
|---|---|---|---|---|
| 1 | Drop exact duplicate rows | 191,508 | 183,506 | 8,002 |
| 2 | Exclude `jnc` groups with Floor/Rooms/Area conflicts | 183,506 | 183,496 | 10 |
| 3 | Keep first row per `jnc` | 183,496 | 183,490 | 6 |

- Final: 183,490 rows (4.2% removed overall), saved to `data/interim/listings_dedup.csv`.
- Step 2 removed 10 rows, not the 8 I expected from 4 conflict groups, so some groups had 3 copies. [confirm]
- Non-exact `jnc` repeats differed in: Stations, Building Age, Title, Floor, Rooms, Square Meters. Floor/Rooms/Area differences were treated as conflicting records.
- Building Age differs between rows of the same `jnc` in some groups, so the data was **not scraped on a single date**. Revisit before the 1981 threshold test.
- `jnc` and `bc` are both listing-level IDs. Not usable as building IDs.

### Yen parser (`parse_yen`)
- Handles `万円`, `円`, and `-` (returns None). Anything else returns "FAILED" so it is counted, not silently dropped.
- `round()` used after multiplying by 10,000 to avoid float errors (e.g. 5.45万 -> 54,500).
- Result: **0 failures** in Price, Administrative Costs, Deposit and Gratuity.

### Missing values (`-`) after dedup
| Column | `-` (None) | Share of 183,490 | Raw count before dedup |
|---|---|---|---|
| Price_yen | 0 | 0% | n/a |
| Administrative Costs_yen | 33,311 | 18.2% | 35,100 |
| Deposit_yen | 53,770 | 29.3% | 55,734 |
| Gratuity_yen | 70,493 | 38.4% | 73,168 |

- Price has no missing values, so every row has a target.
- Provisional: `-` means "none" for admin, deposit and gratuity. Test: [median rent / age for `-` vs non-`-` rows: result].

### describe() of parsed money columns
| | Price | Admin | Deposit | Gratuity |
|---|---|---|---|---|
| count | 183,490 | 150,179 | 129,720 | 112,997 |
| mean | 99,317 | 6,101 | 127,585 | 116,461 |
| min | 10,600 | 1 | 100 | 100 |
| median | 82,500 | 5,000 | 87,500 | 92,000 |
| max | 4,450,000 | 295,000 | 17,800,000 | 3,300,000 |

- Price is right-skewed (mean 99k vs median 82.5k). Plan: compare log(rent) with raw rent.

### Suspicious values (flagged, NOT removed yet)
- Admin min ¥1; deposit and gratuity min ¥100: not realistic fees. Count under ¥1,000: [n deposit], [n gratuity].
- Price max ¥4,450,000 (about 50x the median). Inspect: [what the row looks like].
- Deposit max ¥17.8M and 24 months of rent; gratuity max 10 months. Count above 3 months: [n deposit], [n gratuity]. Count below 0.1 months: [n], [n].

### Deposit and gratuity in months of rent
- The 25th to 75th percentile is about 1 month for both. Typical deposit and key money is one month of rent. [exact distribution from value_counts: ...]
- Confirms both are multiples of rent, so they stay out of the model features (target leakage).
- Note: the first describe() was misleading because a display format rounded values to whole numbers. Use unrounded values to read fractions like 0.5.

### Decisions today
1. Dedup rule above is final for now.
2. Money columns parsed; no rows removed for outliers yet. Outliers get `flag_` columns, and exclusion rules go in the cleaning table later with row counts.
3. Deposit and gratuity excluded from model features.

### Open questions
- [ ] Why admin = ¥1 and deposit/gratuity = ¥100? Look at those raw rows.
- [ ] What is the ¥4,450,000 listing?
- [ ] Does `-` in deposit/gratuity mean none (check rent and age of `-` rows)?
- [ ] Which `jnc` groups had 3 copies?



- Rows matching on all 12 visible columns (everything except listing ID and URL): 36,894 (20.1% of 183,490), counted with `keep=False`, so originals are included.
- Cannot tell identical units in one building apart from re-listings under a new ID. All kept, nothing dropped.
- Consequence: a random train/test split will likely be leaky, because twins can land on both sides. Use grouped CV on a building key, and compare random vs grouped scores (the gap is a planned finding).

**Group-size distribution** (groups of rows identical on all 12 visible columns, from `groupby(...).ngroup()`):

| Group size | Number of groups |
|---|---|
| 1 (no look-alike) | 146,596 |
| 2 | 11,530 |
| 3 | 2,131 |
| 4 | 775 |
| 5 | 293 |
| 6 | 164 |
| 7 | 80 |
| 8 | 27 |
| 9 | 36 |
| 10 | 17 |
| Largest group | 30 |

- Among look-alike groups, size 2 is the most common (11,530).
- The tail is small; the biggest group has 30 identical-looking listings.
- Open: inspect the group of 30 by eye (large complex with identical units, or a repeated posting?).

### Saved files
- `data/interim/listings_dedup.csv`: deduplicated only, no parsed columns (checkpoint).
- `data/interim/listings_parsed.csv`: deduplicated plus `_yen` columns and `lookalike_id`. Reload with `dtype={"jnc": str}`.
- Both are covered by `.gitignore`.




## 2026-10-11: Decisions

### Stories / property type
- `平屋`: 213 rows (0.12%)
- Parsed as `stories_above = 1`, `stories_below = 0`.
- The rent distribution for `平屋` is not clearly higher than the overall dataset: median ¥80,000, mean ¥96,704, range ¥39,000 to ¥350,000. This does not support the earlier assumption that houses would rent for more.
- Keep `is_hiraya` as a candidate feature, but only as a model feature to test in ablation; do not assume it helps.

### Floor parsing
- 997 rows (0.5%) are `-`, which is treated as a legitimate missing value rather than a parse failure.
- Basement floors are encoded as negative numbers: `B1階 -> -1`.
- Open-ended ranges like `1-階` are treated as multi-floor with `floor_max = floor_min` and flagged.
- Rare patterns `M9階` and `9B9階` are intentionally rejected as `FAILED` and then reviewed/flagged rather than silently coerced.
- Parser behavior confirmed on examples:
  - `"1階" -> (1, 1, 0)`
  - `"12階" -> (12, 12, 0)`
  - `"1-2階" -> (1, 2, 1)`
  - `"1-階" -> (1, 1, 1)`
  - `"B1階" -> (-1, -1, 0)`
  - `"B1-1階" -> (-1, 1, 1)`
  - `"-" -> (None, None, None)`
  - `"M1階"` and `"1B1階"` -> `FAILED`
- The floor parser passed the notebook tests with only 7 rows failing by design (`M2階` and `1B2階`), and the rest of the rows parsed successfully.
- `is_multi_floor` is now set on a subset of rows with range / multi-floor values; basement rows remain separate.

### Area parsing
- Built area parser: all rows parsed successfully; no failures.
- Distribution: count 183,490; mean 34.21 m²; median 26.90 m²; min 1.00 m²; max 562.63 m².
- The min and max are suspicious outliers and need a quick review, but they are not currently treated as parse errors.

### Building-age parsing
- Built building-age parser: no failures in the notebook test.
-- 新築 encoded as age_years = 0 plus is_new = 1 (domain decision: newly built, under about a year old). Not treated as continuous with 築1年; the flag lets the model learn any new-build premium.
- Check: median rent by age 0 vs 1: [result]
- 4 rows had `築99年以上` ("99 years or older"; the site caps the displayed age). Encoded as age_years=99, is_new=0, age_is_lower_bound=1. Parser and test updated.
- Building age parser: 0 failures on 183,490 rows. 新築 → age_years=0, is_new=1 (28,963 rows, 15.8%). 4 rows had `築99年以上` (site caps the displayed age); encoded as age_years=99, is_new=0, age_is_lower_bound=1. Test updated to reject `築14年abc` instead.

### Summary of notebook direction
- Deduplication and value parsing are now the source of truth for the cleaning pipeline.
- Parsing rules are intentionally conservative: unknown rare floor formats are flagged rather than silently misparsed.
- Model features remain constrained by leakage rules: deposits and gratuity stay out, and parsing is done in code rather than by editing raw source files.

## 2026-10-12: Decisions
   - Stories: 0 failures after adding the 平屋 rule (213 rows → (1, 0)). The earlier 213 failures came from a parser version without that rule. Lesson: run failure counts before `to_numeric`, and re-run them after any reload.
   - Floor: 1,004 missing = 997 `-` + 7 unparsed (`M9階` ×5, `9B9階` ×2), left as missing on purpose.

   - H3 first look: median rent 新築 ¥108,000 vs 築1年 ¥115,000. Median area 27.17 vs 26.04 m². Median rent per m² ¥3,783 vs ¥4,177. No raw premium for 新築 (prediction not supported); size does not explain it. Likely location mix, untested. Decision: keep is_new, test in the ablation under grouped CV.
- Area flags: 777 rows under 10 m², 22 rows over 300 m². Flag only, none removed.


- Tiny fees (admin ¥1-2, deposit/gratuity ¥100) always sit beside normal values in the other fee columns, so they look like placeholder amounts, not real fees (inferred, unverifiable). Count: [n]. Flagged as flag_fee_tiny; to be treated as missing in the move-in cost calculator; not used as features.


- Top rents: ¥4.45M (4SLDK, 365.51 m²) and the next four are all large units (218 to 415 m²) at ¥8,000 to ¥13,900 per m². Real luxury listings, not errors. Kept. Motivates H7 (log target) and per-price-band error reporting.
- no_gratuity: median rent ¥69,000 with `-` vs ¥91,000 with key money. Consistent with `-` meaning "none" (provisional). Age check: [result].

- Madori parser: 0 failures on 183,490 rows. Shapes: K, DK, LDK, SK, SDK, SLDK, LK, SLK, ワンルーム (28,417). No `1R` in the data. Outputs: n_rooms, has_L/D/K/S, is_1R.
- 12SLDK at 38.5 m² (¥110,000) is implausible; flagged via area-per-room, not deleted. Count flagged: [n].


- Two rows with impossible room counts: 12SLDK (38.5 m², ¥110,000) and 13K (25.0 m², ¥73,000). Likely typos in the room digit (inferred). Kept, flagged via flag_rooms_implausible (area per room under 6 m², threshold to be reviewed). Count flagged: [n].

- Area-per-room flag (under 6 m²): 47 rows. Mix of tiny ワンルーム units (3 to 5.8 m², rents consistent) and impossible layouts (2LDK at 5.10 m², 3LDK at 6.50 m², 1K at 1.00 m²; likely area typos, inferred). Replaced by flag_layout_area_conflict (n_rooms >= 2 and area < 15 m²); count: [n]. Nothing removed yet.

## 2026-10-15: Madori, stations, walk-time features

### Madori parser (`parse_rooms`)
- Shapes found: K, DK, LDK, SK, SDK, SLDK, LK, SLK, ワンルーム (28,417 rows). No `1R` in the data.
- Outputs: n_rooms, has_L, has_D, has_K, has_S, is_1R. **0 failures** on 183,490 rows.
- Implausible room counts: `12SLDK` (38.5 m², ¥110,000) and `13K` (25.0 m², ¥73,000). Likely typos in the room digit (inferred, unverifiable). Kept, flagged.
- Area-per-room flag (< 6 m²) caught 47 rows: a mix of tiny ワンルーム units (3 to 5.8 m², rents consistent) and impossible layouts (2LDK at 5.10 m², 3LDK at 6.50 m², 1K at 1.00 m²). Too blunt, so replaced by `flag_layout_area_conflict` (n_rooms >= 2 and area < 15 m²). Count: [n]. Nothing removed.

### Station entry formats
Three entry types, not one:
| Mode | Example | Fields |
|---|---|---|
| walk | `西武新宿線/東伏見駅 歩3分` | walk_min |
| bus | `JR中央線/三鷹駅 バス23分 (バス停)東伏見駅 歩3分` | bus_min, bus_stop_walk_min |
| car | `JR常磐線/亀有駅 車14分(4.1km)` | car_min, car_km |

- **Trap avoided:** the trailing `歩N分` on a bus entry is the walk to the bus stop, not to the station. Bus and car patterns are matched before walk, and `walk_min` stays None for bus entries (test added).
- Stations per listing: 1 station 8,071 (4.4%), 2 stations 11,588 (6.3%), 3 stations 163,831 (89.3%). The site appears to cap the list at 3, so `n_stations` is nearly constant and likely a weak feature (relevant to H6).
- Listings containing バス: 14,070 (7.7%); containing 車: 2,289 (1.2%).
- Copilot's `parse_station_entry` kept `駅` in station names (my spec dropped it). Decision: keep `駅`, which is safer for joining external station data.
- Tests: unit tests per mode plus `tests/test_real_data_stations.py` (every entry parses, entries per listing = commas + 1, bus never sets walk_min, mode counts match raw text). All pass.

### Station long table
- 522,728 rows for 183,490 listings. Matches the arithmetic exactly (8,071×1 + 11,588×2 + 163,831×3), so no entry was lost.
- Modes: walk 502,023 (96.0%), bus 18,085, car 2,620.
- Saved: `data/interim/stations_long.csv`, `data/interim/listings_parsed_v5.csv` (both gitignored).

### Walk-time features
- Built from **walk-mode rows only**: walk_min_nearest, walk_min_second, n_walk_stations, n_lines, walk_le_5/10/15, has_bus_access, has_car_access.
- 1,665 listings (0.9%) have no walk entry (bus or car only): `no_walk_access = 1`, walk columns NaN. Count: [confirm = 183,490 - 181,825].
- walk_min_nearest: median 7, mean 7.98, 75th percentile 10, max 202.
- Extreme walks: 474 listings > 30 min, 4 listings > 60 min. The max (202 min, 用賀駅, ¥135,000) is not plausible as a walk (likely a source error or a very distant station listed as walking). Flagged with `flag_walk_extreme`, not deleted. Threshold to review; [count flagged].
- Also noted: rows 159227 and 159228 are identical look-alikes (68-minute walk, ¥85,000), another example of the leakage risk handled by grouped CV.

### Lessons
- Failure counts must be run before `to_numeric` and re-run after any reload (the 213 `平屋` failures came from a stale saved file).
- Check shapes (digit-to-9, sample strings) before writing a regex; samples revealed bus/car formats that would have corrupted walk time.

### Open questions
- [ ] Is the 202-minute walk a source error?
- [ ] Do remote listings (bus/car only) need their own treatment in the model?
- [ ] Count of `flag_layout_area_conflict` rows.

## 2026-10-15: Location parsing and municipality features

### Name clash (incident)
- The parsed area column was assigned to `Area`, overwriting the raw location text. Noticed when `df["Area"].dtype` printed float.
- Fix: renamed the numeric column to `area_m2`; restored the text as `location` by mapping `jnc` to the original `Area` from `listings_dedup.csv` (`map`, not `merge`, so row order and index, and therefore the station long table's `listing_idx`, stayed valid). Result: 0 missing locations, 183,490 rows.
- Earlier results (H3 medians, area flags, top-rent table) used the numeric values, so they remain valid; only the labels were misleading.
- Lesson: never reuse a raw column name for parsed output. Parsed columns get a suffix (`_yen`, `_m2`).

### Lazy regex failure (caught before use)
- A first-pass regex on `location` truncated names: 東村山市 → 東村, 武蔵村山市 → 武蔵村, 羽村市 → 羽村, and the four 西多摩郡 towns collapsed into `西多摩郡` (317 rows).
- Decision: use a fixed list of Tokyo's 62 municipalities (`src/geo.py`, length checked = 62), match longest name first, skip an optional `…郡` prefix.

### `parse_location`
- Returns `(municipality, town)`, or `("FAILED", None)`; never raises. Tests in `tests/test_geo.py` (including the 62-name check).
- First Copilot-style draft returned only the municipality, never stripped `東京都`, and had no 郡 handling; it would have failed every real row. Caught by the answer key.
- Result: **0 failures** on 183,490 rows. **52 of 62** municipalities present.
- Missing (10): 三宅村, 八丈町, 利島村, 大島町, 小笠原村, 御蔵島村, 新島村, 檜原村, 神津島村, 青ヶ島村 (nine island municipalities plus 檜原村). Interpretation: the dataset has no island listings and none for 檜原村. Coverage fact, not a parser bug. The model cannot be expected to generalize to these areas.
- Previously truncated names now correct: 東村山市 1,877; 武蔵村山市 659; 羽村市 797.
- 西多摩郡 split: 瑞穂町 232, 日の出町 82, 奥多摩町 3 (sum 317, matches the earlier count). 檜原村 absent.
- Assumption: the 郡 skip looks only at the first 6 characters after 東京都. Verified by the 317 = 232 + 82 + 3 reconciliation.

### Region features
- `is_ward` (ends in 区) and `region` (ward / city / town_village). Counts: [paste `df["region"].value_counts()`]. Wards are [x]% of listings.

### Open questions
- [ ] Very small groups (奥多摩町 n=3, 日の出町 n=82): municipality-level target encoding will be noisy; use smoothing or fall back to region.
- [ ] Composite building key: with and without `age_years` (age drifted between scrapes for the same listing).

### Saved
- `data/interim/listings_parsed_v6.csv` (gitignored)

### Next
Composite building key (normalized title + municipality + town + stories + age; add nearest-station string for auto-generated titles), then check distinct keys and largest group sizes.

- Titles: 63,609 auto-generated (34.7%), 119,881 named (65.3%). Auto titles hold no building identity, so their key adds the raw station string and town; expect over-grouping (safe for CV, but check group sizes).

### Composite building key
- Key = normalized title | municipality | town | stories_above | stories_below; auto-generated titles (63,609 rows, 34.7%) also append the raw station string. Floor, rent, area, rooms, age and listing ID are excluded on purpose.
- Result: 93,731 distinct keys for 183,490 rows (mean 1.96 units per key, median 1, 75th percentile 2, max 121).
- Largest group (121 rows): [named complex or auto-title merge? result of the inspection].
- Look-alike consistency check (same look-alike group, different key): [n, expect 0].
- Distinct keys by type: auto [n], named [n]; max group size auto [n], named [n].
- Known limitation: auto-titled rows can merge unrelated buildings (over-grouping). This is the safe direction for grouped CV but reduces effective independent groups.

- Auto-title keys: 34,361 keys for 63,609 rows (mean 1.85, median 1, max 116). Named: ~59,370 keys for 119,881 rows. Similar grouping quality.
- Largest auto group (116 rows): [rent/area spread, municipality count: merge or complex?].
- Look-alike consistency (auto rows): [n, expect 0].
- No-age variant: [nunique, consistency result, decision].


- Building key results: 93,731 keys (auto 34,361, named 59,370). Look-alike consistency: 0 violations (all and auto rows).
- Largest groups are real tower blocks (121, 115, 102 listings; 14 to 15 floors).
- The 116-row auto group shares town, stories, median rent and area with the 121-row named group (南青山7, 15 floors): same building under two keys. Same pattern in 亀戸8. Finding: the named/auto split under-merges buildings (unsafe for CV).
- Decision (pending test): compare current key vs coarse key (municipality|town|stories only); prefer the coarse key for GroupKFold. Count of base keys holding both title types: [n].


### 2026-10-16: Grouping variable for CV
- Fine key (title-based) under-merges: 13,476 of 22,843 municipality|town|stories combinations (59%) hold both named and auto-titled rows, so the same building can sit in two groups. Unsafe for grouped CV.
- Decision: GroupKFold uses `group_coarse` = municipality|town|stories_above|stories_below (22,843 groups, over-merges, safe direction). `building_key` kept for same-building comparables.
- Largest coarse group: [n rows, % of data].
- Limitation: coarse groups merge distinct same-height buildings in one town, reducing independent groups, but protects against leakage.