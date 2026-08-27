# BOQ Capacity Estimator (Python / Streamlit)

Same tool as the HTML version, rebuilt in Python: enter camera counts per
analytics event, tune per-model resource assumptions if needed, and get a
GPU / vCPU / RAM / storage / bandwidth spec to quote a client — with a
one-click Excel BOQ export.

## Project structure

```
boq-calculator-py/
├── app.py                     # Streamlit UI
├── boq_calculator/
│   ├── __init__.py            # public API
│   ├── models.py              # Stage, OnlineEvent, OfflineEvent, FrameProcessor, StreamingSetup
│   ├── catalog.py              # default event/model catalog (from the original workbook)
│   ├── calculations.py         # rollup math -> Totals, client spec text
│   └── export.py               # Excel BOQ export (openpyxl)
├── test_calculations.py       # sanity checks for the calc core, no Streamlit needed
├── requirements.txt
└── README.md
```

## Setup (VS Code)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Any input change recalculates instantly.

## Run the calculation tests (no Streamlit needed)

```bash
python test_calculations.py
```

Useful for editing `boq_calculator/` (the pure-Python core) without
launching the UI.

## How the sizing math works

Every analytics "event" (e.g. Smoke Detection) is a camera count plus one or
more inference **stages** (models). For each stage:

```
load       = cameras * mult          # mult = required FPS * filter fraction
instances  = ceil(load / cap)        # cap = FPS one instance sustains in prod
GPU (MB)   = instances * gpu_per_instance
RAM (MB)   = instances * ram_per_instance
vCPU       = instances * vcpu_per_instance
```

Totals across all enabled online events, offline/batch jobs, and the frame
processor are summed in `calculations.compute_totals()`, then:

```
GPU (GB)       = ceil(total_GPU_MB / 1024)
GPU cards      = ceil(GPU_GB / 16)        # 16GB card assumption
RAM (GB)       = ceil(total_RAM_MB / 1024)
Physical cores = ceil(total_vCPU / 2)
Servers        = ceil(cores / 128)        # 128 cores/server assumption
```

Storage and bandwidth come from total cameras x Mbps/camera:

```
DVR  (TB)  = ceil(bw_per_cam * cameras * 86400 * dvr_days   / (8 * 1024^2))
NDVR (TB)  = ceil(bw_per_cam * cameras * ndvr_hours * 3600 / (8 * 1024^2))
Bandwidth  = bw_per_cam * cameras   (Mbps)
```

All default per-model numbers (FPS capacity, GPU/RAM/vCPU per instance) came
from the original `BOQ_Estimater_sheet.xlsx` workbook. Three models
(Multiclass Detection, Apron Detection, Hand Gloves Detection) had a
required FPS of `0` in that workbook — placeholders, never tuned — so they
default to zero load here too. Edit their `mult` under "Edit model params"
once a client specifies a real required-FPS target.

## Editing the model catalog

Open `boq_calculator/catalog.py`. Each online event is:

```python
OnlineEvent(
    id="my_event",
    name="My Event",
    cameras=50,
    stages=[
        Stage("Model Name", mult=0.5, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
        # more stages for chained/branching pipelines
    ],
)
```

Add a new preset by appending to `default_online_events()` /
`default_offline_events()` — it appears in the UI automatically. Users can
also add one-off custom events from the running app without touching code.

## Notes / assumptions baked in

- 2 vCPU = 1 physical core, 128 cores = 1 server — edit `VCPU_PER_CORE` /
  `CORES_PER_SERVER` in `boq_calculator/calculations.py` if your hardware
  differs.
- `GPU_CARD_GB = 16` assumes a T4-class card; change it for A10/A100/etc.
- Storage assumes constant-bitrate streaming at the configured Mbps/camera.
- LLM/VLM chat services are assumed to be hosted via API, not sized as local
  GPU/CPU load — add a custom event manually if you need to self-host one.
