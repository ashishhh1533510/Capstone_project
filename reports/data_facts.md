# UNSW-NB15 — data facts (Phase 1 EDA)

Source of every number: `notebooks/01_eda.ipynb` → `reports/tables/eda_*.csv`, `reports/figures/eda_*.png`.

**Size and classes.** Official partition: **175,341 training / 82,332 testing** connections, 10 classes,
42 features (39 numeric, 3 categorical: `proto`, `service`, `state`) plus `attack_cat` and `label`.
Normal is 31.9% of train and 44.9% of test. The largest attack classes are Generic (22.8%), Exploits
(19.0%) and Fuzzers (10.4%). The rarest is Worms with 130 training rows (0.07%). Note: the official
files are named the wrong way round (`…testing-set.csv` holds the 175,341 rows). The config maps
them so train = 175,341, as in the UNSW paper. *(eda_class_counts)*

**Quality.** Zero missing and zero infinite values in both splits. No constant numeric columns.
*(eda_missing_infinite)*

**Categoricals.** `proto` has 133 values. Top-10 covers 92.9% of training rows (tcp 45.6%, udp 36.1%,
unas 6.9%). `service` has 13 values, and 53.7% of training rows are `-` (no identified service).
`state` has 9 values in train. `CLO` and `ACC` appear **only in test** (5 rows), so the encoder must
ignore unseen categories. *(eda_values_\*, eda_categorical_summary)*

**Latency rows for the DNN.** 45.6% of training rows are TCP. 98.9% of those have `tcprtt > 0` and
`synack > 0`. Non-TCP rows never have `tcprtt > 0`. Regression split C (normal, TCP, handshake)
has **38,244 train** and **26,082 test** rows, before the 15% validation split. *(eda_tcp_handshake_coverage)*

**Leakage confirmed.** `tcprtt = synack + ackdat` holds on **100%** of rows in both splits (max
difference 4.4×10⁻¹⁶ s, floating-point rounding). `synack` and `ackdat` must stay out of the DNN
inputs. *(eda_leakage_check)*

**Two latency regimes.** Normal handshake traffic is bimodal, and the TTL pair sets the regime:
`sttl/dttl = 31/29` gives a median `tcprtt` of 0.67 ms (≈99% under 10 ms), while `254/252` and
`62/252` give 150–177 ms. The mix differs by split: the fast regime is **74.4% of train normal
but 46.2% of test normal**. So the normal median `tcprtt` is 0.7 ms in train vs 94.9 ms in test.
Per attack class, median handshake `tcprtt` is 95–154 ms in both splits. *(eda_latency_regimes, eda_latency_stats,
eda_latency_by_class, eda_latency_distributions)*

**Packet loss is not mostly zero.** Only 54.4% of training rows have `sloss = dloss = 0`, and only
**30.2% of normal** rows. `sloss`/`dloss` track bytes almost exactly (r = 0.996 with
`sbytes`/`dbytes`). *(eda_loss_zero_share, eda_high_correlation_pairs)*

**Correlation.** 16 numeric feature pairs have |r| ≥ 0.9: bytes/packets/loss, the `ct_*` counters,
`swin`/`dwin`, and `is_ftp_login`/`ct_ftp_cmd` (r = 1.0). *(eda_correlation_heatmap, eda_high_correlation_pairs)*

## What this changes for later phases

1. **Roadmap assumption wrong:** "share of zero loss justifies not predicting loss" — the data
   does not support it. The decision (show loss, don't predict it) needs a different reason or a
   rethink. *Open — for the user to decide.*
2. **DNN / latency gap:** `sttl`/`dttl` must stay in the DNN inputs so it can tell the regimes apart.
   Because the regime mix shifts between train and test, the latency-gap false-alarm rate on
   test normal rows must be checked per regime.
3. **Live demo:** lab VMs will produce TTLs (64/128 minus hops) that never appear in UNSW-NB15
   (31/29, 254/252, 62/252). TTL-dependent predictions may not transfer — check this in Phase 7/12.
4. **Encoding:** one-hot with `handle_unknown="ignore"` (`state` CLO/ACC appear only in test).
