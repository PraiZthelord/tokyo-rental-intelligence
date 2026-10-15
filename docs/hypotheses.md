# Hypothesis log

Rule: write the prediction and the success criterion BEFORE running the test. Record failures too.

| # | Hypothesis | Prediction | Test | Success criterion | Result | Decision |
|---|---|---|---|---|---|---|
| H1 | Walk time has a nonlinear relationship with rent | Rent drops faster in the first ~10 min, then flattens | Compare raw walk_min_nearest vs spline/threshold terms (5, 10, 15 min) using grouped CV | Lower MAE than raw term, beyond CV noise | **First look only, not tested.** Raw median rent falls from ¥100,000 (1 min) to ¥69,000 (15 min), about ¥2,200 per minute. Not smooth: plateau at 2 to 4 min (95k, 92k, 92k), bumps at 9 and 11 min (likely noise or location mix). Confounded by location. | Run the ablation under grouped CV before concluding. |
| H2 | Structured madori adds information beyond floor area | Helps most for small units (1R to 1LDK) | Ablation: area-only vs area + n_rooms, has_L/D/K/S | MAE improvement with CI excluding 0 | pending | pending |
| H3 | New builds (新築) carry a rent premium beyond age 0 vs 1 | Median rent for 新築 > 築1年 | Compare medians, then `is_new` ablation | Premium persists after controlling for area and location | **First look: not supported.** Median rent 新築 ¥108,000 vs 築1年 ¥115,000. Median area 27.17 vs 26.04 m². Median rent per m² ¥3,783 vs ¥4,177. Size does not explain the gap; location mix is the suspected cause (untested). | Keep `is_new` as a candidate. Final decision after ablation under grouped CV. |
-
| H4 | A step at ~45 years (1981 新耐震基準) exists beyond a smooth age curve | Weak or absent | Add `age >= 45` flag on top of a flexible age term | MAE gain beyond CV noise | pending | pending |
| H5 | Random-split CV overstates performance vs building-grouped CV | Random MAE noticeably lower | Same model, random vs grouped CV | Gap is larger than fold-to-fold variation | pending | pending |
| H6 | Multiple station access adds information beyond nearest-station walk time | Weak: n_stations is nearly constant (89% = 3); n_lines and has_bus_access may carry more | Ablation with n_walk_stations, n_lines, has_bus_access | MAE improvement beyond noise | pending | pending |
| H7 | Log(rent) target beats raw rent | Better on RMSE and on expensive listings | Same model, both targets, compare on original scale | Lower MAE on original scale | pending | pending |
| H8 | Deposit and key money are multiples of rent, so they leak the target | Confirmed | Distribution in months of rent | ~90% at exactly 1 month | **Confirmed** (deposit 90.0%, gratuity 90.1% at 1 month) | Excluded from features |
| H9 | The 新築 rent gap is explained by location mix | 新築 listings skew toward cheaper municipalities | Compare the municipality distribution of age 0 vs age 1; compare rent per m² within the same municipality | Gap shrinks or reverses within municipality | pending | pending |

## Already resolved (data-audit findings)
- `jnc` is a listing ID, not a building ID (repeats match exact duplicates). Composite building key needed.
- 20.1% of rows are look-alikes (identical except ID), so random splits are likely leaky. This motivates H5.
- Guess that 平屋 rents above market was **not supported** (median ¥80,000 vs ¥82,500).