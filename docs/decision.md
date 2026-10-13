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




## 2026-10-11:Decisions
- `平屋`: 213 rows (0.12%). Parsed as stories_above=1, stories_below=0 (domain decision).
- 平屋 rent: median ¥80,000, mean ¥96,704, range ¥39,000 to ¥350,000. Not clearly higher than the dataset median (¥82,500); my guess that houses rent higher was not supported.
- Keep an `is_hiraya` flag as a candidate feature (a rare property type; no property-type column exists). Test it in the ablation, don't assume it helps.


- (997 rows, 0.5%): return (None, None, None), a legitimate missing value, not a parse failure. Keep the row; flag floor_missing. Floor is a weak feature anyway.
Basement B1: encode as a negative number, so B1階 becomes -1. Check a few rows to confirm these are really basement units.
Open-ended ranges like 1-階: the end is unknown. Simplest rule: treat as a multi-floor unit with floor_max = floor_min, and flag it. Only 32 rows, so don’t agonize.
M9階 (5) and 9B9階 (2): I’m not sure what these mean. Look at the rows (title, stories, rooms) and decide. With 7 rows total, returning FAILED and excluding or flagging them is acceptable, and honest.


Floor shapes found and the rule for each (- becomes missing, B becomes negative, open range 1-階 gets floor_max = floor_min and flag 1, M9階/9B9階 fail on purpose)
Failure count, multi-floor count, basement count, missing count
Number of rows where floor exceeds building height
One line: “Copilot’s first parse_floor rejected open-ended ranges; caught by tests, fixed.”