# Cloud-Based Network Traffic Analysis, Anomaly Detection and Latency Prediction

PROJ2999 Capstone, GITAM Hyderabad (guide: Dr P. Sowjanya). Using the UNSW-NB15 dataset, the system
flags each network connection as a known attack (Random Forest), an unknown anomaly (Isolation
Forest) or a performance degradation (a PyTorch DNN that predicts healthy latency and response
time). Results are stored in Azure Blob Storage, served by a FastAPI app, explained by a Gemini
agent and shown on a Streamlit dashboard. See `IMPLEMENTATION_ROADMAP.md` for the build plan.

## Setup (Windows, Python 3.11)

```powershell
# The venv lives outside OneDrive so large packages are not synced
python -m venv $HOME\.venvs\cnad
& $HOME\.venvs\cnad\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env   # then fill in the secrets
pytest
```

Put `UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv` in `data/raw/`.
