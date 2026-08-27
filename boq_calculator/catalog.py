"""Default event/model catalog, values sourced from the original
BOQ_Estimater_sheet.xlsx workbook.

Multiclass Detection, Apron Detection, and Hand Gloves Detection had a
required FPS of 0 in that workbook (i.e. never tuned) — they're kept at 0
load here by default. Edit `mult` on those stages once the client specifies
a real required FPS.
"""

from .models import OnlineEvent, OfflineEvent, Stage


def default_online_events():
    return [
        OnlineEvent(
            id="smoke",
            name="Smoke Detection",
            cameras=50,
            stages=[
                Stage("YOLO Smoke Detection", mult=0.5, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
                Stage("SAM 3 Detection (refine)", mult=0.05, cap=5, gpu_mb=6000, ram_mb=12000, vcpu=0),
            ],
        ),
        OnlineEvent(
            id="fire",
            name="Fire Detection",
            cameras=40,
            stages=[
                Stage("YOLO Fire Detection", mult=0.5, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
                Stage("SAM 3 Detection (refine)", mult=0.005, cap=5, gpu_mb=6000, ram_mb=12000, vcpu=0),
            ],
        ),
        OnlineEvent(
            id="combined",
            name="Combined Fire & Smoke Detection",
            cameras=50,
            stages=[
                Stage("YOLO Smoke Detection", mult=0.5, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
                Stage("YOLO Fire Detection", mult=0.5, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
                Stage("SAM 3 Detection (refine)", mult=0.05, cap=5, gpu_mb=6000, ram_mb=12000, vcpu=0),
            ],
        ),
        OnlineEvent(
            id="anpr",
            name="ANPR Detection",
            cameras=50,
            stages=[
                Stage("YOLO License Plate Detection", mult=0.75, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
                Stage("OCR ANPR Recognition", mult=0.5, cap=30, gpu_mb=1500, ram_mb=3000, vcpu=2),
            ],
        ),
        OnlineEvent(
            id="intrusion",
            name="Intrusion Detection",
            cameras=50,
            stages=[
                Stage("YOLO Person Detection", mult=0.5, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
            ],
        ),
        OnlineEvent(
            id="face",
            name="Face Recognition",
            cameras=30,
            stages=[
                Stage("YOLO Face Detection", mult=3, cap=60, gpu_mb=1200, ram_mb=2400, vcpu=2),
                Stage("YOLO Face/No-Face Filter", mult=0.6, cap=300, gpu_mb=1500, ram_mb=3000, vcpu=2),
                Stage("IRnet Face Recognition", mult=3, cap=30, gpu_mb=2533, ram_mb=5066, vcpu=2),
            ],
        ),
        OnlineEvent(
            id="multiclass",
            name="Multiclass Object Detection",
            cameras=50,
            stages=[
                Stage("YOLO Multiclass Detection", mult=0, cap=100, gpu_mb=1200, ram_mb=2400, vcpu=2),
            ],
        ),
        OnlineEvent(
            id="apron",
            name="Apron Detection",
            cameras=50,
            stages=[
                Stage("DeIT Apron Classification", mult=0, cap=300, gpu_mb=750, ram_mb=1500, vcpu=2),
            ],
        ),
        OnlineEvent(
            id="gloves",
            name="Hand Gloves Detection",
            cameras=50,
            stages=[
                Stage("DeIT Hand Glove Classification", mult=0, cap=300, gpu_mb=750, ram_mb=1500, vcpu=2),
            ],
        ),
    ]


def default_offline_events():
    return [
        OfflineEvent("store_oc", "Offline Store Open/Close", minutes_per_recording=3, recordings_per_day=0, gpu_mb=1200, ram_mb=5000, vcpu=2),
        OfflineEvent("forensic", "Offline Forensic Pipeline", minutes_per_recording=30, recordings_per_day=0, gpu_mb=6000, ram_mb=10000, vcpu=5),
        OfflineEvent("cash_oc", "Offline Cash Drawer Open/Close", minutes_per_recording=3, recordings_per_day=0, gpu_mb=1200, ram_mb=5000, vcpu=2),
        OfflineEvent("video_analytics", "Offline Video Analytics Pipeline", minutes_per_recording=10, recordings_per_day=0, gpu_mb=1200, ram_mb=5000, vcpu=2),
    ]
