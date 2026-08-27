"""Aggregate rollup calculations: totals across all events -> final spec."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

from .models import OnlineEvent, OfflineEvent, FrameProcessor, StreamingSetup

VCPU_PER_CORE = 2          # physical-core assumption
CORES_PER_SERVER = 128     # dual 64-core server assumption
GPU_CARD_GB = 16           # T4-equivalent card size


@dataclass
class Totals:
    gpu_mb: float
    gpu_gb: int
    gpu_cards: int
    ram_mb: float
    ram_gb: int
    vcpu: int
    physical_cores: int
    servers: int
    bandwidth_mbps: float
    dvr_tb: int
    ndvr_tb: int


def compute_totals(
    setup: StreamingSetup,
    online_events: List[OnlineEvent],
    offline_events: List[OfflineEvent],
    frame_processor: FrameProcessor,
) -> Totals:
    gpu_mb = ram_mb = vcpu = 0.0

    for ev in online_events:
        r = ev.resource_usage()
        gpu_mb += r["gpu_mb"]
        ram_mb += r["ram_mb"]
        vcpu += r["vcpu"]

    for ev in offline_events:
        r = ev.resource_usage()
        gpu_mb += r["gpu_mb"]
        ram_mb += r["ram_mb"]
        vcpu += r["vcpu"]

    fp = frame_processor.resource_usage(setup.total_cameras)
    ram_mb += fp["ram_mb"]
    vcpu += fp["vcpu"]

    gpu_gb = math.ceil(gpu_mb / 1024) if gpu_mb > 0 else 0
    gpu_cards = math.ceil(gpu_gb / GPU_CARD_GB) if gpu_gb > 0 else 0
    ram_gb = math.ceil(ram_mb / 1024) if ram_mb > 0 else 0
    vcpu_rounded = math.ceil(vcpu) if vcpu > 0 else 0
    physical_cores = math.ceil(vcpu_rounded / VCPU_PER_CORE) if vcpu_rounded > 0 else 0
    servers = math.ceil(physical_cores / CORES_PER_SERVER) if physical_cores > 0 else 0

    bandwidth_mbps = setup.total_cameras * setup.bandwidth_mbps_per_camera

    dvr_tb = _storage_tb(
        setup.bandwidth_mbps_per_camera,
        setup.total_cameras,
        setup.dvr_days * 24 * 60 * 60,
    )
    ndvr_tb = _storage_tb(
        setup.bandwidth_mbps_per_camera,
        setup.total_cameras,
        setup.ndvr_hours * 60 * 60,
    )

    return Totals(
        gpu_mb=gpu_mb,
        gpu_gb=gpu_gb,
        gpu_cards=gpu_cards,
        ram_mb=ram_mb,
        ram_gb=ram_gb,
        vcpu=vcpu_rounded,
        physical_cores=physical_cores,
        servers=servers,
        bandwidth_mbps=bandwidth_mbps,
        dvr_tb=dvr_tb,
        ndvr_tb=ndvr_tb,
    )


def _storage_tb(mbps_per_camera: float, cameras: int, seconds: float) -> int:
    """Megabits over `seconds` -> TB. Divide by 8 (bits->bytes) then by
    1024^2 (MB->GB->TB)."""
    megabits_total = mbps_per_camera * cameras * seconds
    tb = megabits_total / (8 * 1024 * 1024)
    return math.ceil(tb) if tb > 0 else 0


def client_spec_text(
    setup: StreamingSetup,
    online_events: List[OnlineEvent],
    offline_events: List[OfflineEvent],
    totals: Totals,
) -> str:
    active_online = "\n".join(
        f"  - {ev.name}: {ev.cameras} cameras" for ev in online_events if ev.enabled
    ) or "  (none)"
    active_offline = "\n".join(
        f"  - {ev.name}: {ev.recordings_per_day} recordings/day"
        for ev in offline_events
        if ev.enabled and ev.recordings_per_day > 0
    )
    offline_block = f"\nBatch Jobs:\n{active_offline}" if active_offline else ""

    return f"""SERVER SPECIFICATION ESTIMATE
------------------------------
Total Cameras: {setup.total_cameras}
Camera Operational Hours: {setup.operational_hours} hrs/day

Analytics Enabled:
{active_online}{offline_block}

RECOMMENDED SPECIFICATION
GPU:      {totals.gpu_gb} GB VRAM  (~{totals.gpu_cards} x 16GB GPU or equivalent)
vCPU:     {totals.vcpu} vCPU  ({totals.physical_cores} physical cores)
RAM:      {totals.ram_gb} GB
Servers:  {totals.servers}
DVR Storage:  {totals.dvr_tb} TB ({setup.dvr_days} days retention)
NDVR Storage: {totals.ndvr_tb} TB ({setup.ndvr_hours} hr buffer)
Incoming Bandwidth: {totals.bandwidth_mbps:,.0f} Mbps

Note: figures are engineering estimates based on stated assumptions;
validate with a load test before final procurement.
"""
