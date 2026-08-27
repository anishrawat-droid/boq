"""Data model for the BOQ capacity estimator.

An "online" (real-time) analytics event is a camera count plus one or more
inference Stages (models) that run against that camera feed. An "offline"
event is a batch/forensic job driven by recordings-per-day rather than FPS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import math


@dataclass
class Stage:
    """A single inference model/stage within an online analytics event.

    mult: effective FPS load generated per camera for this stage
          (required_fps x filter_fraction, pre-multiplied — see README).
    cap:  FPS a single instance can sustain in production.
    gpu_mb / ram_mb / vcpu: resource footprint of ONE instance of this model.
    """

    name: str
    mult: float
    cap: float
    gpu_mb: float
    ram_mb: float
    vcpu: float

    def instances(self, cameras: int) -> int:
        if self.cap <= 0:
            return 0
        load = cameras * self.mult
        return math.ceil(load / self.cap) if load > 0 else 0

    def resource_usage(self, cameras: int) -> dict:
        inst = self.instances(cameras)
        return {
            "instances": inst,
            "gpu_mb": inst * self.gpu_mb,
            "ram_mb": inst * self.ram_mb,
            "vcpu": inst * self.vcpu,
        }


@dataclass
class OnlineEvent:
    """A real-time analytics event, e.g. 'Face Recognition'."""

    id: str
    name: str
    cameras: int
    stages: List[Stage] = field(default_factory=list)
    enabled: bool = True
    custom: bool = False

    def resource_usage(self) -> dict:
        if not self.enabled:
            return {"gpu_mb": 0, "ram_mb": 0, "vcpu": 0, "stages": []}
        total_gpu = total_ram = total_vcpu = 0.0
        stage_rows = []
        for s in self.stages:
            r = s.resource_usage(self.cameras)
            total_gpu += r["gpu_mb"]
            total_ram += r["ram_mb"]
            total_vcpu += r["vcpu"]
            stage_rows.append({"name": s.name, **r})
        return {
            "gpu_mb": total_gpu,
            "ram_mb": total_ram,
            "vcpu": total_vcpu,
            "stages": stage_rows,
        }


@dataclass
class OfflineEvent:
    """A batch/forensic job, e.g. 'Offline Forensic Pipeline'."""

    id: str
    name: str
    minutes_per_recording: float
    recordings_per_day: float
    gpu_mb: float
    ram_mb: float
    vcpu: float
    enabled: bool = True
    custom: bool = False

    def capacity_per_day(self) -> float:
        if self.minutes_per_recording <= 0:
            return 0.0
        return (60 * 24) / self.minutes_per_recording

    def instances(self) -> int:
        if not self.enabled:
            return 0
        cap = self.capacity_per_day()
        if cap <= 0 or self.recordings_per_day <= 0:
            return 0
        return math.ceil(self.recordings_per_day / cap)

    def resource_usage(self) -> dict:
        inst = self.instances()
        return {
            "instances": inst,
            "gpu_mb": inst * self.gpu_mb,
            "ram_mb": inst * self.ram_mb,
            "vcpu": inst * self.vcpu,
        }


@dataclass
class FrameProcessor:
    """Ingestion service load — scales linearly with total camera count
    (no instance rounding, matches the original workbook's formula)."""

    ram_per_feed_mb: float = 200.0
    vcpu_per_feed: float = 0.05
    enabled: bool = True

    def resource_usage(self, total_cameras: int) -> dict:
        if not self.enabled:
            return {"ram_mb": 0.0, "vcpu": 0.0}
        return {
            "ram_mb": total_cameras * self.ram_per_feed_mb,
            "vcpu": total_cameras * self.vcpu_per_feed,
        }


@dataclass
class StreamingSetup:
    total_cameras: int = 40
    operational_hours: float = 24.0
    dvr_days: float = 180.0
    ndvr_hours: float = 6.0
    bandwidth_mbps_per_camera: float = 1.0
    ram_gb: float = 64.0
    vcpu: float = 16.0
    include_models: bool = True
