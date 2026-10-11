# Session Handover

Sessions 1 (scoping, sections 1–7), 2 (Phase 0 build, section 8) and 3 (Phase 1 EDA, section 10).
Next step is in section 11.

**Last updated:** 2026-10-11 · **Current status:** Phase 1 complete (branch `phase-1`), Phase 2 not started
**Project:** PROJ2999 Capstone — Cloud-Based Network Traffic Analysis and Anomaly Detection Using ML
**Team:** Ashish Kumar (2023003296, lead), N. Tarun, P. Ganesh, K. Sathwik — Ashish does all build work alone · **Guide:** Dr P. Sowjanya
**Companion file:** `IMPLEMENTATION_ROADMAP.md` (the phase-by-phase build plan — read it next)

---

# Session 1 — Post-Review-1 Scoping (grill-me session)

## 1. Purpose of the session

After Review 1, the supervisor gave handwritten feedback. The goal was to work out what she is asking
for, decide the technical direction through a grill-me interview (one question at a time), and produce
a build plan so coding can start. **No code was written in this session.**

## 2. Source materials and what was actually read

| Material | Location | Status |
|---|---|---|
| Review 1 deck (20 slides + speaker notes) | `C:\Users\Ashis\OneDrive\Documents\Capstone_Review1_Cloud_Network_Anomaly_Detection.pptx` | Read in full (first attempt failed: file locked while open in PowerPoint) |
| Supervisor's handwritten feedback | `C:\Users\Ashis\Downloads\WhatsApp Image 2026-10-11 at 5.22.50 PM.jpeg` | Read |
| Initial requirements ("Image #1") | Was meant to be attached | **Never received.** Slide 14 quotes the approved project description verbatim; that was used instead. Not needed for now — ask the user for it only if a requirement question comes up |

Note: the `/grill-me` skill tried to call a `grilling` skill that does not exist in this environment;
the grill-me approach was followed manually.

## 3. What Review 1 proposed (nothing implemented yet)

- Dataset: CICIDS2017 (~80 CICFlowMeter features).
- Supervised: Random Forest (O1 oddly said "classifier/regressor").
- Unsupervised: Isolation Forest (benign-only), One-Class SVM comparison; DBSCAN rejected for online use.
- Metrics: accuracy, precision, recall, F1, known vs unseen attacks (following paper [3]).
- Pipeline: live capture → CICFlowMeter → Parquet in S3/Azure → Streamlit.
- Agent: Gemini + LangGraph + LangSmith, explains alerts, advisory only, evaluated qualitatively only.
- Approved description mentions "cyberattacks **or network failures**" — the deck covered attacks only.

## 4. Supervisor's note — transcription and interpretation

```
Comments,
Proposed framework – Ridge Regression | SVM | DBSCAN   (something bracketed above, possibly "SVR")
                   – Scaled – Ridge Regression
                   – L1/L2 – Regression
                   – DNN & DENN / BERT
Performance metric
   └ n/w latency / Delay
   └ Response time, Error rate / learning rate / MSE? / RMSE
   MPE (likely MAPE)      BERTScore
```

Interpretation reached in the session:
- The model list (Ridge, L1/L2, RMSE, MAPE) is regression-oriented → add a **regression task**
  predicting network performance (latency, response time). This also covers the "network failures"
  half of the approved scope that the deck skipped.
- The DNN is one option in her model list, not explicitly a separate "layer"; we chose to make it a
  latency/response-time predictor that sits **beside** the detectors.
- **BERT / BERTScore** most plausibly refer to the explanation agent → BERTScore used to score
  explanations quantitatively. BERT as a model was rejected (text model; data is tabular).
- **DENN** is not a standard term → not used.
- **Learning rate** is a hyperparameter, not a metric → covered as a learning-rate sweep chart.
- CICIDS2017 has **no latency/response-time labels**, so the dataset had to change.

## 5. Decisions made (with who chose what)

All options were presented via structured questions; the user picked the recommended option unless noted.

| # | Topic | Decision | Notes |
|---|---|---|---|
| 1 | Dataset | **UNSW-NB15** official partition (175,341 train / 82,332 test) | Chosen by Claude at the user's request. Has `tcprtt` (latency), `synack` (response time), `sloss`/`dloss`, `sjit`/`djit`, 9 attack classes |
| 2 | DNN choice | Plain feed-forward **DNN** | Chosen by Claude at the user's request; DENN and BERT dropped |
| 3 | Supervisor contact | **Not** confirming with supervisor before building | User's explicit choice |
| 4 | DNN task | Per-connection estimation (not time-window forecasting) | |
| 5 | DNN targets | `tcprtt` + `synack` (2 outputs); inputs exclude `tcprtt`, `synack`, `ackdat` | Leakage: `tcprtt = synack + ackdat`. Packet loss shown on dashboard, not predicted |
| 6 | DNN training data | Normal traffic only | Enables the "latency gap" degradation signal |
| 7 | Splits | Official split + unseen-attack variant | |
| 8 | Held-out classes | DoS, Reconnaissance, Backdoor | Caveat: DoS resembles Exploits → report per class |
| 9 | Feature set | Full features for experiments + live-subset (Argus-reproducible) models for demo | |
| 10 | Unsupervised threshold | 95th percentile of normal validation scores | Same rule for the DNN latency gap |
| 11 | DBSCAN | **Dropped** | **User overrode** the recommendation (offline baseline). No justification slide needed |
| 12 | Strong regression baseline | Add HistGradientBoosting | Alongside mean, Ridge, scaled Ridge, Lasso, ElasticNet |
| 13 | DNN framework | **PyTorch** + Optuna | User chose over the Keras option |
| 14 | Fusion | Labelled tiers: Known attack → Unknown anomaly → Performance degradation → Normal | |
| 15 | Cloud | Azure (Blob + VM) | Azure for Students eligibility confirmed by the user |
| 16 | Inference | FastAPI on Azure VM runs models + agent | |
| 17 | Agent evaluation | ~50 self-written references; BERTScore agent vs template explainer; 1–5 human rating | BERTScore confirmed by the user |
| 18 | Live demo | Two local VMs on host-only network (nmap, hping3, `tc netem`) + pcap replay backup | Azure prohibits DoS testing against its resources |
| 19 | Timeline | User declined to give dates ("irrelevant") | Roadmap has no dates |
| 20 | DENN | Dropped, meaning not pursued | |
| 21 | Work split | Ashish builds everything alone | Roadmap's team-ownership step removed |
| 22 | Scope changes vs Review 1 | User explains them to the guide in person | No deck rewrite or justification slides required |

Defaults set by Claude without a question (open to change): `log1p` targets with metrics in original
units; TCP rows with `tcprtt > 0` and `synack > 0` only; one-hot `service`/`state`, `proto` top-10 +
other; StandardScaler on train only; 15% stratified validation; seed 42; RF 10-class with
`class_weight="balanced"`; DNN start 128→64→32, dropout 0.2, Adam, MSE, early stopping;
explanations for alerts only, cached.

## 6. Files created this session

| File | Contents |
|---|---|
| `IMPLEMENTATION_ROADMAP.md` | Locked decisions, repo layout, Phases 0–14 with "Done when" checks, risk table |
| `SESSION_HANDOVER.md` | This file |

## 7. Open items — all resolved (2026-10-11 follow-up)

| Item | Resolution |
|---|---|
| DENN meaning | Dropped; not pursued |
| BERTScore for explanations | Confirmed — use BERTScore |
| Image #1 (initial requirements) | Dropped; ask the user only if it becomes needed |
| DBSCAN drop vs supervisor's note | Dropped; no justification slide |
| Azure for Students eligibility | Confirmed |
| Team split | Ashish does all the work alone |
| UNSW-NB15 per-class counts | Dataset confirmed; counts still checked as part of Phase 1 EDA (already a roadmap step) |
| Review 1 deck still says CICIDS2017 | User will explain the changes to the guide in person |

No open questions remain.

---

# Session 2 — Phase 0: project setup (2026-10-11)

## 8. What was done

**Phase 0 "Done when" check passed:** `pip install -e ".[dev]"` works, `import cnad` runs,
`pytest` → 2 passed, `ruff check .` → clean.

### Environment decisions (asked and answered this session)

| Topic | Decision | Why |
|---|---|---|
| Python | **3.11.9**, installed per-user with `winget install Python.Python.3.11` | No Python on the machine (only the Microsoft Store stub). Path: `%LOCALAPPDATA%\Programs\Python\Python311\` |
| Virtual environment | **`C:\Users\Ashis\.venvs\cnad`** — outside the project folder | Project is inside OneDrive; a ~2 GB venv (PyTorch) would sync |
| Git | **Separate repo** inside `capstone_project_2023003296`, branch `main` | The whole Desktop is already one git repo; the project gets its own history. The Desktop repo sees the project folder as untracked — that is expected |
| Dependency file | `pyproject.toml` only (no requirements.txt); dev tools in the `[dev]` extra | |
| PyTorch | CPU build (`2.14.1+cpu`) | Laptop has Intel Iris Xe only — no CUDA GPU. DNN training will run on CPU |

Activate in a new terminal: `& $HOME\.venvs\cnad\Scripts\Activate.ps1`

### Pinned versions (in `pyproject.toml`)

pandas 3.0.6 · numpy 2.4.6 · pyarrow 25.0.1 · scikit-learn 1.9.1 · torch 2.14.1 · optuna 5.0.0 ·
joblib 1.6.0 · pyyaml 6.0.3 · matplotlib 3.11.2 · seaborn 0.13.2 · fastapi 0.143.0 · uvicorn 0.54.0 ·
pydantic 2.14.0 · azure-storage-blob 12.31.0 · adlfs 2026.8.0 · streamlit 1.65.0 · plotly 7.1.0 ·
langchain 1.4.4 · langgraph 1.2.14 · langchain-google-genai 4.4.1 · langsmith 0.14.7 ·
bert-score 0.3.13 · python-dotenv 1.2.4 · dev: pytest 9.1.1 · ruff 0.17.0 · jupyter 1.1.1

Only direct dependencies are pinned; transitive ones are not locked.

### Files created

| File | Contents |
|---|---|
| `pyproject.toml` | Package `cnad` (src layout), pinned deps, `[dev]` extra, pytest + ruff config (line length 100, py311) |
| `configs/config.yaml` | seed 42; paths (raw, processed, pcaps, models, figures, tables); CSV names; validation fraction 0.15; held-out classes DoS/Reconnaissance/Backdoor; threshold percentile 95 |
| `src/cnad/config.py` | `load_config(path=None)` (env var `CNAD_CONFIG` overrides) resolves `paths` to absolute paths under `PROJECT_ROOT`; `get_config()` is the cached default |
| `src/cnad/__init__.py` + 9 empty subpackages | `data, detection, regression, fusion, cloud, api, agent, live, dashboard` |
| `tests/test_config.py` | Checks locked config values and that paths resolve under the project root |
| `.gitignore` | `data/`, `models/`, `.env`, Python/tool caches, venvs |
| `.env.example` | Azure storage (account name/key/connection string/container), `CNAD_API_URL`, `GOOGLE_API_KEY`, LangSmith (tracing/key/project) — no values |
| `README.md` | One paragraph + Windows setup commands |
| `.gitkeep` files | `notebooks/`, `scripts/`, `reports/figures/`, `reports/tables/` |
| `data/raw`, `data/processed`, `data/pcaps`, `models/` | Created locally, git-ignored |

Git: first commit `85c9131` on `main` ("Phase 0: project scaffold, config and pinned dependencies").
The existing `.agents/` and `.claude/` grill-me skill files and `skills-lock.json` were committed too.

### GitHub

- Remote `origin` = **https://github.com/ashishhh1533510/Capstone_project** (created empty by the user).
- `main` pushed and tracking `origin/main`. Workflow: keep pushing progress to GitHub; one branch per phase.
- Auth goes through Git Credential Manager. The first push failed from Claude's non-interactive shell
  ("Password authentication is not supported"), so the user ran `git push -u origin main` once
  to sign in; the saved login lets later pushes run without the user.

### Problems hit (useful if setting up again)

- `winget` Python install sat for 10+ minutes before finishing — likely waiting on a hidden dialog.
- The first `pip install` looked dead (its output was buffered) but was still running; a second
  install started in parallel and failed with `WinError 32` (file locked). Fix: kill the stale pip
  processes, run one install. Lesson: log pip to a file and check for running `python.exe` before retrying.

### Not done in Phase 0 (by design)

- Column lists (`categorical`, `numeric`, `regression_targets`, `regression_drop`) and the
  live-subset feature list are **not** in `config.yaml` yet — they belong to Phase 2.

## 9. Next step (superseded — see section 11)

Phase 1 was started and finished in Session 3.

---

# Session 3 — Phase 1: EDA (2026-10-11)

## 10. What was done

**Phase 1 "Done when" check passed:** every dataset number is saved in `reports/tables/eda_*.csv`
or `reports/figures/eda_*.png`, and summarised in `reports/data_facts.md`. `pytest` → 8 passed,
`ruff check .` → clean.

### Data download
- Official UNSW download is a SharePoint folder (not scriptable). Used the Hugging Face mirror
  **`Mireu-Lab/UNSW-NB15`**, file `Archives/UNSW-NB15.zip` (its loose `train.csv`/`test.csv` are
  byte-identical). Original file names kept in `data/raw/`; SHA-256 of both recorded in config
  and checked by a test.
- **The official file names are swapped:** `UNSW_NB15_testing-set.csv` has 175,341 rows,
  `UNSW_NB15_training-set.csv` has 82,332. `config.yaml` sets `train_csv` to the testing-set file
  so train = 175,341 (as in the UNSW paper and our roadmap). Per-class counts confirmed.
- CSVs start with a UTF-8 BOM → read with `encoding="utf-8-sig"`.

### Files created / changed
| File | Contents |
|---|---|
| `configs/config.yaml` | Swapped CSV mapping (with comment), SHA-256s, `expected_rows` |
| `src/cnad/data/load.py` | `raw_path`, `clean` (drop `id`, strip text, `Backdoors`→`Backdoor`, reject unknown classes), `load_split`, `load_both`; `CLASSES` list |
| `tests/test_load.py` | Synthetic `clean` tests + data tests (hash, row counts, classes, Normal ⇔ label 0) that skip if data is absent |
| `notebooks/01_eda.ipynb` | 9 sections, executed with outputs saved. Built from a py-percent script via `nbformat`, run with `jupyter nbconvert --execute --inplace` |
| `reports/tables/eda_*.csv` (14), `reports/figures/eda_*.png` (4) | All EDA outputs; `eda_key_numbers.csv` is the one-table summary |
| `reports/data_facts.md` | Half-page note for Review 2 |
| `.gitignore` | **Bug fix:** `data/` also ignored `src/cnad/data/`, so Phase 0 never committed its `__init__.py`. Now `/data/` and `/models/` (root only) |

### Git
- All Phase 1 work is in commit **`6dc21e4`** on branch **`phase-1`**, pushed to `origin/phase-1`
  (the push worked from Claude's shell with the saved login). `phase-1` is **not merged** into `main` yet.
- `notebooks/01_eda.ipynb` is the source of truth for the EDA. The py-percent script it was built
  from was temporary and is not in the repo; edit the notebook directly from now on.

### Guide meeting
- The user is explaining Phases 0 and 1 to the guide in person on 2026-10-12, using a plain-words
  summary prepared in this session. The guide's reaction may change the packet-loss decision below.

### Findings that affect later phases (details in `reports/data_facts.md`)
1. **Loss is not mostly zero** (only 30% of normal rows have zero loss), so the roadmap's reason for
   not predicting loss does not hold. `sloss`/`dloss` track bytes (r = 0.996). **Open: user to decide**
   whether to keep "show, don't predict" with a different reason, or change it.
2. **Two latency regimes set by TTL** in normal traffic: `31/29` ≈ 0.7 ms, `254/252` and `62/252` ≈ 150–177 ms.
   Train normal is 74% fast, test normal 46% fast → keep `sttl`/`dttl` as DNN inputs; check
   latency-gap false alarms per regime in Phase 6.
3. **Lab TTLs (64/128) never occur in UNSW-NB15** → risk for live-subset models (Phases 7/12).
4. `state` values `CLO`, `ACC` appear only in test → one-hot with `handle_unknown="ignore"`.
5. Leakage confirmed exactly: `tcprtt = synack + ackdat` on 100% of rows.
6. Regression split C size before validation: 38,244 train / 26,082 test.

## 11. Next step

1. Ask the user about the guide meeting and about finding 1 (packet loss). Claude's suggestion:
   keep "show, don't predict", now justified by loss tracking bytes (r = 0.996).
2. Merge `phase-1` into `main` and push, then start **Phase 2 (preprocessing and splits)** on
   branch `phase-2`.
