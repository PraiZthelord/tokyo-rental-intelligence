# Hypothesis log

Rule: write the prediction and success criterion BEFORE running the test. Record failures too.
Grouping variable for all grouped CV: `group_coarse` = municipality|town|stories_above|stories_below (22,843 groups).

| # | Hypothesis | Prediction | Test | Success criterion | Result | Decision |
|---|---|---|---|---|---|---|
| H1 | Walk time has a nonlinear relationship with rent | Rent drops faster in the first ~10 min, then flattens | Raw `walk_min_nearest` vs spline/threshold terms (5, 10, 15 min), grouped CV | Lower MAE than raw term, beyond CV noise | **First look only, not tested.** Raw median rent falls from ¥100,000 (1 min) to ¥69,000 (15 min), about ¥2,200/min. Plateau at 2-4 min; bumps at 9 and 11 min (likely noise or location mix). Confounded by location. | Run ablation under grouped CV |
| H2 | Structured madori adds information beyond floor area | Helps most for small units (1R to 1LDK) | Ablation: area-only vs area + n_rooms, has_L/D/K/S, is_1R | MAE improvement with CI excluding 0 | Pending. Parser done (0 failures, 183,490 rows). | Run ablation |
| H3 | New builds (新築) carry a rent premium beyond age 0 vs 1 | Median rent 新築 > 築1年 | Compare medians, then `is_new` ablation | Premium persists after controlling for area and location | **First look: not supported.** Median rent ¥108,000 (新築) vs ¥115,000 (築1年). Median area 27.17 vs 26.04 m². Rent per m² ¥3,783 vs ¥4,177. Size does not explain it; location mix suspected (untested). | Keep `is_new`; decide after ablation |
| H4 | A step at ~45 years (1981 新耐震基準) exists beyond a smooth age curve | Weak or absent | Add `age >= 45` flag on top of a flexible age term | MAE gain beyond CV noise | Pending. Caveat: data spans multiple scrape dates (age drifted between rows of one listing), so age near the cutoff is approximate. 築99年以上 capped at 99 (4 rows). | Run ablation |
| H5 | Random-split CV overstates performance vs grouped CV | Random MAE noticeably lower | Same model, `KFold` shuffled vs `GroupKFold` on `group_coarse` | Gap larger than fold-to-fold variation | Pending. Motivation: 20.1% of rows are look-alikes (identical except listing ID). Fine `building_key` under-merges (13,476 of 22,843 municipality|town|stories combos hold both named and auto-titled rows), so the coarse key is the grouping variable. | Run baselines |
| H6 | Multiple station access adds information beyond nearest-station walk time | Weak: `n_walk_stations` is nearly constant (89% have 3); `n_lines` and `has_bus_access` may carry more | Ablation with n_walk_stations, n_lines, has_bus_access | MAE improvement beyond noise | Pending | Run ablation |
| H7 | log(rent) target beats raw rent | Better RMSE and on expensive listings | Same model, both targets, compare on original scale | Lower MAE on original scale | Pending. Motivation: right-skewed rent (mean ¥99,317 vs median ¥82,500; max ¥4.45M real luxury units). | Run comparison |
| H8 | Deposit and key money are multiples of rent, so they leak the target | Confirmed | Distribution in months of rent | ~90% at exactly 1 month | **Confirmed.** Deposit 90.0% and gratuity 90.1% at 1 month. | Excluded from features |
| H9 | The 新築 rent gap is explained by location mix | 新築 listings skew toward cheaper municipalities | Compare municipality distribution of age 0 vs 1; rent per m² within municipality | Gap shrinks or reverses within municipality | Pending. `municipality` now available. | Run check |
| H10 | Remote listings (bus/car access only) rent differently from walkable ones | Lower rent per m² | Compare `no_walk_access` (1,665 listings, 0.9%) vs rest, within municipality | Difference persists within municipality | Pending | Run check |

## Already resolved (data-audit findings)
- `jnc` and `bc` are listing IDs, not building IDs (repeats match exact duplicates).
- 20.1% of rows are look-alikes (identical except ID), so random splits are likely leaky. Motivates H5.
- Guess that 平屋 rents above market was **not supported** (median ¥80,000 vs ¥82,500).
- Bus entries end with `歩N分` too; reading that as station walk time would have corrupted H1 (caught before applying, via sample strings and a dedicated test).
- Stations per listing is capped at 3 (89% have exactly 3), so H6 mostly tests line count and access mode.
- `no_gratuity` rows have lower median rent (¥69,000 vs ¥91,000), consistent with `-` meaning "none" (provisional).
- Top rents (¥3M+) are real luxury units (218 to 415 m²), not errors.
- Title-based building key under-merges (same tower appears under a named key and an auto-title key), so grouped CV uses the coarse key.

