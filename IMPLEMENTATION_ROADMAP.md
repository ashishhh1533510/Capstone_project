# Implementation Roadmap — Cloud-Based Network Traffic Analysis, Anomaly Detection and Latency Prediction

PROJ2999 Capstone · GITAM Hyderabad · Guide: Dr P. Sowjanya
Team: Ashish Kumar (lead), N. Tarun, P. Ganesh, K. Sathwik — all build work done by Ashish alone

This file lists every step from an empty folder to the final demo. Each phase ends with a
**Done when** check — do not start the next phase until it passes.

---

## 1. What we are building (plain words)

For every network connection the system answers two questions:

1. **Is this an attack?** — Random Forest (known attacks) + Isolation Forest (anything unusual).
2. **Is this connection slower than it should be?** — a DNN predicts the latency and response time a
   *healthy* network would show; if the real value is much higher, that is a degradation warning.

Every alert gets a plain-English explanation from a Gemini agent. Results are stored in Azure and
shown on a Streamlit dashboard. A live demo captures real traffic from two lab VMs.

## 2. Decisions already locked (from the grill-me session)

| Area | Decision |
|---|---|
| Dataset | **UNSW-NB15**, official partition files (175,341 train / 82,332 test) |
| DNN task | Per-connection estimation (not time-window forecasting) |
| DNN outputs | `tcprtt` (latency) and `synack` (server response time) — 2 outputs |
| DNN inputs | All features **except** `tcprtt`, `synack`, `ackdat` (leakage: `tcprtt = synack + ackdat`) |
| DNN training data | **Normal** TCP connections only, with `tcprtt > 0` and `synack > 0` |
| Target transform | Train on `log1p(target)`, report metrics in original units |
| Splits | Official train/test (main) + unseen-attack variant: **DoS, Reconnaissance, Backdoor** removed from training only |
| Validation | 15% of training, stratified, fixed seed |
| Features | Full feature set for experiments + a second **live-subset** model set (Argus-reproducible features) for the demo |
| Encoding | One-hot `service`, `state`; `proto` = top-10 + "other"; StandardScaler fit on train only |
| Detectors | Random Forest (10 classes, `class_weight="balanced"`); Isolation Forest (in pipeline); One-Class SVM (comparison only) |
| DBSCAN | **Dropped** (no `predict()`, not streamable) |
| Thresholds | 95th percentile of **normal validation** scores (IF, OCSVM and DNN latency gap) — no attack labels used |
| Regression baselines | Mean predictor, Ridge (unscaled), Ridge (scaled), Lasso (L1), ElasticNet (L1+L2), HistGradientBoosting |
| DNN framework | **PyTorch** + Optuna (search over learning rate, depth, width, dropout) |
| Fusion | Labelled tiers: Known attack → Unknown anomaly → Performance degradation → Normal |
| Cloud | **Azure**: Blob Storage (Parquet) + VM running FastAPI (models + agent) + Streamlit |
| Inference | Cloud API — capture machine sends feature rows, Azure scores them |
| Agent | Gemini + LangGraph + LangSmith; explains alerts only; no action tools; cached |
| Agent evaluation | ~50 self-written reference explanations; **BERTScore** for agent **vs** template explainer; 1–5 human rating |
| Live demo | Two local VMs on a private network; nmap, hping3, `tc netem`; tcpdump → Argus → API; pcap replay as backup |

## 3. Final repository layout

```
capstone_project_2023003296/
├── README.md
├── IMPLEMENTATION_ROADMAP.md
├── pyproject.toml                # or requirements.txt + requirements-dev.txt
├── .env.example                  # AZURE_*, GOOGLE_API_KEY, LANGSMITH_* (never commit .env)
├── .gitignore
├── configs/
│   └── config.yaml               # paths, seed, held-out classes, thresholds, feature lists
├── data/                         # git-ignored
│   ├── raw/                      # UNSW_NB15_training-set.csv, UNSW_NB15_testing-set.csv
│   ├── processed/                # parquet splits
│   └── pcaps/                    # demo recordings
├── models/                       # git-ignored: *.joblib, *.pt, scaler, encoders
├── reports/
│   ├── figures/
│   └── tables/
├── notebooks/
│   └── 01_eda.ipynb
├── src/cnad/
│   ├── __init__.py
│   ├── config.py                 # loads config.yaml
│   ├── data/
│   │   ├── load.py               # read CSVs, clean labels
│   │   ├── preprocess.py         # encoding, scaling, column lists
│   │   └── splits.py             # official, held-out, validation, regression subset
│   ├── detection/
│   │   ├── supervised.py         # Random Forest
│   │   ├── unsupervised.py       # Isolation Forest, One-Class SVM, thresholds
│   │   └── evaluate.py
│   ├── regression/
│   │   ├── baselines.py          # mean, Ridge, Lasso, ElasticNet, HistGB
│   │   ├── dnn.py                # PyTorch model + training loop
│   │   ├── tune.py               # Optuna search
│   │   └── evaluate.py
│   ├── fusion/
│   │   └── tiers.py              # labelled-tier alert logic
│   ├── cloud/
│   │   └── blob.py               # Parquet read/write to Azure Blob
│   ├── api/
│   │   ├── main.py               # FastAPI app
│   │   └── schemas.py            # Pydantic request/response models
│   ├── agent/
│   │   ├── graph.py              # LangGraph state graph
│   │   ├── prompts.py
│   │   ├── template_explainer.py # non-LLM baseline
│   │   └── evaluate.py           # BERTScore + human ratings
│   ├── live/
│   │   ├── capture.sh            # tcpdump + argus
│   │   ├── argus_to_features.py  # Argus output → live-subset schema
│   │   └── client.py             # sends rows to the API
│   └── dashboard/
│       └── app.py                # Streamlit
├── scripts/                      # thin entry points: train_detectors.py, train_regression.py, ...
└── tests/
```

---

## Phase 0 — Project setup and boilerplate

1. Create the repo folders above and an empty `src/cnad` package.
2. Create a Python 3.11 virtual environment.
3. Write `pyproject.toml` / `requirements.txt` with pinned versions:
   `pandas, numpy, pyarrow, scikit-learn, torch, optuna, joblib, pyyaml, matplotlib, seaborn,
   fastapi, uvicorn, pydantic, azure-storage-blob, adlfs, streamlit, plotly, langchain,
   langgraph, langchain-google-genai, langsmith, bert-score, python-dotenv`
   Dev: `pytest, ruff, jupyter`.
4. Add `.gitignore` (`data/`, `models/`, `.env`, `__pycache__/`, `.venv/`).
5. Add `.env.example` with every secret name and no values.
6. Write `configs/config.yaml` (seed = 42, file paths, held-out classes, threshold percentile = 95,
   validation fraction = 0.15) and `src/cnad/config.py` to load it.
7. Write a one-paragraph `README.md` with setup commands.
8. Set up Git: first commit, `main` branch protected by convention, one branch per phase.

**Done when:** `pip install -e .` works, `python -c "import cnad"` runs, and `pytest` runs (zero tests is fine).

## Phase 1 — Get and understand the data (EDA)

1. Download the UNSW-NB15 partition CSVs from the official UNSW source into `data/raw/`.
2. `load.py`: read both CSVs, strip whitespace in `attack_cat`, standardise class names, drop `id`.
3. In `01_eda.ipynb`, record and save to `reports/`:
   - Row counts per class, train vs test (check against the known numbers).
   - Missing and infinite values per column.
   - Value counts for `proto`, `service`, `state`.
   - Share of TCP rows, and share of TCP rows with `tcprtt > 0` and `synack > 0`.
   - Distribution of `tcprtt` and `synack` (raw and log), normal vs attack.
   - Confirm `tcprtt ≈ synack + ackdat` (proves the leakage rule).
   - Share of zero `sloss`/`dloss` (justifies not predicting loss).
   - Correlation heatmap of the numeric features.
4. Write a half-page "data facts" note in `reports/` — this feeds the Review 2 slides.

**Done when:** every number you will quote about the dataset is saved in a table or figure.

## Phase 2 — Preprocessing and splits

1. `preprocess.py`:
   - Define column lists in config: `categorical`, `numeric`, `label`, `attack_cat`,
     `regression_targets = [tcprtt, synack]`, `regression_drop = [tcprtt, synack, ackdat]`.
   - One-hot `service` and `state`; `proto` → top-10 + "other".
   - StandardScaler fitted on training rows only; save the fitted transformer with joblib.
2. `splits.py` — produce and save as Parquet:
   - **A. Official:** train (minus validation) / validation (15%, stratified by `attack_cat`) / test.
   - **B. Held-out:** same as A but DoS, Reconnaissance and Backdoor removed from train and validation;
     test unchanged.
   - **C. Regression:** normal-only, TCP, `tcprtt > 0` and `synack > 0`, taken from A's
     train/validation/test; inputs exclude `regression_drop`; targets are `log1p` of the two values.
3. Define the **live-subset feature list** in config: the features Argus can produce
   (durations, packet and byte counts, TTLs, loads, loss, inter-packet times, jitter, window sizes,
   TCP base sequence numbers, mean packet sizes, plus `tcprtt`/`synack`/`ackdat` for detection).
4. Unit tests: no test rows in training; held-out classes absent from B-train; no leakage columns in
   C inputs; scaler fitted only on train.

**Done when:** all split files exist, tests pass, and row counts are logged.

## Phase 3 — Attack detectors

1. `supervised.py`: Random Forest, 10 classes, `class_weight="balanced"`; small grid over
   `n_estimators`, `max_depth`, `min_samples_leaf` on validation macro-F1.
2. `unsupervised.py`:
   - Isolation Forest trained on normal training rows only.
   - One-Class SVM (RBF) on normal rows only — subsample (e.g. 20k) if training is too slow.
   - Threshold = 95th percentile of each model's score on **normal validation** rows.
3. `evaluate.py` — for each model on split A and split B:
   - Multiclass (RF only): per-class precision/recall/F1, macro-F1, confusion matrix.
   - Binary (all): accuracy, precision, recall, F1, false-alarm rate, ROC-AUC.
   - Split B: detection rate **per held-out class** (DoS, Recon, Backdoor reported separately).
4. RF feature importance chart (used later by the dashboard and the agent).
5. Save models to `models/` and all tables/figures to `reports/`.

**Done when:** one comparison table shows RF vs IF vs OCSVM on known and unseen attacks.

## Phase 4 — Regression baselines

1. `baselines.py`: mean predictor; Ridge on unscaled inputs; Ridge on scaled inputs; Lasso;
   ElasticNet; HistGradientBoosting (wrapped in `MultiOutputRegressor`).
2. Tune alpha / l1_ratio / HistGB depth and learning rate on validation.
3. `evaluate.py` (shared with the DNN): per target, on split C test, in **original units**:
   RMSE, MAE, MAPE, R². Also a predicted-vs-actual scatter plot per target.
4. Save the baseline results table.

**Done when:** every baseline beats the mean predictor and the table is saved.

## Phase 5 — The DNN

1. `dnn.py`:
   - `nn.Module`: input → [Linear → ReLU → Dropout] × depth → Linear(2).
   - Start: 128 → 64 → 32, dropout 0.2, Adam, MSE loss on log targets, batch size 512.
   - One reusable `train_one(model, loaders, cfg)` function: train loop, validation loop,
     early stopping (patience ≈ 10), best checkpoint saved, loss curves logged.
   - Fix all seeds (`torch`, `numpy`, `random`).
2. `tune.py`: Optuna search (~50 trials) over learning rate (log scale 1e-4…1e-2), depth (2–4),
   width (64–512), dropout (0–0.4), weight decay. Objective = validation RMSE.
3. Retrain the best configuration with 3–5 seeds; report mean ± std.
4. Evaluate on split C test with the same metrics as Phase 4.
5. Figures: learning-rate sweep vs validation RMSE; training/validation loss curves.

**Done when:** one table shows DNN vs all baselines (mean ± std for the DNN), and the result is
reported honestly whichever model wins.

## Phase 6 — Fusion (connecting the parts)

1. Latency gap: `gap = log1p(actual_tcprtt) − log1p(predicted_tcprtt)`; only positive gaps count;
   threshold = 95th percentile of gaps on **normal validation** rows. Same for `synack`.
   Rows without a handshake get "no latency signal".
2. `tiers.py`: for each row —
   RF says attack → **Known attack: <type>**;
   else IF flags → **Unknown anomaly**;
   else latency gap above threshold → **Performance degradation**;
   else **Normal**. Each output carries the reason and the raw scores.
3. Evaluate:
   - Each tier on its own.
   - Combined "any alert" recall and false-alarm rate on splits A and B.
   - **Bridge result:** distribution of the latency gap for normal vs attack rows, especially the
     held-out DoS rows; count how many held-out attacks RF missed but the latency gap caught.

**Done when:** the bridge result figure exists — this is the main new contribution for Review 2.

## Phase 7 — Live-subset models

1. Retrain RF, IF and the DNN using only the live-subset features (same splits, same procedures).
2. Table: full-feature vs live-subset scores — the accuracy cost of deployability.
3. Save these as the models the API loads.

**Done when:** live-subset models are saved and the comparison table exists.

## Phase 8 — Cloud storage (Azure)

1. Activate Azure for Students (eligibility confirmed); create a resource group, a Storage Account and one container.
2. `blob.py`: `write_parquet(df, folder)` and `read_parquet(folder, since=None)` using
   `azure-storage-blob` / `adlfs`; credentials from `.env`.
3. Folder layout: `processed/date=YYYY-MM-DD/`, `alerts/date=…/`, `agent_traces/date=…/`;
   write in micro-batches (e.g. every 100 rows or 10 seconds), not one file per row.
4. Upload the offline evaluation tables too, so the dashboard can show them.

**Done when:** a script writes and reads back a test batch from Blob.

## Phase 9 — Inference API (FastAPI on Azure)

1. `schemas.py`: Pydantic model for a live-subset feature row and for the tiered alert response.
2. `main.py`:
   - Load preprocessors and live-subset models once at startup.
   - `POST /score` — accepts a batch of rows, returns tiered alerts, buffers results to Blob.
   - `GET /health`.
3. Local test with uvicorn and sample rows from the test split.
4. Provision a small Azure Linux VM; install the project; run with uvicorn behind systemd;
   open only the needed port; secrets via environment variables.

**Done when:** `curl` from your laptop to the Azure VM returns correct tiered alerts.

## Phase 10 — Explanation agent

1. `template_explainer.py`: fill-in-the-blank explanations from tier, type, top RF features and
   latency gap (the non-LLM baseline).
2. `graph.py` — LangGraph state graph: gather context (alert, scores, top features, recent related
   alerts) → Gemini writes explanation → format check → output. **No action tools.**
3. Trigger only for alerts, never for normal rows; cache by alert ID; rate-limit Gemini calls.
4. Add `POST /explain/{alert_id}` to the FastAPI app; store explanations in `agent_traces/`.
5. LangSmith tracing on every run (latency, tokens, cost).
6. Evaluation (`agent/evaluate.py`):
   - Sample ~50 alerts covering every tier and attack type.
   - Write one reference explanation per alert **before** reading model outputs.
   - BERTScore (precision/recall/F1) for the agent and for the template explainer.
   - Rate each agent explanation 1–5 for correctness.
   - Report mean latency and cost per explanation from LangSmith.

**Done when:** a table shows agent vs template on BERTScore, human rating, latency and cost.

## Phase 11 — Dashboard (Streamlit on Azure)

1. Pages: **Overview** (traffic volume, protocol/service mix); **Alerts** (filter by tier and type,
   click to show the explanation); **Latency** (expected vs actual over time, gap histogram);
   **Model results** (offline tables and figures from Blob); **About** (architecture diagram).
2. Read from Blob with caching; auto-refresh every few seconds.
3. Run on the same Azure VM as the API (separate port/service).

**Done when:** the dashboard on Azure shows test-split rows streamed through the API.

## Phase 12 — Live capture and demo environment

1. Two VMs on a host-only network on one laptop: **attacker** (Kali) and **target** (Ubuntu running
   SSH and a small web server). Never point attack tools at any other network.
2. `capture.sh`: tcpdump on the target interface → rotating pcap → Argus → `ra` output with the
   needed fields.
3. `argus_to_features.py`: map Argus fields to the live-subset schema; check feature distributions
   against training data (flag big drifts before trusting predictions).
4. `client.py`: batch rows and send them to `POST /score` on Azure.
5. Demo scenarios, each recorded as a pcap backup:
   - Normal browsing / SSH → mostly **Normal**.
   - `nmap` scan → **Known attack** or **Unknown anomaly**.
   - `hping3` SYN flood → **Known attack** (DoS).
   - `tc netem delay 300ms` on the target → **Performance degradation**.
6. Rehearse full replay from pcap in case the live path fails.

**Done when:** all four scenarios show the expected tier on the Azure dashboard, live and from replay.

## Phase 13 — Testing, reproducibility and clean-up

1. Unit tests for preprocessing, splits, tiers, API schemas, Argus mapping.
2. One integration test: sample rows → API → Blob → readable by dashboard.
3. `scripts/` entry points rerun every experiment from scratch with the fixed seed.
4. `ruff` clean; README with setup, run order, and expected outputs.
5. Shut down or deallocate Azure VMs when not in use (avoid burning credits).

**Done when:** a fresh clone on a clean machine reproduces every table by following the README.

## Phase 14 — Results, report and final demo

1. Final tables:
   - Detection: RF vs IF vs OCSVM, known vs unseen (per held-out class).
   - Regression: mean / Ridge / scaled Ridge / Lasso / ElasticNet / HistGB / DNN on RMSE, MAE, MAPE, R².
   - Bridge: latency gap normal vs attack; attacks caught only by the latency tier.
   - Full vs live-subset accuracy cost.
   - Agent vs template: BERTScore, human rating, latency, cost.
2. Figures: confusion matrices, ROC curves, predicted-vs-actual, learning-rate sweep, gap
   histograms, architecture diagram.
3. Slides for review (scope changes since Review 1 are explained to the guide in person).
4. Report: problem statement, objectives, related work (six papers + UNSW-NB15 paper),
   methodology, results, limitations (lab dataset, no real failures, DoS/Exploits overlap,
   one-region cloud, single human rater for agent explanations), future work.
5. Demo script (≈10 minutes): architecture → offline results → live scenarios on the dashboard →
   click an alert to show its explanation → LangSmith trace.

**Done when:** the demo runs end to end twice in a row without manual fixes.

---

## Known risks and what we do about them

| Risk | Mitigation |
|---|---|
| DNN does not beat HistGradientBoosting | Report it honestly; the DNN's value is the latency-gap signal and multi-output design |
| Leakage inflates regression scores | `regression_drop` enforced in code and by a unit test |
| DoS looks like Exploits, so unseen test looks easy | Report per-class and multiclass confusion, not just binary |
| MAPE explodes on tiny latencies | `> 0` filter; also report MAE and RMSE; consider SMAPE if needed |
| Live features drift from training data | Distribution check in `argus_to_features.py`; live-subset models |
| Azure credits run out | Deallocate VMs when idle; keep the local run path working |
| Gemini cost / non-determinism | Alerts only, caching, temperature 0, LangSmith monitoring; template fallback |
| Live demo fails on the day | Recorded pcap replay of every scenario |
