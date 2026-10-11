# Session Handover — Post-Review-1 Scoping (grill-me session)

**Date:** 2026-10-11
**Project:** PROJ2999 Capstone — Cloud-Based Network Traffic Analysis and Anomaly Detection Using ML
**Team:** Ashish Kumar (2023003296, lead), N. Tarun, P. Ganesh, K. Sathwik — Ashish does all build work alone · **Guide:** Dr P. Sowjanya
**Companion file:** `IMPLEMENTATION_ROADMAP.md` (the phase-by-phase build plan — read it next)

---

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

## 8. Next step

Start **Phase 0** of `IMPLEMENTATION_ROADMAP.md`: project boilerplate (folders, virtual environment,
pinned requirements, `.gitignore`, `.env.example`, `configs/config.yaml`, `src/cnad` package).
